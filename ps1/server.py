# Adapted from lecture code

import socket
import selectors
import types
import os
from dotenv import load_dotenv
import json

sel = selectors.DefaultSelector()

load_dotenv()

# TODO: flesh out this data structure if needed
accounts = {}
messageId = 0

# HELPER FOR UNIT TESTING
def get_accounts_structure():
    """
    Returns the accounts dictionary used by the server.

    Parameters
    ----------
    None.

    Returns
    -------
    accounts: dict

    Notes
    -----
    This function is ONLY USED FOR TESTING.
    """
    return accounts

def reset_messageId():
    """
    Sets messageId to 0 in the server.

    Parameters
    ----------
    None.

    Returns
    -------
    None.

    Notes
    -----
    This function is ONLY USED FOR TESTING.
    """
    messageId = 0

def clear_accounts_structure():
    """
    Clears the accounts data structure used by the server.

    Parameters
    ----------
    None.

    Returns
    -------
    None.

    Notes
    -----
    This function is ONLY USED FOR TESTING.
    """
    accounts.clear()

# HELPERS FOR SERVER ACTIONS
def create_account(username, password):
    """
    Attempts to create an account with the given username and password

    Parameters
    ----------
    username : str
        The desired username of the account
    password : str
        The desired password of the account

    Returns
    -------
    list
        list[0] is True or False, and indicates if the account was created successfully
        list[1] is an empty string on success and an error message on failure
    """
    print("Creating account")
    if username not in accounts:
        accounts[username] = {"socket": None, "loggedIn": True, "accountInfo": {"username": username, "password": password}, "messageHistory": []}
        return [True, ""]
    else:
        # error: account is already in the database
        return [False, "ER1: account is already in database"]

def login(username, password, sock):
    """
    Attempts to log a user in with the given username and password

    Parameters
    ----------
    username : str
        The inputted username of the account
    password : str
        The inputted password of the account
    sock : socket
        The socket the user is sending the request to log in from

    Returns
    -------
    list
        list[0] is True or False, and indicates if the user logged in successfully
        list[1] is an empty string on success and an error message on failure

    Notes
    -----
    Attempting to login to the same account twice does not produce an error.
    The second login attempt will return success, and the user will remain logged in.
    """
    if username not in accounts:
        # error: account with that username does not exist
        return [False, "ER1: account with that username does not exist"]
    else:
        if accounts[username]["accountInfo"]["username"] == username and accounts[username]["accountInfo"]["password"] == password:
            # if you try to login twice for some reason nothing happens
            accounts[username]["loggedIn"] = True
            # Bind user to a certain socket on login
            accounts[username]["socket"] = sock
            return [True, ""]
        else:
            # error: incorrect password
            return [False, "ER2: incorrect password"]

def logout(username):
    """
    Attempts to logout a user in with the given username and password

    Parameters
    ----------
    username : str
        The inputted username of the account to logout of

    Returns
    -------
    list
        list[0] is True or False, and indicates if the user logged out successfully
        list[1] is an empty string on success and an error message on failure

    Notes
    -----
    Attempting to logout of the same account twice does not produce an error.
    The second logout attempt will return success, and the user will remain logged out.
    """
    if username not in accounts:
        # error: account with that username does not exist
        return [False, "ER1: account with that username does not exist"]
    else:
        # if you try to logout twice for some reason nothing happens
        accounts[username]["loggedIn"] = False
        # Remove user from a socket at logout
        accounts[username]["socket"] = None
        return [True, ""]

def list_accounts():
    """
    Attempts to logout a user in with the given username and password

    Parameters
    ----------
    None.

    Returns
    -------
    list
        list[0] is always True. This function cannot fail.
        list[1] is a list of all account names stored by the server.
    """
    # Simply return all the accounts, searching for a subset is done on client-side
    accountNames = list(accounts.keys())
    return [True, accountNames]


def send_message(from_username, to_username, message, time):
    """
    Attempts to send a message from one user to another. If the receiving user is logged in, the message
    is marked as delivered instantly. Otherwise, it is marked as undelivered.

    Parameters
    ----------
    from_username: str
        The username of the account sending the message
    to_username: str
        The username of the account receiving the message
    message: str
        The message text
    time:
        A string representing the string to be sent

    Returns
    -------
    list
        list[0] is always True. This function cannot fail.
        list[1] is dictionary containing the the information that is now stored in the server about the
        message that was sent. This dictionary has the following keys: sender, timestamp, message, messageId,
        and delivered.
    """
    global messageId
    if to_username not in accounts:
        return [False, "ER1: account with that username does not exist"]

    if accounts[to_username]["loggedIn"] == True:
        message_dict = {"sender": from_username, "timestamp": time, "message": message, "messageId": messageId, "delivered": True}
        accounts[to_username]["messageHistory"].append(message_dict)
        # TODO: Figure out what to do here to notify the logged-in user
        # Do we somehow send it immediately to through the socket to the 2nd client?
    else:
        # The receiving user is logged out, add the message to their list of messages
        message_dict = {"sender": from_username, "timestamp": time, "message": message, "messageId": messageId, "delivered": False}
        accounts[to_username]["messageHistory"].append(message_dict)
    # Each time a message is sent the messageId counter goes up
    messageId += 1
    return [True, message_dict]

def read_message(username, num):
    """
    Attempts to send a message from one user to another. If the receiving user is logged in, the message
    is marked as delivered instantly. Otherwise, it is marked as undelivered.

    Parameters
    ----------
    username: str
        The username of the account requesting to read messages
    num: int
        The number of messages requested

    Returns
    -------
    list
        list[0] is always True. This function cannot fail.
        list[1] is dictionary containing two pieces of data.
        list[1]["num_read"] is the number of messages read, which may be less than num if the user
        had less than num undelivered messages.
        list[1]["messages"] is a list of dictionaries containint information about the messages that were read.
        Each message has the following keys: sender, timestamp, message, messageId, and delivered.
    """
    # Go through message array and append undelivered messages
    num_read = 0
    returned_messages = []
    print("messages", accounts[username]["messageHistory"])
    for message in accounts[username]["messageHistory"]:
        if message["delivered"] == False:
            returned_messages.append(message)
            num_read += 1
            if num_read == num:
                break

    # TODO: Add messageId here
    return [True, {"num_read": num_read, "messages": returned_messages}]

def delete_message(username, id):
    """
    Attempts to delete a message with a specific ID from a user's list of messages.

    Parameters
    ----------
    username: str
        The username of the account requesting to delete the message
    id: int
        The ID of the message to delete

    Returns
    -------
    list
        list[0] is True or False, and indicates if the user deleted the requested message successfully
        list[1] is an empty string on success and an error message on failure
    """
    print("Deleting message", id, "from", username)
    if username not in accounts:
        return [False, "ER3: attempting to delete a message from an account that does not exist"]
    # parsing error
    message_id = int(id)
    for i in range(len(accounts[username]["messageHistory"])):
        if accounts[username]["messageHistory"][i]["messageId"] == message_id:
            del accounts[username]["messageHistory"][i]
            return [True, ""]
    return [False, "ER4: account did not receive message with that id"]

def delete_account(username):
    """
    Deletes a account with the given username.

    Parameters
    ----------
    username: str
        The username of the account to delete

    Returns
    -------
    list
        list[0] is True or False, and indicates if the user deleted the requested account successfully
        list[1] is an empty string on success and an error message on failure
    """
    if username not in accounts:
        return [False, "ER1: attempting to delete an account that does not exist"]
    else:
        del accounts[username]
        return [True, ""]


# HELPERS FOR DEALING WITH SOCKETS
def accept_wrapper(sock):
    """
    Accepts a new connection from a client.

    Parameters
    ----------
    sock: socket
        The socket of the request comes from.

    Returns
    -------
    None.
    """
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", user=b"")
    # let alice know that we dont need read and write
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# WIRE PROTOCOL VERSION
def service_connection_wp(key, mask):
    """
    Services a connection from a client using a custom wire protocol.

    Parameters
    ----------
    key: namedtuple
    mask: selectors.EVENT_READ / selectors.EVENT_WRITE

    Returns
    -------
    None.

    Notes
    -----
    This version understand the custom wire protocol.
    Though this function does not return, the server will always send some kind of response to the client.
    In the case where a send message request is made, and the receiving user is logged in, the server will
    send an additional message to the receiving user's socket with the new message information.
    """
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        # TODO: Recieve the first numeric bytes + turn into a number
        str_bytes = ""
        recv_data = sock.recv(1)
        while recv_data:
            if len(recv_data.decode("utf-8")) > 0:
                if (recv_data.decode("utf-8")).isnumeric():
                    str_bytes += recv_data.decode("utf-8")
                else:
                    break
            recv_data = sock.recv(1)
        if not recv_data:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

        num_bytes = int(str_bytes)

        # TODO: read more bytes using recv until you've fit all the bytes in
        data.outb += recv_data
        cur_bytes = 1
        while(cur_bytes < num_bytes):
            recv_data = sock.recv(num_bytes - cur_bytes)
            if recv_data:
                print("RECEIVED RAW DATA:", recv_data)
                data.outb += recv_data
                cur_bytes += len(recv_data.decode("utf-8"))
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()

    if mask & selectors.EVENT_WRITE:
        if not data.outb:
            return
        if data.outb:
            # TODO: change this line to process as we need to
            in_data = data.outb.decode("utf-8")
            # Flush out the input data from the buffer so that things remain synced
            data.outb = data.outb[len(in_data):]
            # Get 2 letter request type code
            request_type = in_data[:2]
            # The rest of the sent over data is the data needed to complete the request
            in_data = in_data[2:]

            # Reserve error code ER0 for unknown request type
            return_data = "ER0"
            match request_type:
                case "CR":
                    # create account
                    username, password = in_data.split(" ")
                    call_info = create_account(username, password)
                    if call_info[0] == True:
                        return_data = "CRT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "LI":
                    # login
                    username, password = in_data.split(" ")
                    call_info = login(username, password, sock)
                    if call_info[0] == True:
                        return_data = "LIT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "LO":
                    # logout
                    username = in_data
                    call_info = logout(username)
                    if call_info[0] == True:
                        return_data = "LOT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "LA":
                    # list accounts
                    acct_names = list_accounts()[1]
                    return_data = "LAT" + " ".join(acct_names)

                case "SE":
                    in_data_array = in_data.split(" ")
                    from_username = in_data_array[0]
                    to_username = in_data_array[1]
                    time = in_data_array[2]
                    message = " ".join(in_data_array[3:])
                    # from_username, to_username, time, message = in_data.split(" ")
                    call_info = send_message(from_username, to_username, message, time)
                    # send message
                    # TODO: should we send a notif to the receiver's socket if they are logged on?
                    if call_info[0] == True:
                        return_data = "SET"
                        if accounts[to_username]["loggedIn"] == True:
                            # to_data = accounts[to_username]["data"]
                            to_sock = accounts[to_username]["socket"]
                            message_dict = call_info[1]
                            sending_data = "SEL" + str(message_dict["messageId"]) + " " + message_dict["sender"] + " " + message_dict["timestamp"] + " " + str(len(message_dict["message"])) + " "  + message_dict["message"]
                            sending_data = str(len(sending_data)) + sending_data
                            # Send data to the logged in user's socket
                            sending_data = sending_data.encode("utf-8")
                            sent = to_sock.sendall(sending_data)
                            # to_data.outb = to_data.outb[total_len_sending+1:]

                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "RE":
                    username, num = in_data.split(" ")
                    call_info = read_message(username, num)
                    if call_info[0] == True:
                        return_data = "RET" + str(call_info[1]["num_read"])
                        for message in call_info[1]["messages"]:
                            return_data += " " + str(message["messageId"]) + " " + message["sender"]  + " " + message["timestamp"] + " " + str(len(message["message"])) + message["message"]
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "DM":
                    # delete message
                    username, id = in_data.split(" ")
                    print("case DM Deleting message", id, "from", username)
                    call_info = delete_message(username, id)
                    if call_info[0] == True:
                        return_data = "DMT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "DA":
                    username = in_data
                    call_info = delete_account(username)
                    if call_info[0] == True:
                        return_data = "DAT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

            # return_data = trans_to_pig_latin(data.outb.decode("utf-8"))
            return_data = str(len(return_data)) + return_data
            print("returning: ", return_data)
            return_data = return_data.encode("utf-8")
            sent = sock.sendall(return_data)

# JSON Version
def service_connection_json(key, mask):
    """
    Services a connection from a client using json.

    Parameters
    ----------
    key: namedtuple
    mask: selectors.EVENT_READ / selectors.EVENT_WRITE

    Returns
    -------
    None.

    Notes
    -----
    This version understands json.
    Though this function does not return, the server will always send some kind of response to the client.
    In the case where a send message request is made, and the receiving user is logged in, the server will
    send an additional message to the receiving user's socket with the new message information.
    """
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        # TODO: Recieve the first numeric bytes + turn into a number
        str_bytes = ""
        recv_data = sock.recv(1)
        print("recv_data", recv_data.decode("utf-8"))
        while recv_data:
            if len(recv_data.decode("utf-8")) > 0:
                if (recv_data.decode("utf-8")).isnumeric():
                    str_bytes += recv_data.decode("utf-8")
                else:
                    break
            recv_data = sock.recv(1)
        if not recv_data:
            print("closing connection here")
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
        else:
            num_bytes = int(str_bytes)

            # TODO: read more bytes using recv until you've fit all the bytes you need in
            data.outb += recv_data
            cur_bytes = 1
            while(cur_bytes < num_bytes):
                recv_data = sock.recv(num_bytes - cur_bytes)
                if recv_data:
                    print("RECEIVED RAW DATA:", recv_data)
                    data.outb += recv_data
                    cur_bytes += len(recv_data.decode("utf-8"))
                else:
                    print(f"Closing connection to {data.addr}")
                    sel.unregister(sock)
                    sock.close()


    if mask & selectors.EVENT_WRITE:
        if not data.outb:
            return
        if data.outb:
            # TODO: change this line to process as we need to
            in_data = data.outb.decode("utf-8")
            # Flush out the input data from the buffer so that things remain synced
            data.outb = data.outb[len(in_data):]
            # Convert data to json format
            in_data_json = json.loads(in_data)
            # # Get 2 letter request type code
            request_type = in_data_json["type"]
            # # The rest of the sent over data is the data needed to complete the request
            # in_data = in_data[2:]

            # Reserve error code ER0 for unknown request type
            return_data = {"success": False, "errorMsg": "ER0: unknown request type"}
            match request_type:
                case "CR":
                    # create account
                    # print(in_data)
                    username = in_data_json["username"]
                    password = in_data_json["password"]
                    call_info = create_account(username, password)
                    # print(accounts)
                    if call_info[0] == True:
                        return_data = {"type" : "CRT", "success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LI":
                    # login
                    username = in_data_json["username"]
                    password = in_data_json["password"]
                    call_info = login(username, password, sock)

                    if call_info[0] == True:
                        return_data = {"type" : "LIT", "success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LO":
                    # logout
                    username = in_data_json["username"]
                    call_info = logout(username)
                    if call_info[0] == True:
                        return_data = {"type" : "LOT", "success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LA":
                    # list accounts
                    acct_names = list_accounts()[1]
                    return_data = {"type" : "LAT", "success": True, "accounts": acct_names, "errorMsg": ""}

                case "SE":
                    print("SENDING MESSAGE", in_data)
                    # in_data_array = in_data.split(" ")
                    # from_username = in_data_array[0]
                    # to_username = in_data_array[1]
                    # time = in_data_array[2]
                    # message = " ".join(in_data_array[3:])
                    from_username = in_data_json["from_username"]
                    to_username = in_data_json["to_username"]
                    time = in_data_json["timestamp"]
                    message = in_data_json["message"]
                    # from_username, to_username, time, message = in_data.split(" ")
                    call_info = send_message(from_username, to_username, message, time)
                    # send message
                    # TODO: should we send a notif to the receiver's socket if they are logged on?
                    if call_info[0] == True:
                        return_data = {"type" : "SET", "success": True, "errorMsg": ""}
                        if accounts[to_username]["loggedIn"] == True:
                            # to_data = accounts[to_username]["data"]
                            to_sock = accounts[to_username]["socket"]
                            message_dict = call_info[1]
                            message_dict["type"] = "SEL"
                            # sending_data = "SEL" + str(message_dict["messageId"]) + " " + message_dict["sender"] + " " + message_dict["timestamp"] + " " + str(len(message_dict["message"])) + message_dict["message"]
                            sending_data = json.dumps(message_dict)
                            sending_data = str(len(sending_data)) + sending_data
                            # Send data to the logged in user's socket
                            sending_data = sending_data.encode("utf-8")
                            sent = to_sock.sendall(sending_data)
                            # to_data.outb = to_data.outb[total_len_sending+1:]

                    else:
                        # Pull the entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "RE":
                    print("READING MESSAGES", in_data)
                    username = in_data_json["username"]
                    num = in_data_json["number"]
                    call_info = read_message(username, num)
                    if call_info[0] == True:
                        return_data = call_info[1]
                        return_data["type"] = "RET"
                    else:
                        # Pull the entire error message for json
                        return_data["errorMsg"] = call_info[1]
                    print("return_data", return_data)

                case "DM":
                    # delete message
                    username = in_data_json["username"]
                    id = in_data_json["id"]
                    call_info = delete_message(username, id)
                    if call_info[0] == True:
                        return_data = {"success": True, "errorMsg": ""}
                    else:
                        # Pull the entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "DA":
                    username = in_data_json["username"]
                    call_info = delete_account(username)
                    if call_info[0] == True:
                        return_data = {"success": True, "errorMsg": ""}
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data["errorMsg"] = call_info[1]

            # return_data = trans_to_pig_latin(data.outb.decode("utf-8"))
            print(str(len(return_data)))
            print(return_data)
            # Send Json versions back to client
            return_data = json.dumps(return_data)
            return_data = str(len(return_data)) + return_data
            print("returning: ", return_data)
            return_data = return_data.encode("utf-8")
            sent = sock.sendall(return_data)

if __name__ == "__main__":
    HOST = os.environ.get("HOST_SERVER")
    PORT = int(os.environ.get("PORT_SERVER"))
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    # Version that understands the wire protocol
                    # service_connection_wp(key, mask)
                    # Version that understands json
                    service_connection_json(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        print("closing server")
        sel.close()