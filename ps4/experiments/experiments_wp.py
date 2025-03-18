#!/usr/bin/env python3

import socket
import time
import datetime
import random
import string
import csv
import os
import threading
import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

# Constants
SERVER_HOST = os.environ.get("SERVER_IP", "localhost")
SERVER_PORT = int(os.environ.get("PORT_SERVER", 5002))
NUM_MESSAGES = 100  # Default number of messages to send in experiment
MESSAGE_SIZES = [10, 100, 1000, 10000]  # Message sizes in bytes to test
NUM_USERS = 5  # Number of users to create for testing

# Class to measure socket call duration and data size
class WireMetrics:
    def __init__(self):
        self.metrics = []
        self.lock = threading.Lock()

    def record(self, operation, start_time, end_time, payload_size, status, additional_info=""):
        with self.lock:
            self.metrics.append({
                'operation': operation,
                'duration_ms': (end_time - start_time) * 1000,  # Convert to milliseconds
                'payload_size_bytes': payload_size,
                'timestamp': datetime.datetime.now().isoformat(),
                'status': status,
                'additional_info': additional_info
            })

    def save_to_csv(self, filename="wire_metrics.csv"):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['operation', 'duration_ms', 'payload_size_bytes', 'timestamp', 'status', 'additional_info']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics)
        print(f"Metrics saved to {filename}")

    def print_summary(self):
        if not self.metrics:
            print("No metrics collected.")
            return

        operations = {}
        for metric in self.metrics:
            op = metric['operation']
            if op not in operations:
                operations[op] = {
                    'count': 0,
                    'total_duration': 0,
                    'total_size': 0,
                    'success_count': 0
                }

            operations[op]['count'] += 1
            operations[op]['total_duration'] += metric['duration_ms']
            operations[op]['total_size'] += metric['payload_size_bytes']
            if metric['status'] == 'success':
                operations[op]['success_count'] += 1

        print("\n===== EXPERIMENT RESULTS =====")
        print(f"Total operations: {len(self.metrics)}")
        print("\nOperation Stats:")
        print("-" * 80)
        print(f"{'Operation':<20} {'Count':<10} {'Avg Time (ms)':<15} {'Avg Size (bytes)':<20} {'Success Rate':<15}")
        print("-" * 80)

        for op, stats in sorted(operations.items()):
            avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
            avg_size = stats['total_size'] / stats['count'] if stats['count'] > 0 else 0
            success_rate = (stats['success_count'] / stats['count'] * 100) if stats['count'] > 0 else 0

            print(f"{op:<20} {stats['count']:<10d} {avg_duration:<15.2f} {avg_size:<20.2f} {success_rate:<14.1f}%")


# Generate random message of specified size
def generate_message(size):
    return ''.join(random.choice(string.ascii_letters) for _ in range(size))


# Socket client for Wire protocol
class WireSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Establish a connection to the server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def close(self):
        """Close the connection"""
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_receive(self, request_type, data):
        """Send data to server and receive response using wire protocol"""
        if not self.sock:
            raise Exception("Not connected to server")

        # Format according to custom wire protocol
        wire_message = request_type + data
        # Add length prefix
        message = str(len(wire_message)) + wire_message

        # Send data
        self.sock.sendall(message.encode('utf-8'))

        # Read response
        str_bytes = ""
        recv_data = self.sock.recv(1)
        while recv_data:
            if len(recv_data.decode("utf-8")) > 0:
                if (recv_data.decode("utf-8")).isnumeric():
                    str_bytes += recv_data.decode("utf-8")
                else:
                    break
            recv_data = self.sock.recv(1)

        if not recv_data:
            raise Exception("Connection closed by server")

        num_bytes = int(str_bytes)
        response = recv_data
        cur_bytes = 1

        while(cur_bytes < num_bytes):
            recv_data = self.sock.recv(num_bytes - cur_bytes)
            if recv_data:
                response += recv_data
                cur_bytes += len(recv_data.decode("utf-8"))
            else:
                raise Exception("Connection closed by server during response")

        # Return response
        return response.decode('utf-8')


# Main experiment class for Wire protocol
class WireServerExperiment:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.metrics = WireMetrics()
        self.users = []
        self.clients = {}  # Socket clients by username

    def setup_users(self, num_users):
        """Create test users for the experiment"""
        for i in range(num_users):
            username = f"test_user_{i}_{int(time.time())}"
            password = "test_password"

            client = WireSocketClient(self.host, self.port)
            if not client.connect():
                print(f"Failed to connect for user {username}")
                continue

            # Create account
            start_time = time.time()
            try:
                request_data = f"{username} {password}"
                request_size = len(request_data) + 2  # +2 for the "CR" prefix
                response = client.send_receive("CR", request_data)
                end_time = time.time()

                response_size = len(response)
                total_size = request_size + response_size

                # Check for success - response will start with "CRT" for success
                status = 'success' if response.startswith("CRT") else 'failure'
                self.metrics.record('create_account', start_time, end_time, total_size, status, username)

                if status == 'success':
                    self.users.append(username)
                    self.clients[username] = client
                    print(f"Created user: {username}")
                else:
                    print(f"Failed to create user {username}: {response}")
                    client.close()
            except Exception as e:
                end_time = time.time()
                self.metrics.record('create_account', start_time, end_time, 0, 'error', str(e))
                print(f"Error creating user {username}: {str(e)}")
                client.close()

    def login_users(self):
        """Login all test users"""
        for username in self.users:
            if username not in self.clients or self.clients[username] is None:
                # Create new connection if needed
                client = WireSocketClient(self.host, self.port)
                if not client.connect():
                    print(f"Failed to connect for login of user {username}")
                    continue
                self.clients[username] = client

            start_time = time.time()
            try:
                request_data = f"{username} test_password"
                request_size = len(request_data) + 2  # +2 for the "LI" prefix
                response = self.clients[username].send_receive("LI", request_data)
                end_time = time.time()

                response_size = len(response)
                total_size = request_size + response_size

                # Check for success - response will start with "LIT" for success
                status = 'success' if response.startswith("LIT") else 'failure'
                self.metrics.record('login', start_time, end_time, total_size, status, username)

                if status != 'success':
                    print(f"Failed to login user {username}: {response}")
            except Exception as e:
                end_time = time.time()
                self.metrics.record('login', start_time, end_time, 0, 'error', str(e))
                print(f"Error logging in user {username}: {str(e)}")

    def measure_message_delivery(self, message_size, num_messages):
        """Measure message delivery time and data size"""
        if len(self.users) < 2:
            print("Need at least 2 users for message delivery test")
            return

        # Select sender and receiver
        sender = self.users[0]
        receiver = self.users[1]

        print(f"\nTesting message delivery: {num_messages} messages of size {message_size} bytes")
        print(f"Sender: {sender}, Receiver: {receiver}")

        # Set up receiver socket to listen for incoming messages
        def listen_for_messages(username, num_expected):
            messages_received = 0
            client = self.clients.get(username)
            if not client or not client.sock:
                print(f"No connection for receiver {username}")
                return

            # Set socket to non-blocking
            client.sock.setblocking(0)

            try:
                start_time = time.time()
                while messages_received < num_expected and time.time() - start_time < 30:  # 30 second timeout
                    try:
                        # Try to see if there's any data available
                        client.sock.settimeout(0.1)
                        data = client.sock.recv(1)
                        if data:
                            # We have data, switch back to blocking to read properly
                            client.sock.setblocking(1)

                            # Read the message length
                            str_bytes = data.decode("utf-8")
                            while True:
                                next_byte = client.sock.recv(1)
                                if not next_byte:
                                    break
                                next_char = next_byte.decode("utf-8")
                                if not next_char.isnumeric():
                                    break
                                str_bytes += next_char

                            # Read the message content
                            num_bytes = int(str_bytes)
                            message_data = next_byte
                            cur_bytes = 1

                            while cur_bytes < num_bytes:
                                chunk = client.sock.recv(num_bytes - cur_bytes)
                                if chunk:
                                    message_data += chunk
                                    cur_bytes += len(chunk.decode("utf-8"))
                                else:
                                    break

                            # Parse response
                            message = message_data.decode("utf-8")
                            if message.startswith("SEL"):
                                receive_time = time.time()
                                message_size = len(message)
                                self.metrics.record('receive_instant_message', start_time, receive_time,
                                                   message_size, 'success',
                                                   f"message_received={messages_received+1}")
                                messages_received += 1

                                # Set back to non-blocking for next attempt
                                client.sock.setblocking(0)
                    except socket.timeout:
                        # No data available, continue waiting
                        pass
                    except Exception as e:
                        # Some other error
                        print(f"Error listening for instant messages: {e}")
                        break
            except Exception as e:
                print(f"Error in message listener: {e}")

            print(f"Receiver {username} got {messages_received} instant messages")

        # Start listener thread for receiver
        listener_thread = threading.Thread(target=listen_for_messages, args=(receiver, num_messages))
        listener_thread.daemon = True
        listener_thread.start()

        # Allow listener to initialize
        time.sleep(0.5)

        # Send messages
        for i in range(num_messages):
            message_content = generate_message(message_size)
            timestamp = datetime.datetime.now().isoformat()

            # Measure send time
            start_time = time.time()
            try:
                send_data = f"{sender} {receiver} {timestamp} {message_content}"
                request_size = len(send_data) + 2  # +2 for the "SE" prefix
                send_response = self.clients[sender].send_receive("SE", send_data)
                end_time = time.time()

                response_size = len(send_response)
                total_size = request_size + response_size

                # Check for success - response will start with "SET" for success
                status = 'success' if send_response.startswith("SET") else 'failure'
                self.metrics.record('send_message', start_time, end_time, total_size, status,
                                   f"size={message_size}, index={i}")

                if status != 'success':
                    print(f"Failed to send message {i}: {send_response}")

            except Exception as e:
                end_time = time.time()
                self.metrics.record('send_message', start_time, end_time, 0, 'error', str(e))
                print(f"Error sending message {i}: {str(e)}")

            # Small delay to avoid overwhelming server
            if i % 10 == 0:
                time.sleep(0.01)

        # Wait for listener to complete
        listener_thread.join(timeout=10)

    def test_read_messages(self, num_messages):
        """Test reading non-instant messages"""
        if len(self.users) < 2:
            print("Need at least 2 users for message reading test")
            return

        sender = self.users[2] if len(self.users) > 2 else self.users[0]
        receiver = self.users[3] if len(self.users) > 3 else self.users[1]

        # First logout the receiver so messages won't be instant
        start_time = time.time()
        try:
            logout_data = receiver
            request_size = len(logout_data) + 2  # +2 for the "LO" prefix
            logout_response = self.clients[receiver].send_receive("LO", logout_data)
            end_time = time.time()

            response_size = len(logout_response)
            total_size = request_size + response_size

            # Check for success - response will start with "LOT" for success
            status = 'success' if logout_response.startswith("LOT") else 'failure'
            self.metrics.record('logout', start_time, end_time, total_size, status, receiver)

            if status != 'success':
                print(f"Failed to logout user {receiver}: {logout_response}")
                return
        except Exception as e:
            end_time = time.time()
            self.metrics.record('logout', start_time, end_time, 0, 'error', str(e))
            print(f"Error logging out user {receiver}: {str(e)}")
            return

        # Send messages to offline user
        print(f"\nSending {num_messages} messages to offline user {receiver}")
        for i in range(num_messages):
            message_content = generate_message(100)  # 100 byte messages
            timestamp = datetime.datetime.now().isoformat()

            start_time = time.time()
            try:
                send_data = f"{sender} {receiver} {timestamp} {message_content}"
                request_size = len(send_data) + 2  # +2 for the "SE" prefix
                send_response = self.clients[sender].send_receive("SE", send_data)
                end_time = time.time()

                response_size = len(send_response)
                total_size = request_size + response_size

                # Check for success
                status = 'success' if send_response.startswith("SET") else 'failure'
                self.metrics.record('send_offline_message', start_time, end_time, total_size, status, f"index={i}")
            except Exception as e:
                end_time = time.time()
                self.metrics.record('send_offline_message', start_time, end_time, 0, 'error', str(e))
                print(f"Error sending offline message {i}: {str(e)}")

        # Login the receiver again
        start_time = time.time()
        try:
            # Need to reconnect the receiver
            if receiver in self.clients:
                self.clients[receiver].close()

            client = WireSocketClient(self.host, self.port)
            if not client.connect():
                print(f"Failed to connect for login of user {receiver}")
                return

            self.clients[receiver] = client

            login_data = f"{receiver} test_password"
            request_size = len(login_data) + 2  # +2 for the "LI" prefix
            login_response = self.clients[receiver].send_receive("LI", login_data)
            end_time = time.time()

            response_size = len(login_response)
            total_size = request_size + response_size

            # Check for success
            status = 'success' if login_response.startswith("LIT") else 'failure'
            self.metrics.record('login', start_time, end_time, total_size, status, receiver)

            if status != 'success':
                print(f"Failed to login user {receiver}: {login_response}")
                return
        except Exception as e:
            end_time = time.time()
            self.metrics.record('login', start_time, end_time, 0, 'error', str(e))
            print(f"Error logging in user {receiver}: {str(e)}")
            return

        # Read messages
        start_time = time.time()
        try:
            read_data = f"{receiver} {num_messages}"
            request_size = len(read_data) + 2  # +2 for the "RE" prefix
            read_response = self.clients[receiver].send_receive("RE", read_data)
            end_time = time.time()

            response_size = len(read_response)
            total_size = request_size + response_size

            # Extract number of messages read from response
            # RET{num_read} format
            status = 'success' if read_response.startswith("RET") else 'failure'
            messages_read = 0
            if status == 'success' and len(read_response) > 3:
                try:
                    # Try to extract the number of messages read
                    remaining = read_response[3:]
                    if " " in remaining:
                        messages_read = int(remaining.split(" ")[0])
                    else:
                        messages_read = int(remaining)
                except:
                    pass

            self.metrics.record('read_messages', start_time, end_time, total_size, status,
                               f"messages_read={messages_read}")

            print(f"Read {messages_read} offline messages")
        except Exception as e:
            end_time = time.time()
            self.metrics.record('read_messages', start_time, end_time, 0, 'error', str(e))
            print(f"Error reading messages: {str(e)}")

    def cleanup(self):
        """Clean up created test users"""
        for username in self.users:
            if username in self.clients and self.clients[username]:
                start_time = time.time()
                try:
                    request_data = username
                    request_size = len(request_data) + 2  # +2 for the "DA" prefix
                    response = self.clients[username].send_receive("DA", request_data)
                    end_time = time.time()

                    response_size = len(response)
                    total_size = request_size + response_size

                    # Check for success
                    status = 'success' if response.startswith("DAT") else 'failure'
                    self.metrics.record('delete_account', start_time, end_time, total_size, status, username)

                    if status == 'success':
                        print(f"Deleted user: {username}")
                    else:
                        print(f"Failed to delete user {username}: {response}")
                except Exception as e:
                    end_time = time.time()
                    self.metrics.record('delete_account', start_time, end_time, 0, 'error', str(e))
                    print(f"Error deleting user {username}: {str(e)}")

                # Close the connection
                self.clients[username].close()

        self.users = []
        self.clients = {}

    def run_experiment(self, message_sizes, num_messages, num_users, output_file):
        """Run the full experiment"""
        try:
            print(f"Starting experiment with {num_users} users, testing {len(message_sizes)} message sizes")
            print(f"Each size will send {num_messages} messages")

            # Setup phase
            self.setup_users(num_users)
            self.login_users()

            # Message delivery tests for different sizes
            for size in message_sizes:
                self.measure_message_delivery(size, num_messages)

            # Test reading offline messages
            self.test_read_messages(num_messages)

            # Generate report
            self.metrics.print_summary()
            self.metrics.save_to_csv(output_file)

        finally:
            # Always try to clean up
            print("\nCleaning up test users...")
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Measure Wire Protocol messaging server performance')
    parser.add_argument('--host', default=SERVER_HOST, help='Server host (default: from .env or localhost)')
    parser.add_argument('--port', type=int, default=SERVER_PORT, help='Server port (default: from .env or 5002)')
    parser.add_argument('--messages', type=int, default=NUM_MESSAGES, help='Number of messages per test')
    parser.add_argument('--users', type=int, default=NUM_USERS, help='Number of test users to create')
    parser.add_argument('--output', default='wire_server_metrics.csv', help='Output CSV file for metrics')
    parser.add_argument('--sizes', type=int, nargs='+', default=MESSAGE_SIZES,
                        help='Message sizes to test in bytes (default: 10 100 1000 10000)')

    args = parser.parse_args()

    print("=== Wire Protocol Message Server Performance Experiment ===")
    print(f"Server host: {args.host}")
    print(f"Server port: {args.port}")
    print(f"Number of messages per test: {args.messages}")
    print(f"Number of test users: {args.users}")
    print(f"Message sizes to test (bytes): {args.sizes}")
    print(f"Output file: {args.output}")
    print("=" * 55)

    experiment = WireServerExperiment(args.host, args.port)
    experiment.run_experiment(args.sizes, args.messages, args.users, args.output)


if __name__ == "__main__":
    main()