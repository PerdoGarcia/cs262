# baby shark doo doo doo doo doo doo
import unittest
import socket

# TODO CHANGE THIS DO NOT HARD CODE
HOST = "127.0.0.1"
PORT = 54400

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))

    def tearDown(self):
        self.s.close()

    def test_createAccountAndLogin(self):
        pass
        # Code

    def test_sendMessage(self):
        pass
    # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')

    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())

    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)

if __name__ == '__main__':
    unittest.main()