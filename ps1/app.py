import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import socket
import time
import os
from dotenv import load_dotenv
import json

load_dotenv()

class App(tk.Tk):
    """
    Main class for the chat app. Handles all UI and server communication.


    Attributes:
    - current_user (str): The username of the currently logged in user.
    - messages (list): A list of dictionaries representing messages.
    - accounts (list): A list of usernames.
    - socket (socket): The socket object for server communication.
    - is_logged_in (bool): Whether the user is logged in.
    - is_connected (bool): Whether the client is connected to the server.
    - number_of_messages (int): The number of messages to display.
    - host (str): The host address of the server.
    - port (int): The port number of the server.
    - is_json (bool): Whether to use JSON or wire protocol for communication.

    """
    def __init__(self):
        super().__init__()
        self.title("Chat App")
        self.geometry("800x600")

        # State variables
        self.current_user = None
        self.messages = []
        self.accounts = []
        self.socket = None
        self.is_logged_in = False
        self.is_connected = False
        self.number_of_messages = 5
        self.host = os.environ.get("HOST_SERVER")
        self.port = int(os.environ.get("PORT_SERVER"))
        self.is_json = True

        # Setup UI container
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Connect to server and start read thread
        threading.Thread(target=self.connect_to_server, daemon=True).start()

        self.frames = {}
        self.show_frame(Onboarding)


    # CLIENT STATE MANAGEMENT FUNCTIONS

    def run(self):
        self.mainloop()


    def reset_state(self):
        # reset state variables when users log out
        self.current_user = None
        self.messages = []

    def show_frame(self, page):
        """Shows frames of a selected page

        Args:
            page (tk.Frame): Selected frame to show
        Notes:
            - Destroys current frame and creates new frame
        """
        # Get current frame and stop its functions
        current_frame = list(self.frames.values())[0] if self.frames else None
        if current_frame:
            current_frame.destroy()

        # Create new frame
        frame = page(self.container, self)
        self.frames = {page: frame}
        frame.grid(row=0, column=0, sticky="nsew")


    # SERVER COMMUNICATION

    def connect_to_server(self):
        while not self.is_connected:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.is_connected = True
                print("Connected to server.")
                # Once connected, start read thread
                self.after(500, lambda : threading.Thread(target=self.read_from_server, daemon=True).start() )

                return True
            except Exception as e:
                print(f"Failed to connect to server: {e}")
                time.sleep(5)

    #
    def read_from_server(self):
        if self.is_json:
            self.read_from_server_json()
        else:
            self.read_from_server_wp()


    def write_to_server(self, message):
        if self.is_json:
            return self.write_to_server_json(message)
        else:
            return self.write_to_server_wp(message)


    def read_from_server_wp(self):
        """Reads messages from the server using wire protocol
        Notes:
            - Reads messages from the server and calls handle_reads_wp to process them accordingly
        """
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
                self.handle_reads(message[:num_bytes])

            except Exception as e:
                print("Error reading from server:", e)
                self.is_connected = False
                self.after(300, lambda :threading.Thread(target=self.connect_to_server, daemon=True).start())
                break


    # functions to handle reads for wire protocol and json
    def handle_reads(self, server_message):
        if self.is_json:
            self.handle_reads_json(server_message)
        else:
            self.handle_reads_wp(server_message)


    def handle_reads_wp(self, server_message):
        """Handles messages received from the server by processing them by our designated message types

        Example: Server sends a message with type "SET" to indicate a successful message send
        Server sends a sucessful login message with type "LIT", so user should be logged in, updating self.is_logged_in to True
        Args:
            server_message (string): A string containing the message from the server, with bytes to read as a prefix,
            then a "type" key to indicate the type of message which is always a 3 letter code,
            followed by whatever message the server wants to send to the client
        Notes:
            "SET" - Message sent successfully
            "SEL" - Message received from another user while logged in
            "LIT" - Login successful
            "LOT" - Logout successful
            "LAT" - List of accounts
            "RET" - Retrieve messages
            "DMT" - Delete message
        """
        request_type = server_message[:3]
        data = server_message[3:]

        match request_type:
            case "CRT":
                pass
            case "SEL":
                parts = data.split(" ")
                message_id = parts[0]
                sender = parts[1]
                timestamp = parts[2]
                message_content = " ".join(parts[4:])
                self.messages.append({
                    "messageId": message_id,
                    "sender": sender,
                    "timestamp": timestamp,
                    "message": message_content
                })
                # Update UI if MessageDisplay is current frame
                current_frame = list(self.frames.values())[0] if self.frames else None
                if current_frame and isinstance(current_frame, MessageDisplay):
                    current_frame.after(0, current_frame.refresh_display)

            case "LIT":
                self.is_logged_in = True
            case "LOT":
                self.is_logged_in = False
                self.reset_state()
            case "LAT":
                self.accounts = data.split(" ")
            case "RET":
                parts = data.split(" ")
                num_read = int(parts[0])

                if num_read == 0:
                    return

                new_messages = []
                index = 1

                for _ in range(num_read):
                    message_id = parts[index]
                    sender = parts[index + 1]
                    timestamp = parts[index + 2]
                    message_length = int(parts[index + 3])
                    message_content = " ".join(parts[index + 4 : index + 4 + message_length])
                    index += 4 + message_length

                    new_messages.append({
                        "messageId": message_id,
                        "sender": sender,
                        "timestamp": timestamp,
                        "message": message_content
                    })

                if new_messages:
                    self.messages = new_messages
                    # Update UI if MessageDisplay is current frame
                    current_frame = list(self.frames.values())[0] if self.frames else None
                    if current_frame and isinstance(current_frame, MessageDisplay):
                        current_frame.after(0, current_frame.refresh_display)

            case "SET":
                pass
            case "DMT":
                current_frame = list(self.frames.values())[0] if self.frames else None
                if current_frame and isinstance(current_frame, MessageDisplay):
                    current_frame.after(0, current_frame.refresh_display)
            case "ER0":
                pass
            case "ER1":
                self.logged_in = False
                self.reset_state()
                print("some error", data)
            case "ER2":
                self.logged_in = False
                self.reset_state()
                print("ER2: incorrect password", data)
            case "ER3":
                print("failed to delete message", data)
            case "DAT":
                self.logged_in = False
                self.reset_state()
                pass
            case _:
                print(server_message)


    #
    def write_to_server_wp(self, message):
        """Writes messages to the server using json

        Args:
            message_dict (string): Contains a message to send to the server

        Returns:
            boolean: True or false depending on if the message was sent successfully
        """
        if not self.is_connected:
            print("Not connected to server")
            return False
        try:
            return_data = str(len(message)) + message
            self.socket.sendall(return_data.encode('utf-8'))
            print(f"Sent: {message}")
            return True
        except Exception as e:
            print("Failed to write to the server.")
            print(e)
            return False

    def write_to_server_json(self, message_dict):
        """Writes messages to the server using json

        Args:
            message_dict (dict): Contains a json message to send to the server

        Returns:
            boolean: True or false depending on if the message was sent successfully
        """
        if not self.is_connected:
            print("Not connected to server")
            return False
        try:
            json_message = json.dumps(message_dict)
            return_data = str(len(json_message)) + json_message
            self.socket.sendall(return_data.encode('utf-8'))
            return True
        except Exception as e:
            print("Failed to write to server:", e)
            return False

    def read_from_server_json(self):
        """Reads messages from the server using json
        Notes:
            - Reads messages from the server, processing the bytes
            and calls handle_reads_json to process them accordingly
        """
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

                while (cur_bytes < num_bytes):
                    data = self.socket.recv(num_bytes - cur_bytes)
                    if not data:
                        self.is_connected = False
                        break
                    ret_data += data
                    cur_bytes += len(data.decode("utf-8"))

                message = ret_data.decode('utf-8')
                json_data = json.loads(message)
                self.handle_reads_json(json_data)

            except Exception as e:
                print("Error reading from server:", e)
                self.after(300, lambda :threading.Thread(target=self.connect_to_server, daemon=True).start())
                self.is_connected = False
                break

    def handle_reads_json(self, json_data):
        """Handles messages received from the server by processing them by our designated message types

        Example: Server sends a message with type "SET" to indicate a successful message send
        Server sends a sucessful login message with type "LIT", so user should be logged in, updating self.is_logged_in to True
        Args:
            json_data (dict): A dictionary containing the message from the server,
            always containing a "type" key to indicate the type of message,
            success messages contain a boolean whether what ever action was successful or not
            and whatever message the server wants to send to the client
        Notes:
            "SET" - Message sent successfully
            "SEL" - Message received from another user while logged in
            "LIT" - Login successful
            "LOT" - Logout successful
            "LAT" - List of accounts
            "RET" - Retrieve messages
            "DMT" - Delete message
        """
        request_type = json_data.get("type", "")
        match request_type:
            case "SET":
                print("Sending message success")
            case "SEL":
                self.messages.append({
                    "messageId": json_data["messageId"],
                    "sender": json_data["sender"],
                    "timestamp": json_data["timestamp"],
                    "message": json_data["message"]
                })
                # Update UI if MessageDisplay is current frame
                current_frame = list(self.frames.values())[0] if self.frames else None
                if current_frame and isinstance(current_frame, MessageDisplay):
                    current_frame.after(0, current_frame.refresh_display)

            case "LIT":
                self.is_logged_in = True
                print("Login successful")
            case "LOT":
                self.is_logged_in = False
                self.reset_state()
            case "LAT":
                self.accounts = json_data.get("accounts", [])
            case "RET":
                messages = json_data.get("messages", [])
                new_messages = []
                for msg in messages:
                    new_messages.append({
                        "messageId": msg["messageId"],
                        "sender": msg["sender"],
                        "timestamp": msg["timestamp"],
                        "message": msg["message"]
                    })
                if new_messages:
                    self.messages = new_messages
                    # Update UI if MessageDisplay is current frame
                    current_frame = list(self.frames.values())[0] if self.frames else None
                    if current_frame and isinstance(current_frame, MessageDisplay):
                        current_frame.after(0, current_frame.refresh_display)

            case "DMT":
                current_frame = list(self.frames.values())[0] if self.frames else None
                if current_frame and isinstance(current_frame, MessageDisplay):
                    current_frame.after(0, current_frame.refresh_display)

            case _:
                print("Unknown message type:", request_type)


class Onboarding(tk.Frame):
    """Class for the login/signup page

    Args:
        tk (tk.Frame):
    Atributes:
        - parent: The parent Tk.frame that called the frame
        - controller: The controller object that is used to control the app
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.label = tk.Label(self, text="Sign in")

        self.label_username = tk.Label(self, text='Username')
        self.label_username.grid(row=0)

        self.label_password = tk.Label(self, text='Password')
        self.label_password.grid(row=1)

        self.textbox_username = tk.Entry(self)
        self.textbox_username.grid(row=0, column=1)

        self.textbox_password = tk.Entry(self)
        self.textbox_password.grid(row=1, column=1)

        self.button_login = tk.Button(self, text="Login", command=self.handle_login)
        self.button_login.grid(row=2, column=1)
        self.button_create_account = tk.Button(self, text="Create Account", command=self.handle_create_account)
        self.button_create_account.grid(row=2, column=2)

        self.update_accounts()


    # updates accounts on login page to ensure that users are updated correctly
    def update_accounts(self):
        if self.controller.is_json:
            self.controller.write_to_server_json({"type": "LA"})
        else:
            self.controller.write_to_server("LA")
        self.after_id = self.after(1000, self.update_accounts)

    # cleanup function to cancel any pending after calls
    def cleanup(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    # leave to navigation page
    def leave_to_navigation(self):
        self.cleanup()
        self.controller.show_frame(Navigation)

    # gpt hash function
    def enhash(self, password):
        # Takes in password, outputs hashed password
        # Simple shift of ASCII values and reversal
        shifted = ''.join(chr((ord(c) + 5) % 128) for c in password)
        return shifted[::-1]



    def handle_login(self):
        """Handles the login process for the user
        Notes:
            - Checks if the username and password are valid
            - If they are, the user is logged in and taken to the navigation page
        """
        username = self.textbox_username.get()
        password = self.textbox_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        if ' ' in username or ' ' in password:
            messagebox.showerror("Error", "Username and password cannot contain spaces")
            return

        if username in self.controller.accounts:
            hashed_password = self.enhash(password)
            if self.controller.is_json:
                return_value = {
                    "type": "LI",
                    "username": username,
                    "password": hashed_password
                }
            else:
                return_value = "LI" + username + " " + hashed_password
            if self.controller.write_to_server(return_value):
                self.cleanup()
                self.controller.current_user = username
                self.after(500, self.check_login_success)
            else:
                messagebox.showerror("Error", "Login failed. Please try again.")
        else:
            messagebox.showerror("Error", "Account does not exist.")

    # checks if login was successful
    def check_login_success(self):
        # Check the controller's is_logged_in variable
        if self.controller.is_logged_in is False:
            messagebox.showerror("Error", "Login failed. Please try again.")
        else:
            self.controller.current_user = self.textbox_username.get()
            self.textbox_username.delete(0, tk.END)
            self.textbox_password.delete(0, tk.END)
            self.leave_to_navigation()


    def handle_create_account(self):
        """ Handles the account creation process for the user
        Notes:
            - Checks if the username and password are valid
            - If they are, the user is created and logged in and taken to the navigation page
        """
        username = self.textbox_username.get()
        password = self.textbox_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        if ' ' in username or ' ' in password:
            messagebox.showerror("Error", "Username and password cannot contain spaces")
            return
        if username in self.controller.accounts:
            messagebox.showerror("Error", "Account already exists.")
            return

        hashed_password = self.enhash(password)
        if self.controller.is_json:
            return_value = {
                "type": "CR",
                "username": username,
                "password": hashed_password
            }
        else:
            return_value = "CR" + username + " " + hashed_password
        if self.controller.write_to_server(return_value):
            # Store these for after we get CRT response
            self.pending_username = username
            self.pending_password = hashed_password
            self.after(100, self.complete_account_creation)

    def complete_account_creation(self):
        # Only proceed with login if we got CRT confirmation
        if self.pending_username and self.pending_password:
            if self.controller.is_json:
                login_value = {
                    "type": "LI",
                    "username": self.pending_username,
                    "password": self.pending_password
                }
            else:
                login_value = "LI" + self.pending_username + " " + self.pending_password
            self.controller.current_user = self.pending_username
            if self.controller.write_to_server(login_value):
                self.after(200, self.check_login_success)


class Navigation(tk.Frame):
    """
    Navigation page for the chat app

    Notes:
    - Contains buttons to navigate to different pages of the app
    Chat, Onboarding, MessageDisplay, and SearchAccount
    - Also contains buttons to logout and delete account

    Args:
        tk (tk.Frame): The parent Tk.frame that called the frame

    Attributes:
        - parent: The parent Tk.frame that called the frame
        - controller: The controller object that is used to control the app
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        title_label = tk.Label(self, text="Navigation page", font=("Arial", 24))
        title_label.pack(pady=20)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        self.send_messages_btn = tk.Button(
            button_frame,
            text="Send Messages",
            command=lambda: controller.show_frame(Chat),
            width=20,
            height=2
        )
        self.send_messages_btn.pack(pady=10)

        self.read_messages_btn = tk.Button(
            button_frame,
            text="Read Messages",
            command=lambda: controller.show_frame(MessageDisplay),
            width=20,
            height=2
        )
        self.read_messages_btn.pack(pady=10)

        self.search_account = tk.Button(
            button_frame,
            text="Search Accounts",
            command=lambda: controller.show_frame(SearchAccount),
            width=20,
            height=2
        )
        self.search_account.pack(pady=10)

        self.logout_btn = tk.Button(
            self,
            text="Logout",
            command=self.handle_logout,
            width=10
        )
        self.logout_btn.pack(pady=20)

        self.delete_account_btn = tk.Button(
            self,
            text="Delete Account",
            command=self.on_delete_account,
            width=10
        )
        self.delete_account_btn.pack(pady=20)

    # Delete account by sending message to server as well as updating the state
    def on_delete_account(self):
        if self.controller.is_json:
            message_to_write = {
                "type": "DA",
                "username": self.controller.current_user
            }
        else:
            message_to_write = "DA" + self.controller.current_user
        if self.controller.write_to_server(message_to_write):
            self.controller.reset_state()
            self.controller.show_frame(Onboarding)


    # Logout by sending message to server as well as updating the state
    def handle_logout(self):
        if self.controller.is_json:
            message_to_write = {
                "type": "LO",
                "username": self.controller.current_user
            }
        else:
            message_to_write = "LO" + self.controller.current_user
        if self.controller.write_to_server(message_to_write):
            self.controller.reset_state()
            self.controller.is_logged_in = False
            self.controller.show_frame(Onboarding)

class Chat(tk.Frame):
    """
    Frame for sending messages to other users

    Notes:
    - Contains a search bar to search for users to send messages to
    - Contains a text box to enter messages, and a button to send on click

    Args:
        tk (tk.Frame): The parent Tk.frame that called the frame

    Attributes:
        - parent: The parent Tk.frame that called the frame
        - controller: The controller object that is used to control the app
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.grid_columnconfigure(1, weight=1)

        # UI setup
        self.back_button = tk.Button(
            self,
            text="Back to Navigation",
            command=self.back_to_navigation
        )
        self.back_button.grid(row=0, column=0, columnspan=3, pady=(10,20), sticky="w", padx=10)


        self.label = tk.Label(self, text="Enter username to send to:")
        self.label.grid(row=1, column=0, padx=10, pady=5)

        self.username_textbox = tk.Entry(self)
        self.username_textbox.grid(row=1, column=1, sticky="ew", padx=10)


        self.label_entry = tk.Label(self, text="Enter message:")
        self.label_entry.grid(row=2, column=0, padx=10, pady=5)

        self.entry_textbox = tk.Entry(self)
        self.entry_textbox.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        self.button = tk.Button(self, text="Send", command=self.on_button_click)
        self.button.grid(row=2, column=2, padx=10)

        self.status_label = tk.Label(self, text="")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)

        self.update_accounts()

    #
    def back_to_navigation(self):
        self.after_cancel(self.after_id)
        self.controller.show_frame(Navigation)

    # update accounts to ensure that the user is up to date
    def update_accounts(self):
        if self.controller.is_json:
            self.controller.write_to_server_json({"type": "LA"})
        else:
            self.controller.write_to_server("LA")
        self.after_id = self.after(500, self.update_accounts)


    # Handle sending messages
    def on_button_click(self):
        username = self.username_textbox.get()
        message = self.entry_textbox.get()

        if not username or not message:
            self.status_label.config(text="Please fill in both username and message.", fg="red")
            return

        if username not in self.controller.accounts:
            self.status_label.config(text="Failed to send message.", fg="red")
            return

        timestamp = str(datetime.now()).replace(" ", "")
        if self.controller.is_json:
            send_value = {
                "type": "SE",
                "from_username": self.controller.current_user,
                "to_username": username,
                "timestamp": timestamp,
                "message": message
            }
        else:
            send_value = f"SE{self.controller.current_user} {username} {timestamp} {message}"

        if self.controller.write_to_server(send_value):
            self.status_label.config(text="Message sent successfully!", fg="green")
            self.entry_textbox.delete(0, tk.END)
            self.username_textbox.delete(0, tk.END)
        else:
            self.status_label.config(text="Failed to send message.", fg="red")

class MessageDisplay(tk.Frame):
    """
    Page to display messages received frame

    Notes:
    - Contains a search bar to search for users to send messages to
    - Contains a text box to enter messages, and a button to send on click

    Args:
        tk (tk.Frame): The parent Tk.frame that called the frame

    Attributes:
        - parent: The parent Tk.frame that called the frame
        - controller: The controller object that is used to control the app
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.number_of_messages = 10


        if self.controller.is_json:
            message = {
            "type": "RE",
            "username": self.controller.current_user,
            "number": self.number_of_messages,
            }
        else:
            message = f"RE{self.controller.current_user} {str(self.number_of_messages)}"
        self.controller.write_to_server(message)
        self._setup_ui()
        self.refresh_display()

    def _setup_ui(self):
        """Setup all UI elements for the message display page"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top buttons
        # no longer needed to cleanup
        self.back_button = ttk.Button(
            self, text="Back to Navigation",
            command=lambda: self.controller.show_frame(Navigation)
        )
        self.delete_button = ttk.Button(
            self, text="Delete Message",
            command=self.delete_message
        )
        self.message_count_entry = ttk.Entry(self, width=5)
        self.set_message_count_button = ttk.Button(
            self, text="Enter",
            command=self.set_message_count
        )

        # Layout top buttons
        self.back_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.delete_button.grid(row=0, column=3, sticky="w", padx=10, pady=10)
        self.message_count_entry.grid(row=0, column=4, sticky="e", padx=10, pady=10)
        self.set_message_count_button.grid(row=0, column=5, sticky="e", padx=10, pady=10)

        # Message display area
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.message_list = tk.Listbox(self.paned)
        self.message_list.bind('<<ListboxSelect>>', self.display_message)

        self.message_content = tk.Text(self.paned, wrap=tk.WORD)
        self.message_content.config(state='disabled')

        self.paned.add(self.message_list)
        self.paned.add(self.message_content)

    def _format_message(self, msg):
        """Format a message dictionary into display string"""
        return f"From: {msg['sender']}: {msg['message']} \n\n At: {msg['timestamp']}"

    def refresh_display(self):
        """Update the message list display while preserving selection and scroll"""
        if not self.controller.current_user or not self.controller.is_logged_in:
            return

        # Save current view state
        current_selection = self.message_list.curselection()
        current_scroll = self.message_list.yview()

        # Update display
        self.message_list.delete(0, tk.END)
        for msg in self.controller.messages[:self.number_of_messages]:
            self.message_list.insert(tk.END, self._format_message(msg))

        # Restore view state
        if current_selection:
            self.message_list.selection_set(current_selection)
        self.message_list.yview_moveto(current_scroll[0])

    def set_message_count(self):
        """Handle message count change"""
        try:
            new_count = self.message_count_entry.get()
            if not new_count or not new_count.isdigit():
                print("Invalid input:", new_count)
                return

            self.number_of_messages = int(new_count)
            self.refresh_display()

        except ValueError as e:
            print("Error:", e)
            messagebox.showerror("Error", "Please select a number")

    def display_message(self, event):
        """Show selected message in detail view"""
        if not self.message_list.curselection():
            return

        selection = self.message_list.curselection()[0]
        message_dict = self.controller.messages[selection]
        formatted_message = self._format_message(message_dict)

        self.message_content.config(state='normal')
        self.message_content.delete(1.0, tk.END)
        self.message_content.insert(1.0, formatted_message)
        self.message_content.config(state='disabled')

    def delete_message(self):
        """Delete selected message"""
        if not self.message_list.curselection():
            return

        selection = self.message_list.curselection()[0]
        message_id = self.controller.messages[selection]["messageId"]
        self.controller.messages.pop(selection)
        if self.controller.is_json:
            message = {
                "type": "DM",
                "username": self.controller.current_user,
                "id": message_id
            }
        else:
            message = f"DM{self.controller.current_user} {message_id}"

        if self.controller.write_to_server(message):
            print("Message deleted successfully")

class SearchAccount(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.accounts = self.controller.accounts
        self.is_first_display = True

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.back_button = ttk.Button(
            self,
            text="Back to Navigation",
            command=self.back_to_navigation
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.label = tk.Label(self, text="Enter username to search for:")
        self.label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.username_textbox = tk.Entry(self)
        self.username_textbox.grid(row=1, column=1, sticky="ew", padx=10)

        self.search_button = tk.Button(self, text="Search", command=self.search_account)
        self.search_button.grid(row=1, column=2, pady=5, padx=10)

        self.results_text = tk.Text(self, wrap=tk.WORD, height=10)
        self.results_text.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

        self.update_accounts()

    def back_to_navigation(self):
        self.after_cancel(self.after_id)
        self.controller.show_frame(Navigation)

    def update_accounts(self):
        if self.controller.is_json:
            self.controller.write_to_server_json({"type": "LA"})
        else:
            self.controller.write_to_server("LA")
        self.display_accounts()
        self.after_id = self.after(500, self.update_accounts)

    def display_accounts(self, filter_text=None):
        # Always display if we have a filter_text, regardless of whether accounts changed
        if not filter_text and not self.is_first_display and self.controller.accounts == self.accounts:
            return

        self.is_first_display = False
        self.accounts = self.controller.accounts.copy()
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)

        displayed_accounts = self.accounts

        if filter_text:
            displayed_accounts = [user for user in displayed_accounts if filter_text.lower() in user.lower()]

        for username in displayed_accounts:
            self.results_text.insert(tk.END, f"Username: {username}\n")

        self.results_text.config(state='disabled')

    def search_account(self):
        search_term = self.username_textbox.get()
        self.display_accounts(search_term)



if __name__ == "__main__":
    print("Hello, World!")
    app = App()
    app.run()
