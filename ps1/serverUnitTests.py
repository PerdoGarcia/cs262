import unittest
from server import create_account, login, logout, list_accounts, send_message, read_message, delete_message, delete_account, clear_accounts_structure, get_accounts_structure, reset_messageId

class TestServerMethods(unittest.TestCase):

    def setUp(self):
        # Reset the accounts and messageId before each test
        clear_accounts_structure()
        reset_messageId()
        

    def test_create_account(self):
        # Test valid account creation
        result = create_account("user1", "password1")
        self.assertTrue(result[0])
        accounts = get_accounts_structure()
        self.assertIn("user1", accounts)

        # Test creating an account that already exists
        result = create_account("user1", "password1")
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER1: account is already in database")

    def test_login(self):
        # Test login with existent account and correct password
        create_account("user1", "password1")
        result = login("user1", "password1", None, None)
        self.assertTrue(result[0])

        # Test login with incorrect password
        result = login("user1", "wrongpassword", None, None)
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER2: incorrect password")

        # Test login with non-existent account
        result = login("user2", "password2", None, None)
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER1: account with that username does not exist")

    def test_logout(self):
        # Test logout with an existent account
        create_account("user1", "password1")
        login("user1", "password1", None, None)
        result = logout("user1")
        self.assertTrue(result[0])

        # Test logout with non-existent account
        result = logout("user2")
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER1: account with that username does not exist")

    def test_list_accounts(self):
        # Test if we return list of all current accounts
        create_account("user1", "password1")
        create_account("user2", "password2")
        result = list_accounts()
        self.assertTrue(result[0])
        self.assertIn("user1", result[1])
        self.assertIn("user2", result[1])

    def test_send_message(self):
        # Test sending a message to an existing account
        create_account("user1", "password1")
        create_account("user2", "password2")
        login("user1", "password1", None, None)
        login("user2", "password2", None, None)
        result = send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
        self.assertTrue(result[0])
        self.assertEqual(result[1]["message"], "Hello")

        # Test sending message to non-existent account
        result = send_message("user1", "user3", "Hello", "2023-10-10 10:00:00")
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER1: account with that username does not exist")

    def test_read_message_loggedOut(self):
        # Test sending a message to a logged out user, should be marked as "undelivered" and fetchable via read message
        create_account("user1", "password1")
        create_account("user2", "password2")
        login("user1", "password1", None, None)
        login("user2", "password2", None, None)
        logout("user2")
        send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
        result = read_message("user2", 1)
        self.assertTrue(result[0])
        self.assertEqual(result[1]["num_read"], 1)
        self.assertEqual(result[1]["messages"][0]["message"], "Hello")
    
    def test_read_message_loggedIn(self):
        # Test sending a message to a logged in user, should be marked as "delivered"
        create_account("user1", "password1")
        create_account("user2", "password2")
        login("user1", "password1", None, None)
        login("user2", "password2", None, None)
        send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
        result = read_message("user2", 1)
        self.assertTrue(result[0])
        self.assertEqual(result[1]["num_read"], 0)
        accounts = get_accounts_structure()
        self.assertEqual(len(accounts["user2"]["messageHistory"]), 1)
        self.assertTrue(accounts["user2"]["messageHistory"][0]["delivered"])

    def test_delete_message(self):
        # Test deleting an existent message
        create_account("user1", "password1")
        create_account("user2", "password2")
        login("user1", "password1", None, None)
        login("user2", "password2", None, None)
        send_message("user1", "user2", "Hello", "2023-10-10 10:00:00")
        result = delete_message("user2", 0)
        self.assertTrue(result[0])

        # Test deleting non-existent message
        result = delete_message("user2", 1)
        self.assertFalse(result[0])
        self.assertEqual(result[1], "ER2: account did not receive message with that id")

    def test_delete_account(self):
        # Test deleting your own account
        create_account("user1", "password1")
        result = delete_account("user1")
        self.assertTrue(result[0])
        accounts = get_accounts_structure()
        self.assertNotIn("user1", accounts)

if __name__ == '__main__':
    unittest.main()