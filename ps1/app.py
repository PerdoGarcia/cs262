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


class CentralState:
    def __init__(self):
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


    def reset_state(self):
        self.current_user = None
        self.messages = []

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            print("Connected to server.")
            return True
        except Exception as e:
            print("Failed to connect to server.")
            print(e)
            self.is_connected = False
            return False

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

    def handle_reads(self, server_message):
        if self.is_json:
            self.handle_reads_json(server_message)
        else:
            self.handle_reads_wp(server_message)


    def read_from_server_wp(self):
        while self.is_connected:
            try:
                str_bytes = ""
                recv_data = self.socket.recv(1)
                print("Received data:", recv_data)
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

                    # data = self.socket.recv(1024)
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
                break

    def handle_reads_wp(self, server_message):
        print("Handling reads", server_message)
        request_type = server_message[:3]
        data = server_message[3:]

        match request_type:
            case "CRT":
                pass

            case "SEL":
                print("message recieved while logged in", data)
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

            case "LIT":
                self.is_logged_in = True

                pass
            case "LOT":
                self.is_logged_in = False
                self.reset_state()
            case "LAT":
                self.accounts = data.split(" ")
            case "RET":
                parts = data.split(" ")
                num_read = int(parts[0])

                # If there are no messages to read, don't update the message list at all
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

            case "SET":
                pass
            case "DMT":
                # Delete message
                self.messages = []
                self.write_to_server("RE" + self.current_user + " " + str(self.number_of_messages))
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


    # perhaps create a thread on the client for reading
    # and create a thread on the client for writing
    def write_to_server_wp(self, message):
        print("Writing to server", message)
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


     #JSON
    def write_to_server_json(self, message_dict):
        print("Writing JSON to server:", message_dict)
        if not self.is_connected:
            print("Not connected to server")
            return False
        try:
            json_str = json.dumps(message_dict)
            full_message = f"{len(json_str)}{json_str}"
            self.socket.sendall(full_message.encode('utf-8'))
            print(f"Sent JSON: {json_str}")
            return True
        except Exception as e:
            print("Failed to write to server:", e)
            return False


    def read_from_server_json(self):
        while self.is_connected:
            try:
                # Still need to read length prefix byte by byte
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

                # Still need to read exact number of bytes
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
                self.is_connected = False
                break


    def handle_reads_json(self, json_data):
        print("Handling JSON:", json_data)

        # Check for error first
        if not json_data.get("success", False):
            print("Server Error:", json_data.get("errorMsg"))
            return

        request_type = json_data.get("type", "")
        print("Request type:", request_type)
        match request_type:
            case "SEL":  # Received message
                self.messages.append({
                    "messageId": json_data["messageId"],
                    "sender": json_data["sender"],
                    "timestamp": json_data["timestamp"],
                    "message": json_data["message"]
                })

            case "LIT":  # Login success
                self.is_logged_in = True

                print("Login successful")

            case "LOT":  # Logout success
                self.is_logged_in = False
                self.reset_state()

            case "LAT":  # List accounts
                self.accounts = json_data.get("accounts", [])

            case "RET":  # Read messages
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

            case "DMT":  # Delete message success
                self.messages = []
                self.write_to_server_json({
                    "type": "RE",
                    "username": self.current_user,
                    "number": self.number_of_messages
                })

            case "ER0":
                pass
            case "ER1":
                self.logged_in = False
                self.reset_state()
                print("some error", )
            case "ER2":
                self.logged_in = False
                self.reset_state()
                print("Acount is already in database or does not exist")
            case "ER3":
                print("attempting to delete a message from an account that does not exist")
            case "DAT":
                self.logged_in = False
                self.reset_state()
                pass

            case _:
                print("Unknown message type:", request_type)



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chat App")
        self.geometry("800x600")

        self.state = CentralState()
        connected = self.state.connect_to_server()
        if connected:
            threading.Thread(target=self.state.read_from_server, daemon=True).start()

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.show_frame(Onboarding)

    def show_frame(self, page):
        if page not in self.frames:
            self.frames[page] = page(self.container, self, self.state)
            self.frames[page].grid(row=0, column=0, sticky="nsew")

        frame = self.frames[page]
        self.frames[page].tkraise()

        if page == SearchAccount or page == Chat or page == Onboarding:
            frame.update_accounts()
        elif page == MessageDisplay:
            frame.update_messages()

        if page == MessageDisplay:
            frame.refresh_page()

    def get_state(self):
        return self.state

    def run(self):
        self.mainloop()


class Onboarding(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state
        self.current_users = state.accounts

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

    def update_accounts(self):
        if self.state.is_json:
            self.state.write_to_server_json({"type": "LA"})
        else:
            self.state.write_to_server("LA")
        self.after_id = self.after(500, self.update_accounts)

    def leave_to_navigation(self):
        print("Leaving Onboarding...")
        self.after_cancel(self.after_id)
        self.controller.show_frame(Navigation)


    # gpt
    def enhash(self, password):
        # Simple shift of ASCII values and reversal
        shifted = ''.join(chr((ord(c) + 5) % 128) for c in password)
        return shifted[::-1]

    def handle_login(self):
        username = self.textbox_username.get()
        password = self.textbox_password.get()
        print("==== HANDLE LOGIN ====")
        print("Before - state.is_logged_in:", self.state.is_logged_in)
        print("Before - state.current_user:", self.state.current_user)
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        if ' ' in username or ' ' in password:
            messagebox.showerror("Error", "Username and password cannot contain spaces")
            return

        if username in self.state.accounts:
            hashed_password = self.enhash(password)
            if self.state.is_json:
                return_value = {
                    "type": "LI",
                    "username": username,
                    "password": hashed_password
                }
            else:
                return_value = "LI" + username + " " + hashed_password
            if self.state.write_to_server(return_value):
                self.state.current_user = username
                self.after(500, self.check_login_success)
            else:
                messagebox.showerror("Error", "Login failed. Please try again.")
        else:
            messagebox.showerror("Error", "Account does not exist.")

    def handle_create_account(self):
        username = self.textbox_username.get()
        password = self.textbox_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        if ' ' in username or ' ' in password:
            messagebox.showerror("Error", "Username and password cannot contain spaces")
            return
        if username in self.state.accounts:
            messagebox.showerror("Error", "Account already exists.")
            return

        hashed_password = self.enhash(password)
        if self.state.is_json:
            return_value = {
                "type": "CR",
                "username": username,
                "password": hashed_password
            }
        else:
            return_value = "CR" + username + " " + hashed_password
        if self.state.write_to_server(return_value):
            # Store these for after we get CRT response
            self.pending_username = username
            self.pending_password = hashed_password
            self.after(500, self.complete_account_creation)

    def complete_account_creation(self):
        # Only proceed with login if we got CRT confirmation
        if self.pending_username and self.pending_password:
            if self.state.is_json:
                login_value = {
                    "type": "LI",
                    "username": self.pending_username,
                    "password": self.pending_password
                }
            else:
                login_value = "LI" + self.pending_username + " " + self.pending_password
            self.state.current_user = self.pending_username
            if self.state.write_to_server(login_value):
                self.after(500, self.check_login_success)

    def check_login_success(self):
        if self.state.is_logged_in is False:
            messagebox.showerror("Error", "Login failed. Please try again.")
        else:
            self.state.current_user = self.textbox_username.get()
            self.textbox_username.delete(0, tk.END)
            self.textbox_password.delete(0, tk.END)
            self.leave_to_navigation()


class Navigation(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state

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

    def on_delete_account(self):
        if self.state.is_json:
            message_to_write = {
                "type": "DA",
                "username": self.state.current_user
            }
        else:
            message_to_write = "DA" + self.state.current_user
        if self.state.write_to_server(message_to_write):
            self.state.reset_state()
            self.controller.show_frame(Onboarding)

    def handle_logout(self):
        if self.state.is_json:
            message_to_write = {
                "type": "LO",
                "username": self.state.current_user
            }
        else:
            message_to_write = "LO" + self.state.current_user
        if self.state.write_to_server(message_to_write):
            self.state.reset_state()
            self.state.is_logged_in = False
            self.controller.show_frame(Onboarding)

class Chat(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state


        self.grid_columnconfigure(1, weight=1)

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

    def back_to_navigation(self):
        self.after_cancel(self.after_id)
        self.controller.show_frame(Navigation)

    def update_accounts(self):
        if self.state.is_json:
            self.state.write_to_server_json({"type": "LA"})
        else:
            self.state.write_to_server("LA")
        self.after_id = self.after(500, self.update_accounts)

    def on_button_click(self):
        username = self.username_textbox.get()
        message = self.entry_textbox.get()

        if not username or not message:
            self.status_label.config(text="Please fill in both username and message.", fg="red")
            return

        if username not in self.state.accounts:
            self.status_label.config(text="Failed to send message.", fg="red")
            return

        timestamp = str(datetime.now()).replace(" ", "")
        if self.state.is_json:
            send_value = {
                "type": "SE",
                "from_username": self.state.current_user,
                "to_username": username,
                "timestamp": timestamp,
                "message": message
            }
        else:
            send_value = f"SE{self.state.current_user} {username} {timestamp} {message}"

        if self.state.write_to_server(send_value):
            self.status_label.config(text="Message sent successfully!", fg="green")
            self.entry_textbox.delete(0, tk.END)
            self.username_textbox.delete(0, tk.END)
        else:
            self.status_label.config(text="Failed to send message.", fg="red")

class MessageDisplay(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state
        self.number_of_messages = 10
        self.after_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.back_button = ttk.Button(
            self,
            text="Back to Navigation",
            command=lambda: controller.show_frame(Navigation)
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.delete_button = ttk.Button(
            self,
            text="Delete Message",
            command=self.delete_message
        )
        self.delete_button.grid(row=0, column=3, sticky="w", padx=10, pady=10)
        # to count the number of messages
        self.message_count_entry = ttk.Entry(self, width=5)
        self.message_count_entry.grid(row=0, column=4, sticky="e", padx=10, pady=10)


        self.set_message_count_button = ttk.Button(
            self,
            text="Enter",
            command=self.set_message_count,
        )
        self.set_message_count_button.grid(row=0, column=5, sticky="e", padx=10, pady=10)

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.message_list = tk.Listbox(self.paned)
        self.message_list.bind('<<ListboxSelect>>', self.display_message)

        self.message_content = tk.Text(self.paned, wrap=tk.WORD)
        self.message_content.config(state='disabled')

        self.paned.add(self.message_list)
        self.paned.add(self.message_content)

        self.messages = self.state.messages.copy()
        for msg in self.messages:
            formatted_msg = f"From: {msg['sender']}: {msg['message']} \n\n At: {msg['timestamp']}"
            self.message_list.insert(tk.END, formatted_msg)

        self.update_messages()

    def back_to_navigation(self):
        if hasattr(self, "after_id") and self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
            self.message_content.delete(1.0, tk.END)

        self.controller.show_frame(Navigation)



    def set_message_count(self):
        try:
            new_count = self.message_count_entry.get()
            print("Entered count:", new_count)

            if new_count and new_count.isdigit():
                print("Old message count:", self.number_of_messages)
                self.number_of_messages = int(new_count)
                print("New message count:", self.number_of_messages)

                # Clear current display
                self.message_list.delete(0, tk.END)
                self.messages = []
                if self.state.is_json:
                    self.state.write_to_server_json({
                        "type": "RE",
                        "username": self.state.current_user,
                        "number": self.number_of_messages
                    })
                else:
                    self.state.write_to_server("RE" + self.state.current_user + " " + str(self.number_of_messages))
                print("Sent request for", self.number_of_messages, "messages")

            else:
                print("Invalid input:", new_count)
        except ValueError as e:
            print("Error:", e)
            messagebox.showerror("Error", "Please enter a valid number")


    def refresh_page(self):
        self.message_list.delete(0, tk.END)
        self.messages = self.state.messages.copy()

        for msg in self.messages:
            formatted_msg = f"From: {msg['sender']}: {msg['message']} \n\n At: {msg['timestamp']}"
            self.message_list.insert(tk.END, formatted_msg)

        self.update_messages()

    def update_messages(self):
        print("displaying self.state.messages", self.state.messages)
        print("displaying self.messages", self.messages)
        # We're logged out, stop updating messages
        if not self.state.current_user or not self.state.is_logged_in:
            return
        if self.state.is_json:
            self.state.write_to_server_json({
                "type": "RE",
                "username": self.state.current_user,
                "number": self.number_of_messages
            })
        else:
            self.state.write_to_server("RE" + self.state.current_user + " " + str(self.number_of_messages))

        # Only update display if messages have actually chaanged
        if self.state.messages != self.messages:
            current_selection = self.message_list.curselection()
            current_scroll = self.message_list.yview()

            # (prevent reference copy so i can update messages)
            self.messages = self.state.messages.copy()

            #Rebuild display
            self.message_list.delete(0, tk.END)
            for msg in self.state.messages[:self.number_of_messages]:
                formatted_msg = f"From: {msg['send']}: {msg['message']} \n\n At: {msg['timestamp']}"
                self.message_list.insert(tk.END, formatted_msg)

            # Restore selection/scroll position if needed
            if current_selection:
                self.message_list.selection_set(current_selection)
            self.message_list.yview_moveto(current_scroll[0])
        self.after_id = self.after(500, self.update_messages)

    def display_message(self, event):
        print("displaying self.state.messages", self.state.messages)
        print("displaying self.messages", self.messages)
        if not self.message_list.curselection():
            return

        selection = self.message_list.curselection()[0]
        message_dict = self.messages[selection]
        formatted_message = f"From: {message_dict['sender']}: {message_dict['message']} \n\n At: {message_dict['timestamp']}"

        self.message_content.config(state='normal')
        self.message_content.delete(1.0, tk.END)
        self.message_content.insert(1.0, formatted_message)
        self.message_content.config(state='disabled')

    def delete_message(self):
        if self.message_list.curselection():
            selection = self.message_list.curselection()[0]
            message_to_delete = self.messages[selection]
            message_id = message_to_delete["messageId"]
            if self.state.is_json:
                delete_command = {
                    "type": "DM",
                    "username": self.state.current_user,
                    "messageId": message_id
                }
            else:
                delete_command = "DM" + self.state.current_user + " " + message_id

            if self.state.write_to_server(delete_command):
                print("Message deleted successfully")


class SearchAccount(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state
        self.accounts = self.state.accounts
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
        self.state.write_to_server("LA")
        self.display_accounts()
        self.after_id = self.after(500, self.update_accounts)

    def display_accounts(self, filter_text=None):
        # Always display if we have a filter_text, regardless of whether accounts changed
        if not filter_text and not self.is_first_display and self.state.accounts == self.accounts:
            return

        self.is_first_display = False
        # Make a copy to ensure proper comparison rather than a reference
        self.accounts = self.state.accounts.copy()
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)

        displayed_accounts = self.accounts

        if filter_text:
            displayed_accounts = [user for user in displayed_accounts if filter_text.lower() in user.lower()]
            print("Filtered accounts:", displayed_accounts)

        for username in displayed_accounts:
            self.results_text.insert(tk.END, f"Username: {username}\n")

        self.results_text.config(state='disabled')

    def search_account(self):
        search_term = self.username_textbox.get()
        print("Searching for:", search_term)
        self.display_accounts(search_term)



if __name__ == "__main__":
    print("Hello, World!")
    app = App()
    app.run()
