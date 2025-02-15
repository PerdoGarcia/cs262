import unittest
import socket
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
        return response.decode("utf-8")

    def send_request(self, request):
        request = str(len(request)) + request
        self.sock.sendall(request.encode('utf-8'))
        response = self.read_message()

        # Ignore SEL messages when using this because they are intended as a notification for the 
        # other client, not as a response
        if (response[0:3] == "SEL"):
            response = self.read_message()
        return response
    
    def send_request_se(self, request):
        request = str(len(request)) + request
        self.sock.sendall(request.encode('utf-8'))

        # Return SEL message as first parameter and then the SET response as second parameter
        responses = []
        # Read SEL message (returned here because both clients are using the same socket)
        resp = self.read_message()
        responses.append(resp)
        # Read SET message (returned here because both clients are using the same socket)
        resp = self.read_message()
        responses.append(resp)
        return responses

    def test_create_account(self):
        # Create account
        request = "CRuser1 password1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "CRT")

        # Test creating an account that already exists
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER1")
        
        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_login(self):
        # Create account
        request = "CRuser1 password1"
        self.send_request(request)

        # Test login with correct user and password
        request = "LIuser1 password1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "LIT")

        # Test login with incorrect password
        request = "LIuser1 wrongpassword"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER2")

        # Test login with non-existent account
        request = "LIuser2 password2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER1")
        
        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_logout(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)

        # Login with correct information and then logout correctly
        request = "LIuser1 password1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "LIT")
        
        request = "LOuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "LOT")

        # Test logout with non-existent account
        request = "LOuser2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER1")

        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_list_accounts(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)

        # Create another account
        request = "CRuser2 password2"
        self.send_request(request)

        # Send list accounts request and check it has correct content
        request = "LA"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "LAT")
        self.assertIn("user1", response)
        self.assertIn("user2", response)

        # Delete accounts to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

        request = "DAuser2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_send_message_logged_in(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)

        # Create another account
        request = "CRuser2 password2"
        self.send_request(request)

        # Login both users
        request = "LIuser1 password1"
        response = self.send_request(request)
        request = "LIuser2 password2"
        response = self.send_request(request)

        # Send a message from one to the other while logged in
        request = "SEuser1 user2 2023-10-10-10:00:00 Hello World"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "SET")

        # Test sending message to non-existent account
        request = "SEuser1 user3 2023-10-10-10:00:00 Hello World"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER1")

        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

        request = "DAuser2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_read_message_loggedout(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)
        # Create another account
        request = "CRuser2 password2"
        self.send_request(request)
        
        # Login only sending user
        request = "LIuser1 password1"
        response = self.send_request(request)

        # Send a message from one to the other while the receipient is logged out
        request = "SEuser1 user2 2023-10-10-10:00:00 Hello World"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "SET")

        # Check that read messages gets the undelivered message
        request = "REuser2 1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "RET")
        self.assertEqual(response[3], "1")
        body = response[5:]
        body_parts = body.split(" ")
        message = " ".join(body_parts[3:])
        self.assertEqual("11Hello World", message)

        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

        request = "DAuser2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_delete_message(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)
        # Create another account
        request = "CRuser2 password2"
        self.send_request(request)
        
        # Login both users
        request = "LIuser1 password1"
        response = self.send_request(request)
        request = "LIuser2 password2"
        response = self.send_request(request)

        # Send a message and extract the message id, then delete that message
        request = "SEuser1 user2 2023-10-10-10:00:00 Hello World"
        response_sel, response_set = self.send_request_se(request)
        message_id = ""
        i = 3
        while response_sel[i].isnumeric():
            message_id += response_sel[i]
            i += 1
        request = "DMuser2 " + message_id
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DMT")

        # Test deleting non-existent message
        request = "DMuser2 " + str(int(message_id) + 1)
        response = self.send_request(request)
        self.assertEqual(response[0:3], "ER4")

        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

        request = "DAuser2"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

    def test_delete_account(self):
        # Create one account
        request = "CRuser1 password1"
        self.send_request(request)
        # Delete account to clean up
        request = "DAuser1"
        response = self.send_request(request)
        self.assertEqual(response[0:3], "DAT")

if __name__ == '__main__':
    unittest.main()