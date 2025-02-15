
import socket
import time
import json
import threading
import statistics
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class LatencyTester:
    def __init__(self, host=None, port=None, is_json=True, num_iterations=100):
        """
        Initialize latency tester for server communication.
        """
        self.host = host or os.environ.get("HOST_SERVER")
        self.port = port or int(os.environ.get("PORT_SERVER"))
        self.is_json = is_json
        self.num_iterations = num_iterations
        self.socket = None
        self.is_connected = False

        # Latency tracking
        self.latencies = []
        self.send_time = None
        self.current_iteration = 0

    def enhash(self, password):
        """Simple hash function to match client-side hashing."""
        shifted = ''.join(chr((ord(c) + 5) % 128) for c in password)
        return shifted[::-1]

    def connect_to_server(self):
        """Establish a socket connection."""
        print(f"Attempting to connect to {self.host}:{self.port}")

        while not self.is_connected:
            try:
                print(f"Attempting to connect to {self.host}:{self.port}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.is_connected = True
                print("Connected to server.")

                # Start read thread
                threading.Thread(target=self.read_from_server, daemon=True).start()
                return True
            except Exception as e:
                print(f"Failed to connect to server: {e}")
                print(f"Current host: {self.host}, port: {self.port}")
                time.sleep(1)

    def read_from_server(self):
        """Reads messages from the server"""
        while self.is_connected:
            try:
                str_bytes = ""
                recv_data = self.socket.recv(1)
                while recv_data:
                    if len(recv_data.decode("utf-8")) > 0:
                        if (recv_data.decode("utf-8")).isnumeric():
                            str_bytes += recv_data.decode("utf-8")
                        else:
                            break
                    recv_data = self.socket.recv(1)

                num_bytes = int(str_bytes)
                cur_bytes = 1
                ret_data = recv_data

                if not str_bytes:
                    print("No length prefix received")
                    continue

                while (cur_bytes < num_bytes):
                    data = self.socket.recv(num_bytes - cur_bytes)
                    if not data:
                        print("Server connection closed")
                        self.is_connected = False
                        break
                    ret_data += data
                    cur_bytes += len(data.decode("utf-8"))

                message = ret_data.decode('utf-8')
                print(f"Received: {message[:num_bytes]}")

                # Calculate latency for experiment messages
                if self.send_time is not None:
                    latency = (time.time() - self.send_time) * 1000  # Convert to milliseconds
                    self.latencies.append(latency)
                    self.current_iteration += 1
                    self.send_time = None

            except Exception as e:
                print("Error reading from server:", e)

    def write_to_server(self, message):
        """Send a message to the server."""
        if not self.is_connected:
            print("Not connected to server")
            return False
        try:
            # Prepare message based on protocol
            if self.is_json:
                message_str = json.dumps(message)
            else:
                # Wire protocol message formatting
                if message['type'] == 'CR':
                    message_str = f"CR{message['username']} {message['password']}"
                elif message['type'] == 'LI':
                    message_str = f"LI{message['username']} {message['password']}"
                elif message['type'] == 'SE':
                    message_str = f"SE{message['from_username']} {message['to_username']} {message['timestamp']} {message['message']}"
                else:
                    raise ValueError(f"Unsupported message type: {message['type']}")

            # Prepare payload with length prefix
            payload = str(len(message_str.encode('utf-8'))) + message_str

            # Track send time for latency calculation
            self.send_time = time.time()

            # Send message
            self.socket.sendall(payload.encode('utf-8'))
            print(f"Sent: {payload}")
            return True
        except Exception as e:
            print(f"Failed to write to the server: {e}")
            return False

    def send_messages(self):
        """
        Send messages and measure latency.
        """
        # Connect to server
        if not self.connect_to_server():
            return {"protocol": "JSON" if self.is_json else "Wire Protocol",
                    "error": "Could not connect to server"}

        try:
            # Create Tester account
            tester_create_msg = {
                'type': 'CR',
                'username': 'Tester',
                'password': self.enhash('testerpass')
            }
            if not self.write_to_server(tester_create_msg):
                return {"error": "Failed to create Tester account"}

            # Wait for account creation
            while self.current_iteration == 0 and self.is_connected:
                time.sleep(0.1)

            # Create TestReceiver account
            receiver_create_msg = {
                'type': 'CR',
                'username': 'TestReceiver',
                'password': self.enhash('receiverpass')
            }
            if not self.write_to_server(receiver_create_msg):
                return {"error": "Failed to create TestReceiver account"}

            # Wait for account creation
            while self.current_iteration == 1 and self.is_connected:
                time.sleep(0.1)

            # Login Tester
            tester_login_msg = {
                'type': 'LI',
                'username': 'Tester',
                'password': self.enhash('testerpass')
            }
            if not self.write_to_server(tester_login_msg):
                return {"error": "Failed to login Tester"}

            # Wait for login
            while self.current_iteration == 2 and self.is_connected:
                time.sleep(0.1)

            # Send test messages
            for i in range(self.num_iterations):
                # Prepare send message
                timestamp = str(datetime.now()).replace(" ", "")
                send_msg = {
                    'type': 'SE',
                    'from_username': 'Tester',
                    'to_username': 'TestReceiver',
                    'timestamp': timestamp,
                    'message': f'Test message {i}'
                }

                # Send message
                if not self.write_to_server(send_msg):
                    break

                # Wait for response
                while self.current_iteration < i + 3 and self.is_connected:
                    time.sleep(0.1)

        except Exception as e:
            print(f"Unexpected error during testing: {e}")
            return {"error": str(e)}

        # Calculate and return statistics
        return {
            "protocol": "JSON" if self.is_json else "Wire Protocol",
            "min_latency_ms": min(self.latencies) if self.latencies else None,
            "max_latency_ms": max(self.latencies) if self.latencies else None,
            "mean_latency_ms": statistics.mean(self.latencies) if self.latencies else None,
            "median_latency_ms": statistics.median(self.latencies) if self.latencies else None,
            "iterations": len(self.latencies)
        }

def run_comprehensive_test():
    """
    Run comprehensive latency tests for both JSON and wire protocol.
    """
    print("Running Comprehensive Latency Tests...")

    # Test JSON Protocol
    print("\n--- Testing JSON Protocol ---")
    json_tester = LatencyTester(is_json=True, num_iterations=10)
    json_results = json_tester.send_messages()

    # Test Wire Protocol
    print("\n--- Testing Wire Protocol ---")
    wp_tester = LatencyTester(is_json=False, num_iterations=10)
    wp_results = wp_tester.send_messages()

    # Print Results
    print("\n--- JSON Protocol Results ---")
    for key, value in json_results.items():
        print(f"{key}: {value}")

    print("\n--- Wire Protocol Results ---")
    for key, value in wp_results.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    run_comprehensive_test()