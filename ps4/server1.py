# Adapted from lecture code

from dotenv import load_dotenv
import os

# gRPC imports
import grpc
import message_server_pb2
import message_server_pb2_grpc
import threading

from concurrent import futures
import sqlite3

load_dotenv()

# GRPC code
class MessageServer(message_server_pb2_grpc.MessageServerServicer):
    """Provides methods that implement functionality of the message server."""

    def __init__(self):
        # self.accounts = {}
        # self.logged_in_users = {}
        # self.instantMessages = {}
        # self.messageId = 0

        # SQLite3 connection setup
        self.connection = sqlite3.connect('server.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        print("Connected to the database")

        # Creates table for users if it doesn't exist
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        logged_in INTEGER NOT NULL);""")
        self.connection.commit()

        # Creates table for messages if it doesn't exist
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY,
        sender_username TEXT,
        recipient_username TEXT,
        message TEXT,
        timestamp TEXT,
        instant INTEGER,
        delivered INTEGER,
        FOREIGN KEY (recipient_username)
            REFERENCES users (username),
        FOREIGN KEY (sender_username)
            REFERENCES users (username) 
        );""")
        self.connection.commit()
        print("Database set up completed")

        # Lock for preventing race conditions
        self.lock = threading.Lock()

    def CreateAccount(self, request, context):
        """
        Attempts to create an account with the given username and password

        Parameters
        ----------
        request : message_server_pb2.CreateRequest
            request.username : str
                The desired username of the account
            request.password : str
                The desired password of the account

        Returns
        -------
        reply: message_server_pb2.CreateReply
            reply.success is True or False, and indicates if the account was created successfully
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Trying to create account for ", request.username)
        with self.lock:
            # Check if the username already exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # error: account is already in the database
                return message_server_pb2.CreateReply(success=False, errorMessage="ER1: account is already in database")
            else:
                self.cursor.execute(f'INSERT INTO users (username, password, logged_in) VALUES ("{request.username}", "{request.password}", 1)')
                # self.accounts[request.username] = {
                #     "accountInfo": {"username": request.username, "password": request.password},
                #     "loggedIn": True,
                #     "messageHistory": []
                # }
                self.connection.commit()
                return message_server_pb2.CreateReply(success=True, errorMessage="")

    def LoginAccount(self, request, context):
        """
        Attempts to log a user in with the given username and password

        Parameters
        ----------
        request : message_server_pb2.LoginRequest
            request.username : str
                The username of the account being logged into
            request.password : str
                The inputted (hashed) password of the account being logged into

        Returns
        -------
        reply: message_server_pb2.LoginReply
            reply.success is True or False, and indicates if the account was created successfully
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Trying to login ", request.username)
        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # Check if the password is correct
                if (response[0][1] == request.password):
                    # If you try to login twice for some reason nothing happens
                    self.cursor.execute(f'UPDATE users SET logged_in = 1 WHERE username = "{request.username}"')
                    self.connection.commit()
                    return message_server_pb2.LoginReply(success=True, errorMessage="")
                else:
                    # error: incorrect password
                    return message_server_pb2.LoginReply(success=False, errorMessage="ER2: incorrect password")
            else:
                # error: account with that username does not exist
                return message_server_pb2.LoginReply(success=False, errorMessage="ER1: account with that username does not exist")
            
            # if request.username not in self.accounts:
            #     # error: account with that username does not exist
            #     return message_server_pb2.LoginReply(success=False, errorMessage="ER1: account with that username does not exist")
            # else:
                # if self.accounts[request.username]["accountInfo"]["username"] == request.username and self.accounts[request.username]["accountInfo"]["password"] == request.password:
                #     # If you try to login twice for some reason nothing happens
                #     self.accounts[request.username]["loggedIn"] = True
                #     self.logged_in_users[request.username] = True
                #     return message_server_pb2.LoginReply(success=True, errorMessage="")
                # else:
                #     # error: incorrect password
                #     return message_server_pb2.LoginReply(success=False, errorMessage="ER2: incorrect password")

    def LogoutAccount(self, request, context):
        """
        Attempts to logout a user in with the given username and password

        Parameters
        ----------
        request : message_server_pb2.LogoutRequest
            request.username : str
                The username of the account being logged out of

        Returns
        -------
        reply: message_server_pb2.LogoutReply
            reply.success is True or False, and indicates if the account was created successfully
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Trying to logout ", request.username)
        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # If you try to logout twice for some reason nothing happens
                self.cursor.execute(f'UPDATE users SET logged_in = 0 WHERE username = "{request.username}"')
                self.connection.commit()
                return message_server_pb2.LogoutReply(success=True, errorMessage="")
            else:
                # error: account with that username does not exist
                return message_server_pb2.LogoutReply(success=False, errorMessage="ER1: account with that username does not exist")
            # if request.username not in self.accounts:
            #     # error: account with that username does not exist
            #     return message_server_pb2.LogoutReply(success=False, errorMessage="ER1: account with that username does not exist")
            # else:
            #     # If you try to logout twice for some reason nothing happens
            #     self.accounts[request.username]["loggedIn"] = False
            #     del self.logged_in_users[request.username]
            #     return message_server_pb2.LogoutReply(success=True, errorMessage="")

    def ListAccounts(self, request, context):
        """
        Lists all accounts currently on the server.

        Parameters
        ----------
        None.

        Returns
        -------
        reply: message_server_pb2.ListAccountsReply
            reply.success is always True. This function cannot fail.
            reply.accounts is a list of all account names stored by the server.
        """
        with self.lock:
            self.cursor.execute(f'SELECT username FROM users')
            response = self.cursor.fetchall()
            accountNames = [x[0] for x in response]

            # accountNames = list(self.accounts.keys())
            accountReply = message_server_pb2.ListAccountsReply()
            accountReply.success = True
            accountReply.accounts.extend(accountNames)
            return accountReply

    def SendMessage(self, request, context):
        """
        Attempts to send a message from one user to another. If the receiving user is logged in, the message
        is marked as delivered instantly. Otherwise, it is marked as undelivered.

        Parameters
        ----------
        request : message_server_pb2.SendMessageRequest
            request.fromUser : str
                The username of the account sending the message
            request.toUser: str
                The username of the account receiving the message
            user.time:
                A string representing the string to be sent
            user.message: str
                The message text

        Returns
        -------
        reply: message_server_pg2.SendMessageReplyToSender
            reply.success is True or False, and indicates if the message was sent successfully to the other user
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Sending message from ", request.fromUser, " to ", request.toUser)
        with self.lock:
            # Check if the sending username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.fromUser}"')
            response = self.cursor.fetchall()
            if len(response) == 0:
                return message_server_pb2.SendMessageReplyToSender(success=False, errorMessage="ER1: sending account with that username does not exist")
            
            # Check if the receiving username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.toUser}"')
            response = self.cursor.fetchall()
            if len(response) == 0:
                return message_server_pb2.SendMessageReplyToSender(success=False, errorMessage="ER2: receiving account with that username does not exist")

            # If the recieving user is logged in, the message should be marked as for instant delivery
            instant = 0
            if response[0][2] == 1:
                print("instant message")
                instant = 1
            self.cursor.execute(f'INSERT INTO messages (sender_username, recipient_username, message, timestamp, instant, delivered) VALUES ("{request.fromUser}", "{request.toUser}", "{request.message}", "{request.time}", {instant}, 0)')
            self.connection.commit()
            return message_server_pb2.SendMessageReplyToSender(success=True, errorMessage="")

            # if request.toUser not in self.accounts:
            #     return message_server_pb2.SendMessageReplyToSender(success=False, errorMessage="ER1: account with that username does not exist")

            # if self.accounts[request.toUser]["loggedIn"] == True:
            #     # If user is logged in, the message is marked as delivered instantly, and message is added to list of "instant messages" for that user
            #     message_dict = {"sender": request.fromUser, "timestamp": request.time, "message": request.message, "messageId": self.messageId, "delivered": True}
            #     if request.toUser not in self.instantMessages:
            #         self.instantMessages[request.toUser] = []
            #     self.instantMessages[request.toUser].append(message_dict)
            #     self.accounts[request.toUser]["messageHistory"].append(message_dict)
            # else:
            #     # If the receiving user is logged out, add the message to their list of messages
            #     message_dict = {"sender": request.fromUser, "timestamp": request.time, "message": request.message, "messageId": self.messageId, "delivered": False}
            #     self.accounts[request.toUser]["messageHistory"].append(message_dict)
            # # Each time a message is sent the messageId counter goes up
            # self.messageId += 1

            # return message_server_pb2.SendMessageReplyToSender(success=True, errorMessage="")

    def ReadMessages(self, request, context):
        """
        Attempts to get undelivered messages for a user.

        Parameters
        ----------
        request: message_server_pb2.ReadMessagesRequest
            request.username: str
                The username of the account requesting to read messages
            request.numMessages: int
                The number of messages requested

        Returns
        -------
        reply: message_server_pb2.ReadMessagesReply
            reply.success is always True if the user exists and False if the user does not exist.
            reply.numRead is the number of messages read, which may be less than num if the user
            had less than num undelivered messages.
            reply.messages is a list of messages objects
                Each message has the following keys: messageId, fromUser, time, message.
        """
        print("Reading ", request.numMessages, " messages for ", request.username)
        with self.lock:
            # Check if username is in the database, if not there are no messages to read
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) == 0:
                return message_server_pb2.ReadMessagesReply(success=False, numRead=0, messages=[])
            # SELECT * FROM messages WHERE recipient_username = "duck" AND instant = 0 AND delivered = 0 LIMIT 3;
            self.cursor.execute(f'SELECT message_id, sender_username, timestamp, message FROM messages WHERE recipient_username = "{request.username}" AND instant = 0 AND delivered = 0 LIMIT {request.numMessages}')
            response = self.cursor.fetchall()

            # Update all of the selected messages to mark them as delivered
            message_ids = [x[0] for x in response]
            self.cursor.execute(f'UPDATE messages SET delivered = 1 WHERE message_id IN ({",".join([str(x) for x in message_ids])})')
            self.connection.commit()

            readReply = message_server_pb2.ReadMessagesReply(
                success=True,
                numRead=len(response),
                messages=[
                    {
                        "messageId": message[0],
                        "fromUser": message[1],
                        "time": message[2],
                        "message": message[3]
                    }
                    for message in response]
            )
            return readReply

            
            # if request.username not in self.accounts:
            #     return message_server_pb2.ReadMessagesReply(success=False, numRead=0, messages=[])

            # # Go through message array for a user and append undelivered messages
            # num_read = 0
            # returned_messages = []
            # for message in self.accounts[request.username]["messageHistory"]:
            #     if message["delivered"] == False:
            #         message["delivered"] = True
            #         returned_messages.append(message)
            #         num_read += 1
            #         if num_read == request.numMessages:
            #             break


            # readReply = message_server_pb2.ReadMessagesReply(
            #     success=True,
            #     numRead=num_read,
            #     messages=[
            #         {
            #             "fromUser": message["sender"],
            #             "time": message["timestamp"],
            #             "message": message["message"],
            #             "messageId": message["messageId"]
            #         }
            #         for message in returned_messages]
            # )
            # return readReply

    def GetInstantaneousMessages(self, request, context):
        """
        Attempts to read instantaneous messages for a user.

        Parameters
        ----------
        request: message_server_pb2.InstantaneousMessagesRequest
            request.username: str
                The username of the account requesting to read instantaneous messages

        Returns
        -------
        reply: message_server_pb2.InstantaneousMessagesReply
            reply.success is True if there is at least one message waiting to be instantly read, otherwise False.
            reply.numRead is the number of messages read. This function always reads all instantenous messages waiting for a user.
            reply.messages is a list of messages objects
                Each message has the following keys: messageId, fromUser, time, message.
        """
        print("Getting instantaneous messages for ", request.username)
        with self.lock:
            # Check if username is in the database, if not there are no messages to read
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) == 0:
                return message_server_pb2.InstantaneousMessagesReply(success=False, numRead=0, messages=[])
            # SELECT * FROM messages WHERE recipient_username = "duck" AND instant = 0 AND delivered = 0 LIMIT 3;
            self.cursor.execute(f'SELECT message_id, sender_username, timestamp, message FROM messages WHERE recipient_username = "{request.username}" AND instant = 1 AND delivered = 0')
            response = self.cursor.fetchall()

            # Update all of the selected messages to mark them as delivered
            message_ids = [x[0] for x in response]
            self.cursor.execute(f'UPDATE messages SET delivered = 1 WHERE message_id IN ({",".join([str(x) for x in message_ids])})')
            self.connection.commit()

            readReply = message_server_pb2.InstantaneousMessagesReply(
                success=True,
                numRead=len(response),
                messages=[
                    {
                        "messageId": message[0],
                        "fromUser": message[1],
                        "time": message[2],
                        "message": message[3]
                    }
                    for message in response]
            )
            return readReply
        
            # if request.username not in self.instantMessages:
            #     return message_server_pb2.InstantaneousMessagesReply(success=False)
            # else:
            #     if len(self.instantMessages[request.username]) == 0:
            #         return message_server_pb2.InstantaneousMessagesReply(success=True, numRead=0)

            #     readReply = message_server_pb2.InstantaneousMessagesReply(
            #         success=True,
            #         numRead=len(self.instantMessages[request.username]),
            #         messages=[
            #             {
            #                 "fromUser": message["sender"],
            #                 "time": message["timestamp"],
            #                 "message": message["message"],
            #                 "messageId": message["messageId"]
            #             }
            #             for message in self.instantMessages[request.username]]
            #     )
            #     del self.instantMessages[request.username]
            #     return readReply


    def DeleteMessages(self, request, context):
        """
        Attempts to delete a message with a specific ID from a user's list of messages.

        Parameters
        ----------
        request: message_server_pb2.DeleteMessagesRequest
            request.username: str
                The username of the account requesting to delete a message
            request.messageId: int
                The ID of the message to delete

        Returns
        -------
        reply: message_server_pb2.DeleteMessagesReply
            reply.success is True or False, and indicates if the user deleted the requested message successfully
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Deleting message", request.messageId, "from", request.username)
        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # Check if the message exists in the database
                self.cursor.execute(f'SELECT * FROM messages WHERE message_id = "{request.messageId}"')
                response = self.cursor.fetchall()
                if len(response) > 0:
                    # Delete the message in the messages table
                    self.cursor.execute(f'DELETE FROM messages WHERE message_id = "{request.messageId}"')
                    self.connection.commit()
                    return message_server_pb2.DeleteMessagesReply(success=True, errorMessage="")
                else:
                    # Error: attempting to delete a message that does not exist
                    return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER4: account did not receive message with that id")
            else:
                return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER3: attempting to delete a message from an account that does not exist")
            # if request.username not in self.accounts:
            #     return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER3: attempting to delete a message from an account that does not exist")

            # for i in range(len(self.accounts[request.username]["messageHistory"])):
            #     if self.accounts[request.username]["messageHistory"][i]["messageId"] == request.messageId:
            #         del self.accounts[request.username]["messageHistory"][i]
            #         return message_server_pb2.DeleteMessagesReply(success=True, errorMessage="")
            # return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER4: account did not receive message with that id")

    def DeleteAccount(self, request, context):
        """
        Deletes a account with the given username.

        Parameters
        ----------
        request: message_server_pb2.DeleteAccountRequest
            request.username: str
                The username of the account to delete

        Returns
        -------
        reply: message_server_pb2.DeleteAccountReply
            reply.success is True or False, and indicates if the user deleted the requested message successfully
            reply.errorMessage is an empty string on success and an error message on failure
        """
        print("Deleting account ", request.username)
        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # Delete any messages sent to that user first from messages table
                self.cursor.execute(f'DELETE FROM messages WHERE recipient_username = "{request.username}"')
                self.connection.commit()
                # Delete the user in the users table
                self.cursor.execute(f'DELETE FROM users WHERE username = "{request.username}"')
                self.connection.commit()
                message_server_pb2.DeleteAccountReply(success=True, errorMessage="")
            else:
                # Error: attempting to delete an account that does not exist
                return message_server_pb2.DeleteAccountReply(success=False, errorMessage="ER1: attempting to delete an account that does not exist")
            # if request.username not in self.accounts:
            #     return message_server_pb2.DeleteAccountReply(success=False, errorMessage="ER1: attempting to delete an account that does not exist")
            # else:
            #     del self.accounts[request.username]
            #     if request.username in self.logged_in_users:
            #         del self.logged_in_users[request.username]
            #     return message_server_pb2.DeleteAccountReply(success=True, errorMessage="")

# Handles new requests from clients
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_server_pb2_grpc.add_MessageServerServicer_to_server(
        MessageServer(), server
    )
    server.add_insecure_port("[::]:" + os.environ.get("GRPC_PORT"))
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    print("Starting server")
    serve()