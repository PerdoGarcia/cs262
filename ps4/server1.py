# server1.py
from dotenv import load_dotenv
import os

# gRPC imports
import grpc
import message_server_pb2
import message_server_pb2_grpc
import threading
import time
from concurrent import futures
import sqlite3

load_dotenv()

# GRPC code
class MessageServer(message_server_pb2_grpc.MessageServerServicer):
    """Provides methods that implement functionality of the message server."""

    def __init__(self, port):
        # self.accounts = {}
        # self.logged_in_users = {}
        # self.instantMessages = {}
        # self.messageId = 0
        # SQLite3 connection setup
        self.port = port
        self.ports = [5001, 5002, 5003]
        self.db_filename = f'server_{port}.db'
        self.connection = sqlite3.connect(self.db_filename, check_same_thread=False)
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

        # replication
        # contains the port numbers as keys and their connections
        self.connections = {}
        # contains the stubs to the other servers
        self.channels = {}
        # if the current server is the current master
        self.is_master = False
        # who the current master is
        self.current_master = None
        # connects to all servers
        self.connect_all()
        # heartbeat signal for the master
        threading.Thread(target=self.heart_beat, daemon=True).start()


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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.CreateReply(success=False, errorMessage="ER0: connection error")

        with self.lock:
            # Check if the username already exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # error: account is already in the database
                return message_server_pb2.CreateReply(success=False, errorMessage="ER1: account is already in database")
            else:
                self.cursor.execute(f'INSERT INTO users (username, password, logged_in) VALUES ("{request.username}", "{request.password}", 1)')
                self.connection.commit()

                query = f'INSERT INTO users (username, password, logged_in) VALUES ("{request.username}", "{request.password}", 1)'
                params = []
                self.commit_all(query, params)
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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.LoginReply(success=False, errorMessage="ER0: connection error")

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
                    query = f'UPDATE users SET logged_in = 1 WHERE username = "{request.username}"'
                    params = []
                    self.commit_all(query, params)
                    return message_server_pb2.LoginReply(success=True, errorMessage="")
                else:
                    # error: incorrect password
                    return message_server_pb2.LoginReply(success=False, errorMessage="ER2: incorrect password")
            else:
                # error: account with that username does not exist
                return message_server_pb2.LoginReply(success=False, errorMessage="ER1: account with that username does not exist")

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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.LogoutReply(success=False, errorMessage="ER0: connection error")

        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # If you try to logout twice for some reason nothing happens
                self.cursor.execute(f'UPDATE users SET logged_in = 0 WHERE username = "{request.username}"')
                self.connection.commit()

                query = f'UPDATE users SET logged_in = 0 WHERE username = "{request.username}"'
                params = []
                self.commit_all(query, params)
                return message_server_pb2.LogoutReply(success=True, errorMessage="")
            else:
                # error: account with that username does not exist
                return message_server_pb2.LogoutReply(success=False, errorMessage="ER1: account with that username does not exist")


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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            accountReply = message_server_pb2.ListAccountsReply()
            accountReply.success = False
            accountReply.accounts.extend([])
            return accountReply

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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.SendMessageReplyToSender(success=False, errorMessage="ER0: connection error")

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

            query = f'INSERT INTO messages (sender_username, recipient_username, message, timestamp, instant, delivered) VALUES ("{request.fromUser}", "{request.toUser}", "{request.message}", "{request.time}", {instant}, 0)'
            params = []
            self.commit_all(query, params)
            return message_server_pb2.SendMessageReplyToSender(success=True, errorMessage="")


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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.ReadMessagesReply(success=False, numRead=0, messages=[])

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
            query = f'UPDATE messages SET delivered = 1 WHERE message_id IN ({",".join([str(x) for x in message_ids])})'
            params = []
            self.commit_all(query, params)
            return readReply


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
        print("Getting instant messages for ", request.username)
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.InstantaneousMessagesReply(success=False, numRead=0, messages=[])

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
            query = f'UPDATE messages SET delivered = 1 WHERE message_id IN ({",".join([str(x) for x in message_ids])})'
            params = []
            self.commit_all(query, params)
            return readReply


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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER0: connection error")

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

                    # write to other servers
                    query = f'DELETE FROM messages WHERE message_id = "{request.messageId}"'
                    params = []
                    self.commit_all(query, params)
                    return message_server_pb2.DeleteMessagesReply(success=True, errorMessage="")
                else:
                    # Error: attempting to delete a message that does not exist
                    return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER4: account did not receive message with that id")
            else:
                return message_server_pb2.DeleteMessagesReply(success=False, errorMessage="ER3: attempting to delete a message from an account that does not exist")


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
        # If the server is not the master, simply return an error back to the client
        if not self.is_master:
            return message_server_pb2.DeleteAccountReply(success=False, errorMessage="ER0: connection error")

        with self.lock:
            # Check if the username exists in the database
            self.cursor.execute(f'SELECT * FROM users WHERE username = "{request.username}"')
            response = self.cursor.fetchall()
            if len(response) > 0:
                # Delete any messages sent to that user first from messages table
                # first write

                self.cursor.execute(f'DELETE FROM messages WHERE recipient_username = "{request.username}"')
                self.connection.commit()
                # write to other servers
                query = f'DELETE FROM users WHERE username = "{request.username}"'
                params = []
                self.commit_all(query, params)

                # Delete the user in the users table
                # second write
                self.cursor.execute(f'DELETE FROM users WHERE username = "{request.username}"')
                self.connection.commit()
                # write to other servers
                query = f'DELETE FROM users WHERE username = "{request.username}"'
                params = []
                self.commit_all(query, params)
                return message_server_pb2.DeleteAccountReply(success=True, errorMessage="")
            else:
                # Error: attempting to delete an account that does not exist
                return message_server_pb2.DeleteAccountReply(success=False, errorMessage="ER1: attempting to delete an account that does not exist")


    # replication functions
    # server has to act like a client and server
    # lowercase functions are client functions
    # Uppercase functions are server functions

    def commit_all(self, query, params):
        for port in list(self.connections.keys()):
            try:
                if port != self.port:
                    self.commit(port, query, params)
                    print(f"Committed to port {port}")
            except Exception as e:
                self.disconnect(port)
                print(f"Could not commit to port {port}")


    def commit(self, port, query, params):
        request = message_server_pb2.CommitRequest(
            port=port,
            query=query,
            params=params
        )
        try:
            reply = self.connections[port].Commit(request)
            if not reply.success:
                if port in self.connections:
                    self.channels[port].close()
                    self.channels.pop(port)
                    self.connections.pop(port)
            return reply.success
        except Exception as e:
            print(f"Could not commit to port {port}")
            return False


    def Commit(self, request, context):
        query = request.query
        params = request.params
        with self.lock:
            try:
                self.cursor.execute(query, params)
                self.connection.commit()
                reply = message_server_pb2.CommitReply(success=True)
                print(f"Committed: {query} with params {params}")
                return reply
            except Exception as e:
                reply = message_server_pb2.CommitReply(success=False, errorMessage=f"Could not commit: {e}")
                return reply


    def disconnect(self, port):
        request = message_server_pb2.DisconnectRequest(
            requesterPort=self.port,
            replierPort=port,
            isMaster=self.is_master
        )

        # First perform the RPC call (without closing the channel first)
        try:
            reply = self.connections[port].Disconnect(request)
            print(f"Disconnected from port {port}")
        except Exception as e:
            print(f"Could not disconnect from port {port}: {e}")
            reply = message_server_pb2.DisconnectReply(success=False, errorMessage=f"Could not disconnect: {e}")

        if port in self.channels:
            self.channels[port].close()
            del self.channels[port]
        if port in self.connections:
            del self.connections[port]

        self.find_master()

        return reply


    def Disconnect(self, request: message_server_pb2.DisconnectRequest, context):
        port = request.requesterPort
        print(f"Received disconnect request from {port}")
        if port in self.connections:
            del self.connections[port]
        if port in self.channels:
            self.channels[port].close()
            del self.channels[port]
        print("Disconnect successful")
        reply = message_server_pb2.DisconnectReply(success=True, errorMessage="")
        if request.isMaster:
            self.find_master()
        return reply

    def disconnect_all(self):
        # disconnect from all connections
        for port in self.ports:
            if port != self.port:
                try:
                    self.disconnect(port)
                    print(f"Disconnected from port {port}")
                except Exception as e:
                    print(f"Could not disconnect from port {port}")


    def is_master_helper(self, port):
        request = message_server_pb2.IsMasterRequest()
        try:
            reply = self.connections[port].IsMaster(request)
            return reply.isMaster
        except Exception as e:
            print(f"Could not check if {port} is master")
            return False

    def IsMaster(self, request, context):
        reply = message_server_pb2.IsMasterReply(isMaster=self.is_master)
        return reply


    # lowest port connection is the master server
    def find_master(self):
        """
        Find and elect a new master server when needed.
        This method is called when:
        1. A server starts up
        2. A connection to a server fails
        3. A server detects the master is unreachable
        """
        print("Finding new master")
        # active ports
        active_ports = list(self.connections.keys()) + [self.port]
        active_ports.sort()
        print("Active ports:", active_ports)

        new_master = active_ports[0]
        self.current_master = new_master

        if new_master == self.port:
            self.is_master = True
            print("I am now the master")
        else:
            self.is_master = False
            print("Port {} is the new master".format(new_master))


    def add_connect(self, port):
        request = message_server_pb2.AddConnectRequest(
            requestPort=self.port,
            replyPort=port
        )
        try:
            reply = self.connections[port].AddConnect(request)
            print(f"Connected to port {port}")
            return reply.success
        except Exception as e:
            print(f"Could not connect to port {port}")
            return False


    def AddConnect(self, request, context):
        requestPort = request.requestPort
        try:
            self.channels[requestPort] = grpc.insecure_channel(f'localhost:{requestPort}')
            self.connections[requestPort] = message_server_pb2_grpc.MessageServerStub(self.channels[requestPort])
            reply = message_server_pb2.AddConnectReply(success=True)
            print(f"Connected to port {requestPort}")
            self.find_master()
            return reply
        except Exception as e:
            # Better error handling
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "No error message"
            print(f"Error in AddConnect: {error_type}, Message: {error_msg}")
            reply = message_server_pb2.AddConnectReply(success=False,
                                    errorMessage=f"Could not connect: {error_type}: {error_msg}")
            return reply


    def connect_all(self):
        for port in self.ports:
            if port != self.port:
                try:
                    channel = grpc.insecure_channel(f'localhost:{port}')
                    if self.health_check(channel):
                        self.channels[port] = channel
                        self.connections[port] = message_server_pb2_grpc.MessageServerStub(channel)
                        # signal other ports to connect to this port
                        self.add_connect(port)
                        print(f"Connected to port {port} from {self.port}")
                    else:
                        print(f"Could not connect to port {port}")
                except Exception as e:
                    print(f"Could not connect to port {port}")
        # find master in all dbs
        self.find_master()

    # https://grpc.github.io/grpc/python/_modules/grpc.html#channel_ready_future
    def health_check(self, channel):
        try:
            grpc.channel_ready_future(channel).result(timeout=2)
            return True
        except grpc.FutureTimeoutError:
            return False

    def heart_beat(self):
        while True:
            time.sleep(3)
            if not self.is_master and self.current_master is not None:
                # Perform heartbeat check
                channel = grpc.insecure_channel(f'localhost:{self.current_master}')
                try:
                    grpc.channel_ready_future(channel).result(timeout=2)
                    stub = message_server_pb2_grpc.MessageServerStub(channel)
                    request = message_server_pb2.IsMasterRequest()
                    response = stub.IsMaster(request, timeout=2)
                    if not response.isMaster:
                        # If current master does not identify itself as master, trigger election
                        print("Master reported not master anymore.")
                        self.find_master()
                except Exception as e:
                    print(f"Master heartbeat failed for port {self.current_master}: {e}")
                    # disconnect from dead master and select new master
                    self.disconnect(self.current_master)
                    self.find_master()


# Handles new requests from clients
def serve():
    port = int(input("Enter the port number: 5001, 5002, or 5003\n"))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_server = MessageServer(port)
    try:
        message_server_pb2_grpc.add_MessageServerServicer_to_server(
            message_server, server
        )
        server.add_insecure_port("[::]:" + str(port))
        server.start()
        server.wait_for_termination()
    except:
        message_server.disconnect_all()

if __name__ == "__main__":
    print("Starting server")
    serve()