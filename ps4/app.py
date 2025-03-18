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
import message_server_pb2
import message_server_pb2_grpc
import grpc
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
        # TODO: CHANGE BACK
        self.host = os.environ.get("HOST_SERVER_TESTING")
        self.port = int(os.environ.get("PORT_SERVER_TESTING"))


        self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")
        # stub for server communication
        self.connection = message_server_pb2_grpc.MessageServerStub(self.channel)

        # Setup UI container
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Connect to server and start read thread
        threading.Thread(target=self.connect_to_server, daemon=True).start()

        self.frames = {}
        self.show_frame(Onboarding)

    def run(self):
        self.mainloop()


    def reset_state(self):
        # reset state variables when users log out
        self.current_user = None
        self.messages = []
        self.is_logged_in = False

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

    def connect_to_server(self):
        print(f"Client attempting to connect to HOST={self.host}, PORT={self.port}")

        while not self.is_connected:
            try:
                # https://stackoverflow.com/questions/45759491/how-to-know-if-a-grpc-server-is-available
                grpc.channel_ready_future(self.channel).result(timeout=10)
                self.is_connected = True
                print("Connected to server via gRPC.")
                # If you use streaming RPCs for reading, start a thread here:
                return True
            except grpc.FutureTimeoutError:
                print("Server not available yet, retrying...")
                time.sleep(1)
            except Exception as e:
                print(f"Failed to connect to server: {e}")
                time.sleep(1)


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


    # leave to navigation page
    def leave_to_navigation(self):
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

        hashed_password = self.enhash(password)
        request = message_server_pb2.LoginRequest(
                username=username, password=hashed_password
                )

        response = self.controller.connection.LoginAccount(request)

        if response.success:
            self.controller.current_user = username
            self.controller.is_logged_in = True
            self.leave_to_navigation()
        else:
            messagebox.showerror("Error", response.errorMessage)

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
        request = message_server_pb2.CreateRequest(
            username=username, password=hashed_password
        )
        response = self.controller.connection.CreateAccount(request)

        if response.success:
            self.controller.current_user = username
            self.controller.is_logged_in = True
            self.leave_to_navigation()
        else:
            messagebox.showerror("Error", response.errorMessage)


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
        request = message_server_pb2.DeleteAccountRequest(
            username=self.controller.current_user,
        )
        response = self.controller.connection.DeleteAccount(request)

        if response.success:
            self.controller.reset_state()
            self.controller.show_frame(Onboarding)
        else:
            messagebox.showerror("Error", response.errorMessage)


    # Logout by sending message to server as well as updating the state
    def handle_logout(self):
        request = message_server_pb2.LogoutRequest(username=self.controller.current_user)
        response = self.controller.connection.LogoutAccount(request)

        if response.success:
            self.controller.reset_state()
            self.controller.show_frame(Onboarding)
        else:
            messagebox.showerror("Error", response.errorMessage)

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

    #
    def back_to_navigation(self):
        self.controller.show_frame(Navigation)


    # Handle sending messages
    def on_button_click(self):
        username = self.username_textbox.get()
        message = self.entry_textbox.get()

        if not username or not message:
            self.status_label.config(text="Please fill in both username and message.", fg="red")
            return

        timestamp = str(datetime.now()).replace(" ", "")
        request = message_server_pb2.SendMessageRequest(
            fromUser=self.controller.current_user,
            toUser=username,
            time=timestamp,
            message=message
        )
        response = self.controller.connection.SendMessage(request)
        if response.success:
            self.status_label.config(text="Message sent successfully", fg="green")
        else:
            self.status_label.config(text=response.errorMessage, fg="red")

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

        threading.Thread(target=self.poll_messages, daemon=True).start()


        request = message_server_pb2.ReadMessagesRequest(
            username=self.controller.current_user,
            numMessages=self.number_of_messages
        )
        response = self.controller.connection.ReadMessages(request)
        if response.success:
            for msg in response.messages:
                message = {
                    "fromUser": msg.fromUser,
                    "time": msg.time,
                    "message": msg.message,
                    "messageId": msg.messageId
                }
                self.controller.messages.append(message)
        else:
            messagebox.showerror("Error", response.errorMessage)
        self._setup_ui()


    def poll_messages(self):
        # First check if user is logged in
        if not self.controller.current_user or not self.controller.is_logged_in:
            self.after_id = self.after(500, self.poll_messages)
            return

        try:
            request = message_server_pb2.InstantaneousMessagesRequest(
                username=self.controller.current_user)
            response = self.controller.connection.GetInstantaneousMessages(request)
            print("poll message", response)
            if response.success:
                if response.numRead > 0:
                    for msg in response.messages:
                        message = {
                            "fromUser": msg.fromUser,
                            "time": msg.time,
                            "message": msg.message,
                            "messageId": msg.messageId
                        }
                        self.controller.messages.append(message)
                    # Refresh the display
            self.refresh_display()

        except Exception as e:
            print(f"Error in poll_messages: {e}")

        self.after_id = self.after(500, self.poll_messages)

    def back_to_navigation(self):
        self.after_cancel(self.after_id)
        self.controller.show_frame(Navigation)

    def _setup_ui(self):
        """Setup all UI elements for the message display page"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top buttons
        # no longer needed to cleanup
        self.back_button = ttk.Button(
            self, text="Back to Navigation",
            command=self.back_to_navigation
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
        self.refresh_display()

    def _format_message(self, msg):
        """Format a message dictionary into display string"""
        return f"From: {msg['fromUser']}: {msg['message']} \n\n At: {msg['time']}"

    def refresh_display(self):
        """Update the message list display while preserving selection and scroll"""
        if not self.controller.current_user or not self.controller.is_logged_in:
            return

        # Save current view state
        current_selection = self.message_list.curselection()
        current_scroll = self.message_list.yview()

        # Update display
        self.message_list.delete(0, tk.END)

        request = message_server_pb2.ReadMessagesRequest(
            username=self.controller.current_user,
            numMessages=self.number_of_messages
        )

        response = self.controller.connection.ReadMessages(request)

        if response.success:
            if response.numRead > 0:
                for msg in response.messages:
                    message = {
                        "fromUser": msg.fromUser,
                        "time": msg.time,
                        "message": msg.message,
                        "messageId": msg.messageId
                    }
                    self.controller.messages.append(message)
        else:
            messagebox.showerror("Error", response.errorMessage)
            return

        # Now display the messages
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


        request = message_server_pb2.DeleteMessagesRequest(
            username=self.controller.current_user,
            messageId=message_id
        )
        response = self.controller.connection.DeleteMessages(request)

        if not response.success:
            messagebox.showerror("Error", response.errorMessage)
        else:
            self.controller.messages.pop(selection)
            self.refresh_display()

class SearchAccount(tk.Frame):
    # todo fix this shit
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.accounts = self.controller.accounts

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
        self.controller.show_frame(Navigation)

    def update_accounts(self):
        request = message_server_pb2.ListAccountsRequest()
        response = self.controller.connection.ListAccounts(request)

        if response.success:
            self.controller.accounts = list(response.accounts)

        self.display_accounts()

    def display_accounts(self, filter_text=None):
        # Always display if we have a filter_text, regardless of whether accounts changed
        if not filter_text and self.controller.accounts == self.accounts:
            return
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
