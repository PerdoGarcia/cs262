import threading
import random
from queue import Queue
import dotenv

import socket
import selectors
import types
import os
import json

dotenv.load_dotenv()

def instruction_performer(message_queue, clock_speed, run_event):
    # Starts with logical clock at time 0
    clock = 0
    # TODO: Add instruction execution here

    # TODO: Add logging code
    pass

# Returns the message sent by the connection
def service_connection(key, mask):
    pass

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
    

# Runs the machine (turns into listening thread)
def run_machine(clock_speed, port_number, run_event):
    message_queue = Queue(maxsize=0)
    worker = threading.Thread(target=instruction_performer, args=(message_queue, clock_speed, run_event))

    # TODO: Add socket listening code here
    HOST = os.environ.get("HOST_SERVER")
    PORT = port_number
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    sel = selectors.DefaultSelector()
    sel.register(lsock, selectors.EVENT_READ, data=None)

    # Listening socket
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # Accept a new connection
                    sock = key.fileobj
                    conn, addr = sock.accept()
                    print(f"Accepted connection from {addr}")
                    conn.setblocking(False)
                    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", user=b"")
                    events = selectors.EVENT_READ | selectors.EVENT_WRITE
                    sel.register(conn, events, data=data)
                else:
                    # Extract message from the connection
                    # Version that understands the wire protocol
                    service_connection(key, mask)
    except KeyboardInterrupt:
        # TODO: add code for shutting down thread
        print("Caught keyboard interrupt, exiting")
    finally:
        print("Closing server")
        sel.close()
    pass

def main():
    clock_speeds = [random.randint(1,6) for i in range(3)]
    run_event = threading.Event()

    # TODO: add code for starting each machine here