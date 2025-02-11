import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import socket

class CentralState:
    def __init__(self):
        self.current_user = None
        self.messages = {}
        self.accounts = []
        self.socket = None
        self.is_connected = False
        self.host = "127.0.0.1"
        self.port = 54400


    def reset_state(self):
        self.current_user = None
        self.messages = {}


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
        while self.is_connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("Server connection closed")
                    self.is_connected = False
                    break

                message = data.decode('utf-8')
                print(f"Received: {message}")
                self.handle_reads(message)
            except Exception as e:
                print("Error reading from server:", e)
                self.is_connected = False
                break

    def handle_reads(self, server_message):
        request_type = server_message[:3]
        data = server_message[3:]

        match request_type:
            case "CRT":
                self.current_user = data
                pass
            case "LIT":
                self.current_user = data
                pass
            case "LOT":
                self.reset_state()
                pass
            case "LAT":
                self.accounts = data.split(" ")
                print("Active Accounts:", ", ".join(self.accounts))
            case "RET":
                parts = data.split(" ")
                num_read = int(parts[0])
                self.messages = []
                index = 1

                for _ in range(num_read):
                    message_id = parts[index]
                    sender = parts[index + 1]
                    timestamp = parts[index + 2]
                    message_length = int(parts[index + 3])
                    message_content = " ".join(parts[index + 4 : index + 4 + message_length])
                    index += 4 + message_length

                    self.messages.append({
                        "Message ID": message_id,
                        "Sender": sender,
                        "Timestamp": timestamp,
                        "Message": message_content
                    })

                print(f"Retrieved {num_read} messages:")
                for msg in self.messages:
                    print(f"ID: {msg['Message ID']}, From: {msg['Sender']}, Time: {msg['Timestamp']}")
                    print(f"Message: {msg['Message']}\n")
            case "SET":
                pass
            case "ER0":
                pass
            case "DAT":
                pass
            case _:
                print(server_message)


    # perhaps create a thread on the client for reading
    # and create a thread on the client for writing
    def write_to_server(self, message):
        if not self.is_connected:
            print("Not connected to server")
            return False

        try:
            self.socket.sendall(message.encode('utf-8'))
            print(f"Sent: {message}")
            return True
        except Exception as e:
            print("Failed to write to the server.")
            print(e)
            return False


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

        self.frames[page].tkraise()

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

        self.label_username = tk.Label(self, text='First Name')
        self.label_username.grid(row=0)

        self.label_password = tk.Label(self, text='Last Name')
        self.label_password.grid(row=1)

        self.textbox_username = tk.Entry(self)
        self.textbox_username.grid(row=0, column=1)

        self.textbox_password = tk.Entry(self)
        self.textbox_password.grid(row=1, column=1)

        self.button = tk.Button(self, text="Login", command=self.handle_login)
        self.button.grid(row=2, column=1)
        self.button = tk.Button(self, text="Create Account", command=self.handle_create_account)
        self.button.grid(row=2, column=2)

    def refresh_accounts(self):
        self.current_users = self.state.accounts
        self.after(100, self.refresh_accounts)

    # gpt
    def enhash(self, password):
        # Simple shift of ASCII values and reversal
        shifted = ''.join(chr((ord(c) + 5) % 128) for c in password)
        return shifted[::-1]

    def handle_login(self):
        if not self.textbox_username.get() or not self.textbox_password.get():
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        else:
            if self.textbox_username.get() in self.current_users:
                hashed_password = self.enhash(self.textbox_password.get())
                return_value = "LI" + self.textbox_username.get() + " " + hashed_password
                if self.state.write_to_server(return_value):
                    # todo do a check for a user existing
                    self.after(100, self.check_login_success)

    def handle_create_account(self):
        if not self.textbox_username.get() or not self.textbox_password.get():
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        else:
            # todo: hash password
            hashed_password = self.enhash(self.textbox_password.get())
            return_value = "CR" + self.textbox_username.get() + " " + hashed_password
            print(return_value)
            self.state.current_user = self.textbox_username.get()
            if self.state.write_to_server(return_value):
            # todo handle if user already exists
                self.after(100, self.check_login_success)

    def check_login_success(self):
        if self.state.current_user is None:
            messagebox.showerror("Error", "Login failed. Please try again.")
        else:
            self.state.current_user = self.textbox_username.get()

            self.controller.show_frame(Navigation)


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
        if self.state.write_to_server("DA" + self.state.current_user):
            self.state.reset_state()
            self.controller.show_frame(Onboarding)

    def handle_logout(self):
        if self.state.write_to_server("LO" + self.state.current_user):
            self.state.reset_state()
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
            command=lambda: controller.show_frame(Navigation)
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


    def update_accounts(self):
        self.state.write_to_server("LA")
        self.after(100, self.update_accounts)

    def on_button_click(self):
        username = self.username_textbox.get()
        message = self.entry_textbox.get()
        if message and username:
            # (TODO): validation

            if username in self.state.accounts:
                send_value = "SE" + self.state.current_user + " " + username + " " + (str(datetime.now()).replace(" ", "")) + " " + message
                self.state.write_to_server(send_value)
                # check if message was actually sent
                self.status_label.config(
                    text="Email sent successfully!",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text="Failed to send email.",
                    fg="red"
                )
                return

            self.entry_textbox.delete(0, tk.END)
            self.username_textbox.delete(0, tk.END)
        else:
            self.status_label.config(
                text="Please fill in both username and message.",
                fg="red"
            )
            return

    def check_username(self, username):
        # (TODO): Implement this method
        return True
        pass

class MessageDisplay(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state
        self.number_of_messages = 10
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

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.message_list = tk.Listbox(self.paned)
        self.message_list.bind('<<ListboxSelect>>', self.display_message)

        self.message_content = tk.Text(self.paned, wrap=tk.WORD)
        self.message_content.config(state='disabled')

        self.paned.add(self.message_list)
        self.paned.add(self.message_content)

        self.messages = self.state.messages

        for msg in self.messages:
            self.message_list.insert(tk.END, msg)

    # do something with threads to listen for messages

    def update_messages(self):
        self.state.write_to_server("RE" + self.state.current_user + " " + str(self.number_of_messages))
        self.after(1000, self.update_messages)


    def display_message(self, event):
        if not self.message_list.curselection():
            return

        selection = self.message_list.curselection()[0]
        full_message = self.state.messages[selection]

        message_text = f"From: {full_message['Sender']}\n"
        message_text += f"Time: {full_message['Timestamp']}\n"
        message_text += f"Message: {full_message['Message']}"

        self.message_content.config(state='normal')
        self.message_content.delete(1.0, tk.END)
        self.message_content.insert(1.0, message_text)
        self.message_content.config(state='disabled')

    def delete_message(self):
        # todo deal with message deletion later
        if self.message_list.curselection():
            print(self.message_list.curselection())
            selection = self.message_list.curselection()[0]
            self.message_list.delete(selection)
            self.message_content.config(state='normal')
            # c
            self.message_content.delete(1.0, tk.END)
            self.message_content.config(state='disabled')
        pass


class SearchAccount(tk.Frame):
    def __init__(self, parent, controller, state : CentralState):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.state = state

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.back_button = ttk.Button(
            self,
            text="Back to Navigation",
            command=lambda: controller.show_frame(Navigation)
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

    def update_accounts(self):
        self.state.write_to_server("LA")
        self.display_accounts()
        self.after(100, self.update_accounts)

    def display_accounts(self, filter_text=None):
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)

        displayed_accounts = self.state.accounts

        if filter_text:
            displayed_accounts = [user for user in displayed_accounts if filter_text.lower() in user.lower()]

        for username in displayed_accounts:
            self.results_text.insert(tk.END, f"Username: {username}\n")

        self.results_text.config(state='disabled')

    def search_account(self):
        """Search for an account dynamically."""
        search_term = self.username_textbox.get()
        self.display_accounts(search_term)



if __name__ == "__main__":
    print("Hello, World!")
    app = App()
    app.run()
