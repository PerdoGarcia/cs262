import unittest
from unittest.mock import patch, MagicMock, call
import sqlite3
import os
import server1 as server1
import message_server_pb2
import grpc

class TestReplicationFunctions(unittest.TestCase):
    def setUp(self):
        # Create a test database file
        self.test_db = 'test_server.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        # Create a MessageServer instance with connect_on_init=False to prevent actual connections
        self.server = server1.MessageServer(port=5001, connect_on_init=False)
        self.server.db_filename = self.test_db

        # Replace the actual SQLite connection with our test db
        self.server.connection = sqlite3.connect(self.test_db)
        self.server.cursor = self.server.connection.cursor()

        # Initialize test tables
        self.server.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        logged_in INTEGER NOT NULL);""")

        self.server.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY,
        sender_username TEXT,
        recipient_username TEXT,
        message TEXT,
        timestamp TEXT,
        instant INTEGER,
        delivered INTEGER);""")
        self.server.connection.commit()

        # Mock the connections and channels dictionaries
        self.server.connections = {}
        self.server.channels = {}

        # Set up test ports
        self.server.ports = [5001, 5002, 5003]

    def tearDown(self):
        # Close connection and remove test database
        self.server.connection.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_find_master_when_lowest_port(self):
        """Test that find_master elects the server with the lowest port as master"""
        # Setup connections dict with mock ports
        self.server.connections = {5002: MagicMock(), 5003: MagicMock()}

        # Call find_master
        self.server.find_master()

        # Check if this server is elected as master (since it has port 5001)
        self.assertTrue(self.server.is_master)
        self.assertEqual(self.server.current_master, 5001)

    def test_find_master_when_not_lowest_port(self):
        """Test that find_master correctly identifies another server as master"""
        # Set current port to 5002
        self.server.port = 5002

        # Setup connections with port 5001 which should be master
        self.server.connections = {5001: MagicMock(), 5003: MagicMock()}

        # Call find_master
        self.server.find_master()

        # This server should not be master
        self.assertFalse(self.server.is_master)
        self.assertEqual(self.server.current_master, 5001)

    @patch('server1.MessageServer.commit')
    def test_commit_all(self, mock_commit):
        """Test commit_all sends updates to all connected servers"""
        # Setup connections with two other ports
        self.server.port = 5001
        self.server.connections = {5001: MagicMock(), 5002: MagicMock(), 5003: MagicMock()}

        # Test data
        query = "INSERT INTO users VALUES (?, ?, ?)"
        params = ["testuser", "testpassword", 0]

        # Call commit_all
        self.server.commit_all(query, params)

        # Verify commit was called for ports 5002 and 5003 but not for 5001 (self)
        expected_calls = [
            call(5002, query, params),
            call(5003, query, params),
        ]
        mock_commit.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_commit.call_count, 2)

    def test_commit(self):
        """Test the commit function correctly calls the Commit RPC on a connected server"""
        # Create a mock connection
        mock_connection = MagicMock()
        mock_reply = MagicMock()
        mock_reply.success = True
        mock_connection.Commit.return_value = mock_reply

        # Add mock connection to server
        self.server.connections = {5002: mock_connection}
        self.server.channels = {5002: MagicMock()}

        # Test data
        query = "INSERT INTO users VALUES ('testuser', 'testpassword', 0)"
        params = []  # Use empty params for now since we're mocking the call

        # Mock the CommitRequest creation
        with patch('message_server_pb2.CommitRequest') as mock_request:
            # Setup the mock request object
            mock_request_obj = MagicMock()
            mock_request.return_value = mock_request_obj

            # Call commit
            result = self.server.commit(5002, query, params)

            # Verify CommitRequest was created with correct args
            mock_request.assert_called_once_with(port=5002, query=query, params=params)

            # Verify the Commit RPC was called with our mock request
            mock_connection.Commit.assert_called_once_with(mock_request_obj)

            # Verify result is True (success)
            self.assertTrue(result)

    def test_commit_failure(self):
        """Test commit handles failure correctly"""
        # Create a mock connection that fails
        mock_connection = MagicMock()
        mock_reply = MagicMock()
        mock_reply.success = False
        mock_connection.Commit.return_value = mock_reply

        # Add mock connection to server
        self.server.connections = {5002: mock_connection}
        self.server.channels = {5002: MagicMock()}

        # Test data
        query = "INSERT INTO users VALUES ('testuser', 'testpassword', 0)"
        params = []

        # Mock the CommitRequest creation
        with patch('message_server_pb2.CommitRequest') as mock_request:
            # Setup the mock request object
            mock_request_obj = MagicMock()
            mock_request.return_value = mock_request_obj

            # Call commit
            result = self.server.commit(5002, query, params)

            # Verify the connection was removed on failure
            self.assertNotIn(5002, self.server.connections)
            self.assertNotIn(5002, self.server.channels)

            # Verify result is False (failure)
            self.assertFalse(result)

    def test_Commit_success(self):
        """Test the Commit RPC handler successfully executes queries"""
        # Create a mock request with the properties we need
        request = MagicMock()
        request.port = 5001
        request.query = "INSERT INTO users (username, password, logged_in) VALUES ('testuser', 'testpassword', 0)"
        request.params = []

        # Mock context
        context = MagicMock()

        # Call Commit
        reply = self.server.Commit(request, context)

        # Verify the query was executed
        self.server.cursor.execute("SELECT * FROM users WHERE username = 'testuser'")
        result = self.server.cursor.fetchone()
        self.assertIsNotNone(result)

        # Verify the reply indicates success
        self.assertTrue(reply.success)

    def test_Commit_failure(self):
        """Test the Commit RPC handler handles query errors"""
        # Create a mock request with an invalid query
        request = MagicMock()
        request.port = 5001
        request.query = "INVALID SQL QUERY"
        request.params = []

        # Mock context
        context = MagicMock()

        # Call Commit
        reply = self.server.Commit(request, context)

        # Verify the reply indicates failure
        self.assertFalse(reply.success)
        self.assertIn("Could not commit", reply.errorMessage)

    @patch('server1.MessageServer.find_master')
    def test_disconnect(self, mock_find_master):
        """Test disconnect removes connections and calls find_master"""
        # Create a mock connection
        mock_connection = MagicMock()
        mock_reply = MagicMock()
        mock_reply.success = True
        mock_connection.Disconnect.return_value = mock_reply

        # Setup connections
        self.server.connections = {5002: mock_connection}
        self.server.channels = {5002: MagicMock()}

        # Call disconnect
        self.server.disconnect(5002)

        # Verify Disconnect was called
        mock_connection.Disconnect.assert_called_once()

        # Verify connections were removed
        self.assertNotIn(5002, self.server.connections)
        self.assertNotIn(5002, self.server.channels)

        # Verify find_master was called
        mock_find_master.assert_called_once()

    @patch('server1.MessageServer.find_master')
    def test_Disconnect(self, mock_find_master):
        """Test the Disconnect RPC handler removes connections"""
        # Setup connections
        mock_channel = MagicMock()
        self.server.connections = {5002: MagicMock()}
        self.server.channels = {5002: mock_channel}

        # Create a request
        request = message_server_pb2.DisconnectRequest(
            requesterPort=5002,
            replierPort=5001,
            isMaster=True
        )

        # Mock context
        context = MagicMock()

        # Call Disconnect
        reply = self.server.Disconnect(request, context)

        # Verify connections were removed
        self.assertNotIn(5002, self.server.connections)
        self.assertNotIn(5002, self.server.channels)

        # Verify find_master was called (since isMaster=True)
        mock_find_master.assert_called_once()

        # Verify the reply indicates success
        self.assertTrue(reply.success)

    @patch('grpc.insecure_channel')
    @patch('server1.MessageServer.health_check')
    @patch('server1.MessageServer.add_connect')
    @patch('server1.MessageServer.find_master')
    def test_connect_all(self, mock_find_master, mock_add_connect, mock_health_check, mock_insecure_channel):
        """Test connect_all attempts to connect to all configured ports"""
        # Setup mocks
        mock_channel = MagicMock()
        mock_insecure_channel.return_value = mock_channel
        mock_health_check.return_value = True  # All connections are healthy
        mock_add_connect.return_value = True  # All connections succeed

        # Call connect_all
        self.server.connect_all()

        # Verify insecure_channel was called for each port except self
        expected_calls = [
            call('localhost:5002'),
            call('localhost:5003')
        ]
        mock_insecure_channel.assert_has_calls(expected_calls, any_order=True)

        # Verify health_check was called for each channel
        mock_health_check.assert_called_with(mock_channel)

        # Verify add_connect was called for each port
        expected_calls = [
            call(5002),
            call(5003)
        ]
        mock_add_connect.assert_has_calls(expected_calls, any_order=True)

        # Verify find_master was called
        mock_find_master.assert_called_once()

    def test_health_check_success(self):
        """Test health_check with a successful connection"""
        # Create a mock channel where future.result() succeeds
        mock_channel = MagicMock()
        mock_future = MagicMock()
        mock_future.result.return_value = None  # No exception

        with patch('grpc.channel_ready_future', return_value=mock_future):
            result = self.server.health_check(mock_channel)

            # Verify channel_ready_future was called
            self.assertTrue(result)

    def test_health_check_failure(self):
        """Test health_check with a failing connection"""
        # Create a mock channel where future.result() raises an exception
        mock_channel = MagicMock()
        mock_future = MagicMock()
        mock_future.result.side_effect = grpc.FutureTimeoutError()

        with patch('grpc.channel_ready_future', return_value=mock_future):
            result = self.server.health_check(mock_channel)

            # Verify health_check returned False
            self.assertFalse(result)

    def test_IsMaster(self):
        """Test the IsMaster RPC handler returns the correct master status"""
        # Set server as master
        self.server.is_master = True

        # Create a request
        request = message_server_pb2.IsMasterRequest()

        # Mock context
        context = MagicMock()

        # Call IsMaster
        reply = self.server.IsMaster(request, context)

        # Verify the reply indicates this server is master
        self.assertTrue(reply.isMaster)

        # Change master status and test again
        self.server.is_master = False
        reply = self.server.IsMaster(request, context)
        self.assertFalse(reply.isMaster)

    @patch('threading.Thread')
    def test_heart_beat_thread_started(self, mock_thread):
        """Test that the heart_beat thread is started during connect_all"""
        # Setup
        self.server.port = 5001

        # Mock methods that are called in connect_all
        with patch('server1.MessageServer.health_check', return_value=False), \
             patch('server1.MessageServer.find_master') as mock_find_master:

            # Call connect_all
            self.server.connect_all()

            # Verify thread was started with heart_beat target
            mock_thread.assert_called_once()
            args, kwargs = mock_thread.call_args
            self.assertEqual(kwargs['target'], self.server.heart_beat)
            self.assertTrue(kwargs['daemon'])
            mock_thread.return_value.start.assert_called_once()

if __name__ == '__main__':
    unittest.main()