#!/usr/bin/env python3

import grpc
import message_server_pb2
import message_server_pb2_grpc
import time
import datetime
import random
import string
import csv
import os
from dotenv import load_dotenv
import threading
import argparse
import sys

load_dotenv()

# Constants
SERVER_ADDRESS = "[::]:5001"  # Update with your server address
NUM_MESSAGES = 100  # Default number of messages to send in experiment
MESSAGE_SIZES = [10, 100, 1000, 10000]  # Message sizes in bytes to test
NUM_USERS = 5  # Number of users to create for testing

# Class to measure gRPC call duration and data size
class GrpcMetrics:
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

    def save_to_csv(self, filename="grpc_metrics.csv"):
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


# Main experiment class
class MessageServerExperiment:
    def __init__(self, server_address):
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.stub = message_server_pb2_grpc.MessageServerStub(self.channel)
        self.metrics = GrpcMetrics()
        self.users = []

    def setup_users(self, num_users):
        """Create test users for the experiment"""
        for i in range(num_users):
            username = f"test_user_{i}_{int(time.time())}"
            password = "test_password"

            start_time = time.time()
            try:
                request = message_server_pb2.CreateRequest(username=username, password=password)
                request_size = sys.getsizeof(request.SerializeToString())
                response = self.stub.CreateAccount(request)
                end_time = time.time()

                response_size = sys.getsizeof(response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if response.success else 'failure'
                self.metrics.record('create_account', start_time, end_time, total_size, status, username)

                if response.success:
                    self.users.append(username)
                    print(f"Created user: {username}")
                else:
                    print(f"Failed to create user {username}: {response.errorMessage}")
            except Exception as e:
                end_time = time.time()
                self.metrics.record('create_account', start_time, end_time, 0, 'error', str(e))
                print(f"Error creating user {username}: {str(e)}")

    def login_users(self):
        """Login all test users"""
        for username in self.users:
            start_time = time.time()
            try:
                request = message_server_pb2.LoginRequest(username=username, password="test_password")
                request_size = sys.getsizeof(request.SerializeToString())
                response = self.stub.LoginAccount(request)
                end_time = time.time()

                response_size = sys.getsizeof(response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if response.success else 'failure'
                self.metrics.record('login', start_time, end_time, total_size, status, username)

                if not response.success:
                    print(f"Failed to login user {username}: {response.errorMessage}")
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

        # Send messages
        for i in range(num_messages):
            message_content = generate_message(message_size)
            timestamp = datetime.datetime.now().isoformat()

            # Measure send time
            start_time = time.time()
            try:
                send_request = message_server_pb2.SendMessageRequest(
                    fromUser=sender,
                    toUser=receiver,
                    time=timestamp,
                    message=message_content
                )
                request_size = sys.getsizeof(send_request.SerializeToString())
                send_response = self.stub.SendMessage(send_request)
                end_time = time.time()

                response_size = sys.getsizeof(send_response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if send_response.success else 'failure'
                self.metrics.record('send_message', start_time, end_time, total_size, status,
                                   f"size={message_size}, index={i}")

                if not send_response.success:
                    print(f"Failed to send message {i}: {send_response.errorMessage}")
                    continue

            except Exception as e:
                end_time = time.time()
                self.metrics.record('send_message', start_time, end_time, 0, 'error', str(e))
                print(f"Error sending message {i}: {str(e)}")
                continue

            # Measure instant message retrieval time
            start_time = time.time()
            try:
                read_request = message_server_pb2.InstantaneousMessagesRequest(username=receiver)
                request_size = sys.getsizeof(read_request.SerializeToString())
                read_response = self.stub.GetInstantaneousMessages(read_request)
                end_time = time.time()

                response_size = sys.getsizeof(read_response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if read_response.success else 'failure'
                messages_read = read_response.numRead if hasattr(read_response, 'numRead') else 0
                self.metrics.record('receive_instant_message', start_time, end_time, total_size, status,
                                   f"messages_read={messages_read}, size={message_size}")

                if not read_response.success and i % 10 == 0:
                    print(f"Failed to read instant messages at index {i}")

            except Exception as e:
                end_time = time.time()
                self.metrics.record('receive_instant_message', start_time, end_time, 0, 'error', str(e))
                print(f"Error reading instant messages at index {i}: {str(e)}")

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
            logout_request = message_server_pb2.LogoutRequest(username=receiver)
            request_size = sys.getsizeof(logout_request.SerializeToString())
            logout_response = self.stub.LogoutAccount(logout_request)
            end_time = time.time()

            response_size = sys.getsizeof(logout_response.SerializeToString())
            total_size = request_size + response_size

            status = 'success' if logout_response.success else 'failure'
            self.metrics.record('logout', start_time, end_time, total_size, status, receiver)

            if not logout_response.success:
                print(f"Failed to logout user {receiver}: {logout_response.errorMessage}")
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
                send_request = message_server_pb2.SendMessageRequest(
                    fromUser=sender,
                    toUser=receiver,
                    time=timestamp,
                    message=message_content
                )
                request_size = sys.getsizeof(send_request.SerializeToString())
                send_response = self.stub.SendMessage(send_request)
                end_time = time.time()

                response_size = sys.getsizeof(send_response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if send_response.success else 'failure'
                self.metrics.record('send_offline_message', start_time, end_time, total_size, status, f"index={i}")
            except Exception as e:
                end_time = time.time()
                self.metrics.record('send_offline_message', start_time, end_time, 0, 'error', str(e))
                print(f"Error sending offline message {i}: {str(e)}")

        # Login the receiver again
        start_time = time.time()
        try:
            login_request = message_server_pb2.LoginRequest(username=receiver, password="test_password")
            request_size = sys.getsizeof(login_request.SerializeToString())
            login_response = self.stub.LoginAccount(login_request)
            end_time = time.time()

            response_size = sys.getsizeof(login_response.SerializeToString())
            total_size = request_size + response_size

            status = 'success' if login_response.success else 'failure'
            self.metrics.record('login', start_time, end_time, total_size, status, receiver)

            if not login_response.success:
                print(f"Failed to login user {receiver}: {login_response.errorMessage}")
                return
        except Exception as e:
            end_time = time.time()
            self.metrics.record('login', start_time, end_time, 0, 'error', str(e))
            print(f"Error logging in user {receiver}: {str(e)}")
            return

        # Read messages
        start_time = time.time()
        try:
            read_request = message_server_pb2.ReadMessagesRequest(username=receiver, numMessages=num_messages)
            request_size = sys.getsizeof(read_request.SerializeToString())
            read_response = self.stub.ReadMessages(read_request)
            end_time = time.time()

            response_size = sys.getsizeof(read_response.SerializeToString())
            total_size = request_size + response_size

            status = 'success' if read_response.success else 'failure'
            messages_read = read_response.numRead if hasattr(read_response, 'numRead') else 0
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
            start_time = time.time()
            try:
                request = message_server_pb2.DeleteAccountRequest(username=username)
                request_size = sys.getsizeof(request.SerializeToString())
                response = self.stub.DeleteAccount(request)
                end_time = time.time()

                response_size = sys.getsizeof(response.SerializeToString())
                total_size = request_size + response_size

                status = 'success' if response.success else 'failure'
                self.metrics.record('delete_account', start_time, end_time, total_size, status, username)

                if response.success:
                    print(f"Deleted user: {username}")
                else:
                    print(f"Failed to delete user {username}: {response.errorMessage}")
            except Exception as e:
                end_time = time.time()
                self.metrics.record('delete_account', start_time, end_time, 0, 'error', str(e))
                print(f"Error deleting user {username}: {str(e)}")

        self.users = []
        self.channel.close()

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
    parser = argparse.ArgumentParser(description='Measure gRPC message server performance')
    parser.add_argument('--server', default=SERVER_ADDRESS, help='Server address (default: [::]:5001)')
    parser.add_argument('--messages', type=int, default=NUM_MESSAGES, help='Number of messages per test')
    parser.add_argument('--users', type=int, default=NUM_USERS, help='Number of test users to create')
    parser.add_argument('--output', default='message_server_metrics.csv', help='Output CSV file for metrics')
    parser.add_argument('--sizes', type=int, nargs='+', default=MESSAGE_SIZES,
                        help='Message sizes to test in bytes (default: 10 100 1000 10000)')

    args = parser.parse_args()

    print("=== Message Server Performance Experiment ===")
    print(f"Server address: {args.server}")
    print(f"Number of messages per test: {args.messages}")
    print(f"Number of test users: {args.users}")
    print(f"Message sizes to test (bytes): {args.sizes}")
    print(f"Output file: {args.output}")
    print("=" * 45)

    experiment = MessageServerExperiment(args.server)
    experiment.run_experiment(args.sizes, args.messages, args.users, args.output)


if __name__ == "__main__":
    main()