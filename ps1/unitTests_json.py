import unittest
import socket
import threading
import selectors
import types
import json
# from ps1.server import create_account, login, logout, list_accounts, send_message, read_message, delete_message, delete_account, accept_wrapper, service_connection_wp, service_connection_json

HOST = '127.0.0.1'
PORT = 5001

class TestServerMethods(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     # cls.sel = selectors.DefaultSelector()
    #     cls.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     cls.lsock.bind((HOST, PORT))
    #     cls.lsock.listen()
    #     cls.lsock.setblocking(False)
    #     # cls.sel.register(cls.lsock, selectors.EVENT_READ, data=None)
    #     # cls.server_thread = threading.Thread(target=cls.run_server, daemon=True)
    #     # cls.server_thread.start()

    # @classmethod
    # def tearDownClass(cls):
    #     # cls.sel.close()
    #     cls.lsock.close()

    # @classmethod
    # def run_server(cls):
    #     while True:
    #         events = cls.sel.select(timeout=None)
    #         for key, mask in events:
    #             if key.data is None:
    #                 accept_wrapper(key.fileobj)
    #             else:
    #                 service_connection_json(key, mask)

    def setUp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

    def tearDown(self):
        self.sock.close()

    def read_message(self):
        str_bytes = ""
        recv_data = self.sock.recv(1)
        # print("recv_data", recv_data.decode("utf-8"))
        while recv_data:
            if len(recv_data.decode("utf-8")) > 0:
                if (recv_data.decode("utf-8")).isnumeric():
                    str_bytes += recv_data.decode("utf-8")
                else:
                    break
            recv_data = self.sock.recv(1)
        num_bytes = int(str_bytes)

        # TODO: read more bytes using recv until you've fit all the bytes you need in
        response = recv_data
        cur_bytes = 1
        while(cur_bytes < num_bytes):
            recv_data = self.sock.recv(num_bytes - cur_bytes)
            if recv_data:
                # print("RECEIVED RAW DATA:", recv_data)
                response += recv_data
                cur_bytes += len(recv_data.decode("utf-8"))
        # print("received: ", response.decode("utf-8"))
        json_read = json.loads(response.decode("utf-8"))
        return json_read

    def send_request(self, request):
        request = json.dumps(request)
        request = str(len(request)) + request
        self.sock.sendall(request.encode('utf-8'))
        json_read = self.read_message()
        # print(json_read)
        if ("type" in json_read and json_read["type"] == "SEL"):
            json_read = self.read_message()
        return json_read

    def test_create_account(self):
        request = {"type": "CR", "username": "user1", "password": "password1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test creating an account that already exists
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account is already in database")

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_login(self):
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
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_logout(self):
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

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_list_accounts(self):
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        request = {"type": "LA"}
        response = self.send_request(request)
        self.assertTrue(response["success"])
        self.assertIn("user1", response["accounts"])
        self.assertIn("user2", response["accounts"])

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_send_message(self):
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user2", "password": "password2"})
        request = {"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10 10:00:00", "message": "Hello"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        # Test sending message to non-existent account
        request = {"type": "SE", "from_username": "user1", "to_username": "user3", "timestamp": "2023-10-10 10:00:00", "message": "Hello"}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER1: account with that username does not exist")

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_read_message_loggedout(self):
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user2", "password": "password2"})
        self.send_request({"type": "LO", "username": "user2"})
        self.send_request({"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10 10:00:00", "message": "Hello"})
        request = {"type": "RE", "username": "user2", "number": 1}
        response = self.send_request(request)
        self.assertTrue(response["success"])
        self.assertEqual(response["num_read"], 1)
        self.assertEqual(response["messages"][0]["message"], "Hello")

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_delete_message(self):
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        self.send_request({"type": "CR", "username": "user2", "password": "password2"})
        self.send_request({"type": "LI", "username": "user1", "password": "password1"})
        self.send_request({"type": "LI", "username": "user2", "password": "password2"})
        self.send_request({"type": "SE", "from_username": "user1", "to_username": "user2", "timestamp": "2023-10-10 10:00:00", "message": "Hello"})
        request = {"type": "DM", "username": "user2", "id": 0}
        response = self.send_request(request)
        # print(response)
        self.assertTrue(response["success"])

        # Test deleting non-existent message
        request = {"type": "DM", "username": "user2", "id": 1}
        response = self.send_request(request)
        self.assertFalse(response["success"])
        self.assertEqual(response["errorMsg"], "ER4: account did not receive message with that id")

        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

        request = {"type": "DA", "username": "user2"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

    def test_delete_account(self):
        self.send_request({"type": "CR", "username": "user1", "password": "password1"})
        request = {"type": "DA", "username": "user1"}
        response = self.send_request(request)
        self.assertTrue(response["success"])

if __name__ == '__main__':
    unittest.main()

# import unittest
# from ps1.server import create_account, login, logout, list_accounts, send_message, read_message, delete_message, delete_account

# class TestServerMethods(unittest.TestCase):

#     def setUp(self):
#         # Reset the accounts and messageId before each test
#         global accounts, messageId
#         accounts = {}
#         messageId = 0

#     def test_create_account(self):
#         result = create_account("user1", "password1")
#         self.assertTrue(result[0])
#         self.assertIn("user1", accounts)

#         # Test creating an account that already exists
#         result = create_account("user1", "password1")
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER1: account is already in database")

#     def test_login(self):
#         create_account("user1", "password1")
#         result = login("user1", "password1", None, None)
#         self.assertTrue(result[0])

#         # Test login with incorrect password
#         result = login("user1", "wrongpassword", None, None)
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER2: incorrect password")

#         # Test login with non-existent account
#         result = login("user2", "password2", None, None)
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER1: account with that username does not exist")

#     def test_logout(self):
#         create_account("user1", "password1")
#         login("user1", "password1", None, None)
#         result = logout("user1")
#         self.assertTrue(result[0])

#         # Test logout with non-existent account
#         result = logout("user2")
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER1: account with that username does not exist")

#     def test_list_accounts(self):
#         create_account("user1", "password1")
#         create_account("user2", "password2")
#         result = list_accounts()
#         self.assertTrue(result[0])
#         self.assertIn("user1", result[1])
#         self.assertIn("user2", result[1])

#     def test_send_message(self):
#         create_account("user1", "password1")
#         create_account("user2", "password2")
#         login("user1", "password1", None, None)
#         login("user2", "password2", None, None)
#         result = send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
#         self.assertTrue(result[0])
#         self.assertEqual(result[1]["message"], "Hello")

#         # Test sending message to non-existent account
#         result = send_message("user1", "user3", "Hello", "2023-10-10 10:00:00")
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER1: account with that username does not exist")

#     def test_read_message(self):
#         create_account("user1", "password1")
#         create_account("user2", "password2")
#         login("user1", "password1", None, None)
#         login("user2", "password2", None, None)
#         send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
#         result = read_message("user2", 1)
#         self.assertTrue(result[0])
#         self.assertEqual(result[1]["num_read"], 1)
#         self.assertEqual(result[1]["messages"][0]["message"], "Hello")

#     def test_delete_message(self):
#         create_account("user1", "password1")
#         create_account("user2", "password2")
#         login("user1", "password1", None, None)
#         login("user2", "password2", None, None)
#         send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
#         result = delete_message("user2", 0)
#         self.assertTrue(result[0])

#         # Test deleting non-existent message
#         result = delete_message("user2", 1)
#         self.assertFalse(result[0])
#         self.assertEqual(result[1], "ER2: account did not receive message with that id")

#     def test_delete_account(self):
#         create_account("user1", "password1")
#         result = delete_account("user1")
#         self.assertTrue(result[0])
#         self.assertNotIn("user1", accounts)

# if __name__ == '__main__':
#     unittest.main()