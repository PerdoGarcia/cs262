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

# HELPERS FOR SERVER ACTIONS
def create_account(username, password):
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



# HELPERS FOR DEALING WITH SOCKETS
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# NOTE: CURRENTLY WIRE PROTOCOL VERSION
def service_connection(key, mask):
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
                    pass
                case "SE":
                    # send message
                    pass
                case "RE":
                    # read message
                    pass
                case "DM":
                    #delete message
                    pass
                case "DA":
                    # delete account
                    pass

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
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()