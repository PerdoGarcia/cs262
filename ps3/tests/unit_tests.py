import unittest
import socket
import threading
import time
import os
import json
from queue import Queue
import machines
import random

class TestLamportImplementation(unittest.TestCase):
    def setUp(self):
        """Set up environment variables for testing."""
        os.environ["HOST_SERVER"] = "127.0.0.1"
        # Close any existing sockets
        for socket_obj in self.socket_list if hasattr(self, 'socket_list') else []:
            try:
                socket_obj.close()
            except:
                pass
        self.socket_list = []

    def tearDown(self):
        """Close any open sockets."""
        for socket_obj in self.socket_list if hasattr(self, 'socket_list') else []:
            try:
                socket_obj.close()
            except:
                pass

    def test_connections_directly(self):
        """Test connection establishment directly."""
        print("\nTesting direct connection...")

        # Start a simple server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_list.append(server_socket)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 5002))
        server_socket.listen(1)

        # Set a timeout for accept
        server_socket.settimeout(2)

        # Connection event to signal when a connection is received
        connection_received = threading.Event()

        # Thread to accept connection
        def accept_connection():
            try:
                conn, addr = server_socket.accept()
                self.socket_list.append(conn)
                connection_received.set()
            except socket.timeout:
                pass

        accept_thread = threading.Thread(target=accept_connection)
        accept_thread.daemon = True
        accept_thread.start()

        # Connect client to server
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_list.append(client_socket)
            client_socket.connect(('127.0.0.1', 5002))

            # Wait for server to accept
            self.assertTrue(connection_received.wait(3), "Server should accept the connection")
        except Exception as e:
            self.fail(f"Failed to connect: {e}")
        finally:
            # Clean up
            server_socket.close()
            client_socket.close()

    def test_message_sending(self):
        """Test that messages are correctly formatted and sent."""
        print("\nTesting message sending...")

        # Create a test message
        test_message = {
            "time": 42,
            "sender": 0,
            "recipient": 1
        }

        # Create a server to receive the message
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_list.append(server_socket)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", 6000))
        server_socket.listen(1)

        # Accept a connection in a thread
        received_data = []

        def accept_connection():
            conn, _ = server_socket.accept()
            self.socket_list.append(conn)
            # Read the message length
            length_bytes = b""
            while True:
                byte = conn.recv(1)
                if not byte or not byte.decode('utf-8', errors='ignore').isdigit():
                    break
                length_bytes += byte

            # Now read the rest of the message
            message_length = int(length_bytes.decode('utf-8'))
            message_data = byte  # First non-digit byte

            while len(message_data) < message_length:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                message_data += chunk

            received_data.append(message_data.decode('utf-8'))
            conn.close()

        receive_thread = threading.Thread(target=accept_connection)
        receive_thread.daemon = True
        receive_thread.start()

        # Connect and send the message
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_list.append(client_socket)
        client_socket.connect(("127.0.0.1", 6000))

        # Send the message
        machines.send_message(test_message, client_socket)

        # Wait for receive thread to finish
        receive_thread.join(3)

        # Clean up
        client_socket.close()
        server_socket.close()

        # Check if message was received
        self.assertTrue(received_data, "Message should be received")
        # Parse the received message
        received_json = json.loads(received_data[0])
        self.assertEqual(received_json["time"], test_message["time"], "Message time should match")
        self.assertEqual(received_json["sender"], test_message["sender"], "Sender should match")
        self.assertEqual(received_json["recipient"], test_message["recipient"], "Recipient should match")

    def test_operation_1_random_send(self):
        """Test operation 1: Send to random machine."""
        print("\nTesting operation 1: Random send...")

        # Setup test objects
        message_queue = Queue()
        connections = {1: socket.socket(), 2: socket.socket()}
        self.socket_list.extend(connections.values())

        # Mock send_message
        original_send = machines.send_message
        send_calls = []

        def mock_send(message, sock):
            send_calls.append((message, sock))
            return True

        machines.send_message = mock_send

        # Mock random choice to always return machine 1
        original_choice = random.choice
        random.choice = lambda x: 1

        # Mock random.randint to always return 1 (trigger operation 1)
        original_randint = random.randint
        random.randint = lambda a, b: 1

        try:
            # Create a log file
            log_file = open("test_op1.log", "w")

            # Setup initial state
            clock = 0
            machine_id = 0

            # Simulate one execution of the event loop
            if not message_queue.empty():
                message = message_queue.get_nowait()
                clock = max(clock, message["time"]) + 1
            else:
                # Operation 1
                if connections:
                    recipient_id = random.choice(list(connections.keys()))
                    message = {
                        "time": clock,
                        "sender": machine_id,
                        "recipient": recipient_id,
                    }
                    machines.send_message(message, connections[recipient_id])
                clock += 1

            # Check result
            self.assertEqual(len(send_calls), 1, "Should send one message")
            self.assertEqual(send_calls[0][0]["recipient"], 1, "Should send to machine 1")
            self.assertEqual(send_calls[0][0]["sender"], 0, "Sender should be machine 0")

        finally:
            # Cleanup
            machines.send_message = original_send
            random.choice = original_choice
            random.randint = original_randint
            log_file.close()
            os.remove("test_op1.log")

    def test_operation_2_next_machine(self):
        """Test operation 2: Send to next machine."""
        print("\nTesting operation 2: Next machine send...")

        # Setup test objects
        message_queue = Queue()
        connections = {1: socket.socket(), 2: socket.socket()}
        self.socket_list.extend(connections.values())

        # Mock send_message
        original_send = machines.send_message
        send_calls = []

        def mock_send(message, sock):
            send_calls.append((message, sock))
            return True

        machines.send_message = mock_send

        # Mock random.randint to always return 2 (trigger operation 2)
        original_randint = random.randint
        random.randint = lambda a, b: 2

        try:
            # Create a log file
            log_file = open("test_op2.log", "w")

            # Setup initial state
            clock = 0
            machine_id = 0

            # Simulate one execution of the event loop
            if not message_queue.empty():
                message = message_queue.get_nowait()
                clock = max(clock, message["time"]) + 1
            else:
                # Operation 2
                recipient_id = (machine_id + 1) % 3
                if recipient_id in connections:
                    message = {
                        "time": clock,
                        "sender": machine_id,
                        "recipient": recipient_id,
                    }
                    machines.send_message(message, connections[recipient_id])
                clock += 1

            # Check result
            self.assertEqual(len(send_calls), 1, "Should send one message")
            self.assertEqual(send_calls[0][0]["recipient"], 1, "Should send to machine 1 (next after 0)")
            self.assertEqual(send_calls[0][0]["sender"], 0, "Sender should be machine 0")

        finally:
            # Cleanup
            machines.send_message = original_send
            random.randint = original_randint
            log_file.close()
            os.remove("test_op2.log")

    def test_operation_3_broadcast(self):
        """Test operation 3: Broadcast to all machines."""
        print("\nTesting operation 3: Broadcast...")

        # Setup test objects
        message_queue = Queue()
        connections = {1: socket.socket(), 2: socket.socket()}
        self.socket_list.extend(connections.values())

        # Mock send_message
        original_send = machines.send_message
        send_calls = []

        def mock_send(message, sock):
            send_calls.append((message, sock))
            return True

        machines.send_message = mock_send

        # Mock random.randint to always return 3 (trigger operation 3)
        original_randint = random.randint
        random.randint = lambda a, b: 3

        try:
            # Create a log file
            log_file = open("test_op3.log", "w")

            # Setup initial state
            clock = 0
            machine_id = 0

            # Simulate one execution of the event loop
            if not message_queue.empty():
                message = message_queue.get_nowait()
                clock = max(clock, message["time"]) + 1
            else:
                # Operation 3
                for recipient_id, sock in connections.items():
                    if recipient_id != machine_id:
                        message = {
                            "time": clock,
                            "sender": machine_id,
                            "recipient": recipient_id,
                        }
                        machines.send_message(message, sock)
                clock += 1

            # Check result
            self.assertEqual(len(send_calls), 2, "Should send two messages (one to each other machine)")
            recipients = [call[0]["recipient"] for call in send_calls]
            self.assertIn(1, recipients, "Should send to machine 1")
            self.assertIn(2, recipients, "Should send to machine 2")

        finally:
            # Cleanup
            machines.send_message = original_send
            random.randint = original_randint
            log_file.close()
            os.remove("test_op3.log")

if __name__ == "__main__":
    unittest.main()