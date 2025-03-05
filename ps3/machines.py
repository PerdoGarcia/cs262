from multiprocessing import Process, Event
import threading
import random
from queue import Queue
import dotenv
from datetime import datetime

import socket
import selectors
import types
import os
import json
import time

dotenv.load_dotenv()

# globals

clock_speeds = [random.randint(1,6) for i in range(3)]
# Basically changes the probability of sending a message to another machine
MAX_ROLL = 10

def instruction_performer(message_queue, port_number, clock_speed, connections, connections_lock, run_event):
    """
    This function simulates the behavior of a machine in a distributed system and performs lamport clock operations.
    First it initializes the machine with a logical clock at time 0.
    Then it waits for all machines to connect - using the connections_lock to ensure connections are added to the dict properly and
    run_event to signal when the machines should start running and logging.
    It then runs a loop that simulates the machine's behavior by performing the following operations:
    1. If the message queue is not empty, it logs the message and updates the logical clock.
    2. If the message queue is empty, it generates a random event (send message to another machine, send message to next machine, send message to all machines, or do nothing) and performs the event.
    3. It then updates the logical clock.
    4. It sleeps for the remainder of the second to ensure the machine runs at the specified clock
    5. It repeats the loop until the run_event is false (60 seconds have passed).

    Args:
        message_queue (Queue): A queue to hold messages to be processed
        port_number (int): port number of the machine
        clock_speed (int): Machines simulated clock speed
        connections (dict): A dictionary of connections to other machines for use in sending messages
        connections_lock (threading.Lock): Ensure connections are added to the dict properly
        run_event (multiprocessing.Event): To signal when the machines should start running and logging
    """


    # Starts with logical clock at time 0
    clock = 0
    machine_id = port_number - 5001

    # maps machine id to socket
    with connections_lock:
        temp_connections = connect_to_other_machines(machine_id)
        for other_id, sock in temp_connections.items():
            connections[other_id] = sock


    # wait for all machines to connect
    run_event.wait()

    # On start log the machine starting
    log_filename = f"machine_{machine_id}.log"
    log_file = open(log_filename, "w")
    log_message(log_file, "INITIAL", f"Machine {machine_id} initialized with clock speed {clock_speed}", clock, message_queue.qsize())

    # Run while the run_event is true
    while True:
        second_start = time.time()
        for _ in range(clock_speed):
            if not message_queue.empty():
                print("Queue not empty")
                message = message_queue.get_nowait()
                # just log the message
                clock = max(clock, message["time"]) + 1
                log_message(log_file, "RECEIVE ", f"Receive machine {message['sender']}", clock, message_queue.qsize())
            else:
                event = random.randint(1, MAX_ROLL)
                if event == 1:
                    if connections:
                        recipient_id = random.choice(list(connections.keys()))
                        message = {
                            "time": clock,
                            "sender": machine_id,
                            "recipient": recipient_id,
                        }
                        send_message(message, connections[recipient_id])
                        log_message(log_file, "  SEND  ", f"Sent to machine {recipient_id}", clock, message_queue.qsize())

                elif event == 2:
                    recipient_id = (machine_id + 1) % 3
                    if recipient_id in connections:
                        message = {
                            "time": clock,
                            "sender": machine_id,
                            "recipient": recipient_id,
                        }
                        send_message(message, connections[recipient_id])
                        log_message(log_file, "  SEND  ", f"Sent to machine {recipient_id}", clock, message_queue.qsize())

                elif event == 3:
                    for recipient, sock in connections.items():
                        if recipient != machine_id:
                            message = {
                                "time": clock,
                                "sender": machine_id,
                                "recipient": recipient,
                            }
                            send_message(message, sock)
                            log_message(log_file, "  SEND  ", f"Sent to machine {recipient}", clock, message_queue.qsize())

                else:
                    log_message(log_file, "INTERNAL", "    No Details   ", clock, message_queue.qsize())

                clock += 1

        # calc how long we've spent doing operations
        elapsed = time.time() - second_start

        # Sleep for the remainder of the second
        sleep_time = max(0, 1.0 - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

def send_message(message, sock):
    # sends the message to the socket
    try:
        message_str = str(len(json.dumps(message))) + json.dumps(message)
        sock.sendall(message_str.encode("utf-8"))
        return True
    except Exception as e:
        print(f"ERROR SENDING: {e} for message {message}")
        return False

def log_message(log_file, event_type, details, logical_clock, queue_size):
    # logs the message to the log file
    system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_line = f"System Time: {system_time} | | {event_type} | | {details} | | Queue Size: {queue_size} | | Logical Clock: {logical_clock}\n"
    log_file.write(message_line)
    log_file.flush()
    return


# Adds the message sent by the connection to the queue
def service_connection(key, message_queue, sel):
    sock = key.fileobj
    data = key.data
    # READING IN THE MESSAGE
    # Reads the first number that is sent over to figure out how many total bytes are in the message
    str_bytes = ""
    try:
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
    except BlockingIOError:
        # Basically if there's no data to read, just move on
        pass

    except Exception as e:
        print(f"Error reading message: {e}")

    # PROCESSING THE MESSAGE
    # If there's no data, do nothing
    if not data.outb:
        return
    if data.outb:
        try:
            in_data = data.outb.decode("utf-8")
            # Flush out the input data from the buffer
            data.outb = data.outb[len(in_data):]
            # Convert data to json format
            in_data_json = json.loads(in_data)
            # Adds message to the queue
            message_queue.put(in_data_json)
        except Exception as e:
            print(f"Error processing message: {e}")

# HELPERS FOR DEALING WITH SOCKETS
def accept_wrapper(sock, sel, machine_id, connections, connections_lock):
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

    # Populate connections to use for sending messages
    for other_id in range(machine_id):
        if other_id not in connections:
            with connections_lock:
                connections[other_id] = conn
            break

    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", user=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def connect_to_other_machines(machine_id):
    machine_connections = {}
    HOST = os.environ.get("HOST_SERVER")
    all_ports = [5001, 5002, 5003]
    other_ports = [p for p in all_ports if p != (5001 + machine_id)]

    # This prevents duplicate connections
    for port in other_ports:
        other_machine_id = port - 5001
        # Only machines with lower IDs initiate connections
        if machine_id < other_machine_id:
            while True:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((HOST, port))
                    machine_connections[other_machine_id] = sock
                    print(f"Machine {machine_id} connected to machine {other_machine_id}")
                    break
                except Exception as e:
                    time.sleep(0.5)
    return machine_connections


# Runs the machine (turns into listening thread)
def run_machine(clock_speed, port_number, run_event):
    message_queue = Queue(maxsize=0)
    connections = {}
    connections_lock = threading.Lock()
    # Thread that handles instruction execution gets spawned here
    worker = threading.Thread(target=instruction_performer, args=(message_queue, port_number, clock_speed, connections, connections_lock, run_event))
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
    while True:
        # Negative timeout is used to not block so that we can exit the loop on a keyboard interrupt
        events = sel.select(timeout=-1)
        for key, mask in events:
            if key.data is None:
                # Accept a new connection
                accept_wrapper(key.fileobj, sel, port_number - 5001, connections, connections_lock)
            else:
                # Service the connection
                service_connection(key, message_queue, sel)
    # Join the worker thread before machine exits
    worker.join()
    pass

def main():
    # run_event controls when the machines are running (allows for graceful thread closure)
    run_event = Event()

    # Start each "machine" in a separate Process
    m1 = Process(target=run_machine, args=(clock_speeds[0], 5001, run_event), daemon=True)
    m2 = Process(target = run_machine, args = (clock_speeds[1], 5002, run_event), daemon=True)
    m3 = Process(target = run_machine, args = (clock_speeds[2], 5003, run_event), daemon=True)
    m1.start()
    m2.start()
    m3.start()

    try:
        # TODO: probably make this more elegant
        # wait for machines to connect to each other
        time.sleep(5)
        run_event.set()
        time.sleep(60)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
        print("Attempting to close processes")
        m1.join()
        m2.join()
        m3.join()
        print("Threads successfully closed")

    print("Exiting main process")
    pass

if __name__ == '__main__':
    main()