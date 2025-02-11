# Adapted from lecture code

import socket
import selectors
import types
# Helpers for processing each file, separated for conciseness
# from server_helpers import *
sel = selectors.DefaultSelector()

# TODO: CHANGE THIS DO NOT HARD CODE
HOST = "127.0.0.1"
PORT = 54400

# TODO: flesh out this data structure if needed
accounts = {}
messageId = 0

# HELPERS FOR SERVER ACTIONS
def create_account(username, password):
    print("Creating account")
    if username not in accounts:
        accounts[username] = {"loggedIn": True, "accountInfo": {"username": username, "password": password}, "messageHistory": []}
        return [True, ""]
    else:
        # error: account is already in the database
        return [False, "ER1: account is already in database"]

def login(username, password):
    if username not in accounts:
        # error: account with that username does not exist
        return [False, "ER1: account with that username does not exist"]
    else:
        if accounts["accountInfo"]["username"] == username and accounts["accountInfo"]["password"] == password:
            # if you try to login twice for some reason nothing happens
            accounts[username]["loggedIn"] = True
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
        return [True, ""]

def list_accounts():
    # Simply return all the accounts, searching for a subset is done on client-side
    accountNames = list(accounts.keys())
    return [True, accountNames]


def send_message(from_username, to_username, message, time):
    if to_username not in accounts:
        return [False, "ER1: account with that username does not exist"]

    if accounts[to_username]["loggedIn"] == True:
        message_dict = {"sender": from_username, "timestamp": time, "message": message, "messageId": messageId, "delivered": True}
        accounts[to_username]["messageHistory"].append(message_dict)
        # TODO: Figure out what to do here to notify the logged-in user
    else:
        # The receiving user is logged out, add the message to their list of messages
        message_dict = {"sender": from_username, "timestamp": time, "message": message, "messageId": messageId, "delivered": False}
        accounts[to_username]["messageHistory"].append(message_dict)
    # Each time a message is sent the messageId counter goes up
    messageId += 1

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
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# NOTE: CURRENTLY WIRE PROTOCOL VERSION
def service_connection_wp(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
        sel.unregister(sock)
        sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            # TODO: change this line to process as we need to
            in_data = data.outb.decode("utf-8")
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
                    if call_info[0] == True:
                        return_data = "CRT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "LI":
                    # login
                    username, password = in_data.split(" ")
                    call_info = login(username, password)
                    if call_info[0] == True:
                        return_data = "LIT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "LO":
                    # logout
                    username = in_data
                    call_info = logout(username)
                    if call_info[0] == True:
                        return_data = "LOT"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "LA":
                    # list accounts
                    acct_names = list_accounts()[1]
                    return_data = "LI" + " ".join(acct_names)

                case "SE":
                    from_username, to_username, time, message = in_data.split(" ")
                    call_info = send_message(from_username, to_username, message, time)
                    # send message
                    # TODO: should we send a notif to the receiver's socket if they are logged on?
                    if call_info[0] == True:
                        return_data = "SET"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "RE":
                    username, num = in_data.split(" ")
                    call_info = read_message(username, num)
                    if call_info[0] == True:
                        return_data = "RET" + str(call_info[1]["num_read"])
                        for message in call_info[1]["messages"]:
                            return_data += " " + str(len(message)) + " " + message
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "DM":
                    # delete message
                    username, id = in_data.split(" ")
                    call_info = delete_message(username, id)
                    if call_info[0] == True:
                        return_data = "SET"
                    else:
                        # Pull just the error code out when we are using custom wire protocol
                        return_data = call_info[:3]

                case "DA":
                    username = in_data
                    return "DAT"

            # return_data = trans_to_pig_latin(data.outb.decode("utf-8"))
            return_data = return_data.encode("utf-8")
            sent = sock.send(return_data)
            data.outb = data.outb[sent:]

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

                print("Recieved data")
                print(key.data == None)
                if key.data == None:
                    accept_wrapper(key.fileobj)
                else:
                    print("processing request: " + key.data.outb.decode("utf-8"))
                    # Version that understands the wire protocol
                    service_connection_wp(key, mask)
                    # Version that understands json
                    # service_connection_json(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()