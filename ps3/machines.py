import threading
import random
from queue import Queue
import dotenv

import socket
import selectors
import types
import os
import json
import time

dotenv.load_dotenv()

def instruction_performer(message_queue, clock_speed, run_event):
    # Starts with logical clock at time 0
    clock = 0
    # TODO: Add instruction execution here
    # Run while the run_event is true
    while run_event.is_set():
        pass

    # TODO: Add logging code
    pass

# Adds the message sent by the connection to the queue
def service_connection(key, message_queue, sel):
    sock = key.fileobj
    data = key.data
    # READING IN THE MESSAGE
    # Reads the first number that is sent over to figure out how many total bytes are in the message
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
        # Recieved no data, close connection
        print(f"Closing connection to {data.addr}")
        sel.unregister(sock)
        sock.close()
    else:
        num_bytes = int(str_bytes)

        # Reads the next num_bytes bytes to get the full message
        data.outb += recv_data
        cur_bytes = 1
        while(cur_bytes < num_bytes):
            recv_data = sock.recv(num_bytes - cur_bytes)
            if recv_data:
                data.outb += recv_data
                cur_bytes += len(recv_data.decode("utf-8"))
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()

    # PROCESSING THE MESSAGE
    # If there's no data, do nothing
    if not data.outb:
        return
    if data.outb:
        in_data = data.outb.decode("utf-8")
        # Flush out the input data from the buffer so that things remain synced
        data.outb = data.outb[len(in_data):]
        # Convert data to json format
        in_data_json = json.loads(in_data)
        # Adds message to the queue
        message_queue.put(in_data_json)

# HELPERS FOR DEALING WITH SOCKETS
def accept_wrapper(sock, sel):
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
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    

# Runs the machine (turns into listening thread)
def run_machine(clock_speed, port_number, run_event):
    message_queue = Queue(maxsize=0)
    # Thread that handles instruction execution gets spawned here
    worker = threading.Thread(target=instruction_performer, args=(message_queue, clock_speed, run_event))
    worker.start()

    # Code for setting up the listening socket
    HOST = os.environ.get("HOST_SERVER")
    PORT = port_number
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    sel = selectors.DefaultSelector()
    sel.register(lsock, selectors.EVENT_READ, data=None)

    # Listening socket loop (until we get keyboard interrupted)
    while run_event.is_set():
        # Negative timeout is used to not block so that we can exit the loop on a keyboard interrupt
        events = sel.select(timeout=-1)
        for key, mask in events:
            if key.data is None:
                # Accept a new connection
                accept_wrapper(key.fileobj, sel)
            else:
                # Service the connection
                service_connection(key, message_queue, sel)
    # Join the worker thread before machine exits
    worker.join()
    pass

def main():
    clock_speeds = [random.randint(1,6) for i in range(3)]
    # run_event controls when the machines are running (allows for graceful thread closure)
    run_event = threading.Event()
    run_event.set()

    # Start each "machine" in a separate thread
    m1 = threading.Thread(target = run_machine, args = (clock_speeds[0], 5001, run_event))
    m2 = threading.Thread(target = run_machine, args = (clock_speeds[1], 5002, run_event))
    m3 = threading.Thread(target = run_machine, args = (clock_speeds[2], 5003, run_event))
    m1.start()
    m2.start()
    m3.start()

    try:
        # TODO: probably make this more elegant
        while True:
            time.sleep(.1)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
        print("Attempting to close threads")
        run_event.clear()
        m1.join()
        m2.join()
        m3.join()
        print("Threads successfully closed")

if __name__ == '__main__':
    main()