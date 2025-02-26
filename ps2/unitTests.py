import unittest
import grpc
import message_server_pb2
import message_server_pb2_grpc
from concurrent import futures
import server

class TestMessageServer(unittest.TestCase):
    def tearDown(self):
        # Stop server
        self.server.stop(None)
        self.channel.close()

    def setUp(self):
        # Start fresh server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        message_server_pb2_grpc.add_MessageServerServicer_to_server(
            server.MessageServer(), self.server
        )
        self.port = self.server.add_insecure_port("[::]:50051")
        self.server.start()
        self.channel = grpc.insecure_channel(f'localhost:{self.port}')
        self.stub = message_server_pb2_grpc.MessageServerStub(self.channel)

    def test_create_account(self):
        # Test creating an account normally
        request = message_server_pb2.CreateRequest(username="user1", password="password1")
        response = self.stub.CreateAccount(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test creating an account that already exists
        response = self.stub.CreateAccount(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER1: account is already in database")

    def test_login_account(self):
        # Test creating an account and login normally
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        request = message_server_pb2.LoginRequest(username="user1", password="password1")
        response = self.stub.LoginAccount(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test login with incorrect password
        request = message_server_pb2.LoginRequest(username="user1", password="wrongpassword")
        response = self.stub.LoginAccount(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER2: incorrect password")

        # Test login with a non-existent account
        request = message_server_pb2.LoginRequest(username="user2", password="password1")
        response = self.stub.LoginAccount(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER1: account with that username does not exist")

    def test_logout_account(self):
        # Create Account and test normal logout
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user1", password="password1"))
        request = message_server_pb2.LogoutRequest(username="user1")
        response = self.stub.LogoutAccount(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test logout with a non existent account
        request = message_server_pb2.LogoutRequest(username="user2")
        response = self.stub.LogoutAccount(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER1: account with that username does not exist")

    def test_list_accounts(self):
        # Create two accounts and test listing them
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user2", password="password2"))
        request = message_server_pb2.ListAccountsRequest()
        response = self.stub.ListAccounts(request)
        self.assertTrue(response.success)
        self.assertIn("user1", response.accounts)
        self.assertIn("user2", response.accounts)

    def test_send_message(self):
        # Test sending a message between two accounts that exist
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user2", password="password2"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user1", password="password1"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user2", password="password2"))
        request = message_server_pb2.SendMessageRequest(fromUser="user1", toUser="user2", time="2023-10-10 10:00:00", message="Hello")
        response = self.stub.SendMessage(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test sending a message to a non-existent account
        request = message_server_pb2.SendMessageRequest(fromUser="user1", toUser="user3", time="2023-10-10 10:00:00", message="Hello")
        response = self.stub.SendMessage(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER1: account with that username does not exist")

    def test_read_messages(self):
        # Test reading messages for some user that exists
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user2", password="password2"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user1", password="password1"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user2", password="password2"))
        self.stub.LogoutAccount(message_server_pb2.LogoutRequest(username="user2"))
        self.stub.SendMessage(message_server_pb2.SendMessageRequest(fromUser="user1", toUser="user2", time="2023-10-10 10:00:00", message="Hello"))
        request = message_server_pb2.ReadMessagesRequest(username="user2", numMessages=1)
        response = self.stub.ReadMessages(request)
        self.assertTrue(response.success)
        self.assertEqual(response.numRead, 1)
        self.assertEqual(response.messages[0].message, "Hello")

        # Test reading messages for a non-existent account
        request = message_server_pb2.ReadMessagesRequest(username="user3", numMessages=1)
        response = self.stub.ReadMessages(request)
        self.assertFalse(response.success)
        self.assertEqual(response.numRead, 0)
    
    
    def test_read_instant_messages(self):
        # Test reading an instantaneous message for some user that has instantaneous messages
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user2", password="password2"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user1", password="password1"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user2", password="password2"))
        self.stub.SendMessage(message_server_pb2.SendMessageRequest(fromUser="user1", toUser="user2", time="2023-10-10 10:00:00", message="Hello"))
        request = message_server_pb2.InstantaneousMessagesRequest(username="user2")
        response = self.stub.GetInstantaneousMessages(request)
        self.assertTrue(response.success)
        self.assertEqual(response.numRead, 1)
        self.assertEqual(response.messages[0].message, "Hello")

        # Test that instantaneous messages get removed from the queue
        # Also test reading instantaneous messages for a user without instantaneous messages
        request = message_server_pb2.InstantaneousMessagesRequest(username="user2")
        response = self.stub.GetInstantaneousMessages(request)
        self.assertFalse(response.success)

    def test_delete_message(self):
        # Test normal deletion of a message
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user2", password="password2"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user1", password="password1"))
        self.stub.LoginAccount(message_server_pb2.LoginRequest(username="user2", password="password2"))
        self.stub.SendMessage(message_server_pb2.SendMessageRequest(fromUser="user1", toUser="user2", time="2023-10-10 10:00:00", message="Hello"))
        request = message_server_pb2.DeleteMessagesRequest(username="user2", messageId=0)
        response = self.stub.DeleteMessages(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test deletion of a message from an account that doesn't exist
        request = message_server_pb2.DeleteMessagesRequest(username="user3", messageId=0)
        response = self.stub.DeleteMessages(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER3: attempting to delete a message from an account that does not exist")

        # Test deletion of a message that doesn't exist
        request = message_server_pb2.DeleteMessagesRequest(username="user2", messageId=1)
        response = self.stub.DeleteMessages(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER4: account did not receive message with that id")


    def test_delete_account(self):
        # Test deletion of a normal account
        self.stub.CreateAccount(message_server_pb2.CreateRequest(username="user1", password="password1"))
        request = message_server_pb2.DeleteAccountRequest(username="user1")
        response = self.stub.DeleteAccount(request)
        self.assertTrue(response.success)
        self.assertEqual(response.errorMessage, "")

        # Test deletion of an account that doesn't exist
        request = message_server_pb2.DeleteAccountRequest(username="user2")
        response = self.stub.DeleteAccount(request)
        self.assertFalse(response.success)
        self.assertEqual(response.errorMessage, "ER1: attempting to delete an account that does not exist")

if __name__ == "__main__":
    unittest.main()