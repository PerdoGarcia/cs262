# Adapted from lecture code

import socket
import selectors
import types
import os
from dotenv import load_dotenv
import json

sel = selectors.DefaultSelector()

load_dotenv()

# TODO: CHANGE THIS DO NOT HARD CODE
HOST = os.environ.get("HOST_SERVER")
PORT = int(os.environ.get("PORT_SERVER"))

# TODO: flesh out this data structure if needed
accounts = {}
messageId = 0

# HELPERS FOR SERVER ACTIONS
def create_account(username, password):
    print("Creating account")
    if username not in accounts:
        accounts[username] = {"socket": None, "data": None, "loggedIn": True, "accountInfo": {"username": username, "password": password}, "messageHistory": []}
        return [True, ""]
    else:
        # error: account is already in the database
        return [False, "ER1: account is already in database"]

def login(username, password, sock, data):
    # TODO fix login later talk with alice
    # TODO: when a user logs in bind their username to the socket that requested it if it succeeded
    if username not in accounts:
        # error: account with that username does not exist
        return [False, "ER1: account with that username does not exist"]
    else:
        if accounts[username]["accountInfo"]["username"] == username and accounts[username]["accountInfo"]["password"] == password:
            # if you try to login twice for some reason nothing happens
            accounts[username]["loggedIn"] = True
            # Bind user to a certain socket on login
            accounts[username]["socket"] = sock
            accounts[username]["data"] = data
            return [True, ""]
        else:
            # error: incorrect password
            return [False, "ER2: incorrect password"]

def logout(username):
    if username not in accounts:
        # error: account with that username does not exist
        return [False, "ER1: account with that username does not exist"]
    else:
        # if you try to logout twice for some reason nothing happens
        accounts[username]["loggedIn"] = False
        # Remove user from a socket at logout
        accounts[username]["socket"] = None
        accounts[username]["data"] = None
        return [True, ""]

def list_accounts():
    # Simply return all the accounts, searching for a subset is done on client-side
    accountNames = list(accounts.keys())
    return [True, accountNames]


def send_message(from_username, to_username, message, time):
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
    # get messages from the end?
    num_read = 0
    returned_messages = []
    for message in accounts[username]["messageHistory"]:
        if message["delivered"] == False:
            returned_messages.append(message)
            num_read += 1
            if num_read == num:
                break

    # TODO: Add messageId here
    return [True, {"num_read": num_read, "messages": returned_messages}]

def delete_message(username, id):
    if username not in accounts:
        return [False, "ER1: attempting to delete a message from an account that does not exist"]

    for i in range(len(accounts[username]["messageHistory"])):
        if accounts[username]["messageHistory"][i]["messageId"] == id:
            del accounts[username]["messageHistory"][i]
            return [True, ""]
    return [False, "ER2: account did not receive message with that id"]

def delete_account(username):
    del accounts[username]
    return [True, ""]


# HELPERS FOR DEALING WITH SOCKETS
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", user=b"")
    # let alice know that we dont need read and write
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# WIRE PROTOCOL VERSION
def service_connection_wp(key, mask):
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
                    print(in_data)
                    username, password = in_data.split(" ")
                    call_info = create_account(username, password)
                    print(accounts)
                    if call_info[0] == True:
                        return_data = "CRT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[1][:3]

                case "LI":
                    # login
                    username, password = in_data.split(" ")
                    call_info = login(username, password, sock, data)
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
                    print("SENDING MESSAGE", in_data)
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
                            to_data = accounts[to_username]["data"]
                            to_sock = accounts[to_username]["socket"]
                            message_dict = call_info[1]
                            sending_data = "SEL" + str(message_dict["messageId"]) + " " + message_dict["sender"] + " " + message_dict["timestamp"] + " " + str(len(message_dict["message"])) + message_dict["message"]
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
            print(str(len(return_data)))
            print(return_data)
            return_data = str(len(return_data)) + return_data
            print("returning: ", return_data)
            return_data = return_data.encode("utf-8")
            sent = sock.sendall(return_data)

# JSON Version
def service_connection_json(key, mask):
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
                        return_data = {"success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LI":
                    # login
                    username = in_data_json["username"]
                    password = in_data_json["password"]
                    call_info = login(username, password, sock, data)

                    if call_info[0] == True:
                        return_data = {"success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LO":
                    # logout
                    username = in_data_json["username"]
                    call_info = logout(username)
                    if call_info[0] == True:
                        return_data = {"success": True, "errorMsg": ""}
                    else:
                        # Pull entire error message for json
                        return_data["errorMsg"] = call_info[1]

                case "LA":
                    # list accounts
                    acct_names = list_accounts()[1]
                    return_data = {"success": True, "accounts": acct_names, "errorMsg": ""}

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
                        return_data = {"success": True, "errorMsg": ""}
                        if accounts[to_username]["loggedIn"] == True:
                            to_data = accounts[to_username]["data"]
                            to_sock = accounts[to_username]["socket"]
                            message_dict = call_info[1]
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
                    username = in_data_json["username"]
                    num = in_data_json["number"]
                    call_info = read_message(username, num)
                    if call_info[0] == True:
                        return_data = call_info[1]
                    else:
                        # Pull the entire error message for json
                        return_data["errorMsg"] = call_info[1]

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
                    service_connection_wp(key, mask)
                    # Version that understands json
                    # service_connection_json(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()