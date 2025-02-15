import unittest
import socket
import json
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get("HOST_SERVER_TESTING")
PORT = int(os.environ.get("PORT_SERVER_TESTING"))

class TestServerMethods(unittest.TestCase):
    def setUp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

    def tearDown(self):
        self.sock.close()

    def read_message(self):
        # Reads the first number that is sent over to figure out how many total bytes are in the message
        str_bytes = ""
        recv_data = self.sock.recv(1)
        while recv_data:
            if len(recv_data.decode("utf-8")) > 0:
                if (recv_data.decode("utf-8")).isnumeric():
                    str_bytes += recv_data.decode("utf-8")
                else:
                    break
            recv_data = self.sock.recv(1)
        num_bytes = int(str_bytes)

        # Reads the next num_bytes bytes to get the full message
        response = recv_data
        cur_bytes = 1
        while(cur_bytes < num_bytes):
            recv_data = self.sock.recv(num_bytes - cur_bytes)
            if recv_data:
                response += recv_data
                cur_bytes += len(recv_data.decode("utf-8"))
        json_read = json.loads(response.decode("utf-8"))
        return json_read

    def send_request(self, request):
        request = json.dumps(request)
        request = str(len(request)) + request
        self.sock.sendall(request.encode('utf-8'))
        json_read = self.read_message()

        # Ignore SEL messages when using this because they are intended as a notification for the 
        # other client, not as a response
        if ("type" in json_read and json_read["type"] == "SEL"):
            json_read = self.read_message()
        return json_read
    
    def send_request_se(self, request):
        request = json.dumps(request)
        request = str(len(request)) + request
        self.sock.sendall(request.encode('utf-8'))

        # Return SEL message as first parameter and then the SET response as second parameter
        responses = []
        # Read SEL message (returned here because both clients are using the same socket)
        json_read = self.read_message()
        responses.append(json_read)
        # Read SET message (returned here because both clients are using the same socket)
        json_read = self.read_message()
        responses.append(json_read)
        return responses

    def test_create_account(self):
        # Create account
        request = {"type": "CR", "username": "user1", "password": "password1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test creating an account that already exists
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account is already in database")

        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_login(self):
        # Create account and log in
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        request = {"type": "LI", "username": "user1", "password": "password1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test login with incorrect password
        request = {"type": "LI", "username": "user1", "password": "wrongpassword"}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER2: incorrect password")

        # Test login with non-existent account
        request = {"type": "LI", "username": "user2", "password": "password2"}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account with that username does not exist")
        
        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_logout(self):
        # Create one account, login correctly, and logout correctly
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        request = {"type": "LO", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test logout with non-existent account
        request = {"type": "LO", "username": "user2"}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account with that username does not exist")

        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_list_accounts(self):
        # Create two accounts
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        
        # Send list accounts request and check it has correct content
        request = {"type": "LA"}
        response = self.send_request(request)
        self.assertTrue(response["success"])
        self.assertIn("user1", response["accounts"])
        self.assertIn("user2", response["accounts"])

        # Delete accounts to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_send_message_logged_in(self):
        # Create two accounts and login to both
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user2", "password": "password2"})
        
        # Send a message from one to the other while logged in
        request = {"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10-10:00:00", "message": "Hello World"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test sending message to non-existent account
        request = {"type": "SE", "from_username": "user1", "to_username": "user3", "timestamp": "2023-10-10-10:00:00", "message": "Hello World"}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account with that username does not exist")

        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_read_message_loggedout(self):
        # Create two accounts and login to just the sender account
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        
        # Send a message from one to the other while the receipient is logged out
        self.send_request({"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10-10:00:00", "message": "Hello World"})
        request = {"type": "RE", "username": "user2", "number": 1}
        response = self.send_request(request)
        self.assertEqual(response["num_read"], 1)
        self.assertEqual(response["messages"][0]["message"], "Hello World")

        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_delete_message(self):
        # Create two accounts and login to both
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user2", "password": "password2"})
        
        # Send a message and extract the message id, then delete that message
        response_sel, response_set = self.send_request_se({"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10-10:00:00", "message": "Hello World"})
        message_id = response_sel["messageId"]
        request = {"type": "DM", "username": "user2", "id": message_id}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test deleting non-existent message
        request = {"type": "DM", "username": "user2", "id": message_id+1}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER4: account did not receive message with that id")

        # Delete account to clean up
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_delete_account(self):
        # Create one account and then delete it
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

if __name__ == '__main__':
    unittest.main()