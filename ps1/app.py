import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class CentralState:
    def __init__(self):
        self.current_user = None
        self.messages = {}
        self.accounts = []
        self.socket = None

    def connect_to_server(self):
        pass

    def read_from_server(self):
        pass

    def write_to_server(self):
        pass

    def get_messages(self):
        pass

    def send_message(self):
        pass

    def delete_message(self):
        pass

    def search_accounts(self):
        pass

    def delete_account(self):
        pass



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chat App")
        self.geometry("800x600")

        self.state = CentralState()
        self.state.connect_to_server()

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.show_frame(Onboarding)

    def show_frame(self, page):
        if page not in self.frames:
            self.frames[page] = page(self.container, self)
            self.frames[page].grid(row=0, column=0, sticky="nsew")

        self.frames[page].tkraise()

    def get_state(self):
        return self.state

    def switch_applications(self):
        pass

    def run(self):
        self.mainloop()


class Onboarding(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.label = tk.Label(self, text="Sign in")

        self.label_username = tk.Label(self, text='First Name')
        self.label_username.grid(row=0)

        self.label_password = tk.Label(self, text='Last Name')
        self.label_password.grid(row=1)

        self.textbox_username = tk.Entry(self)
        self.textbox_username.grid(row=0, column=1)

        self.textbox_password = tk.Entry(self)
        self.textbox_password.grid(row=1, column=1)

        # self.check_state = tk.IntVar()
        # self.check.pack(padx=10, pady=10)

        self.button = tk.Button(self, text="Login", command=self.on_button_click)
        self.button.grid(row=2, column=1)
        self.button = tk.Button(self, text="Create Account", command=self.on_button_click)
        self.button.grid(row=2, column=2)


    def on_button_click(self):
        self.controller.show_frame(Navigation)

    def handle_login(self):
        state = self.controller.get_state()
        if not self.textbox_username.get() or not self.textbox_password.get():
            messagebox.showerror("Error", "Please fill in both username and password.")
            return
        else:
            if self.textbox_username.get() in self.current_users:
                print(self.current_users)
                self.controller.show_frame(Navigation)
        pass

    def handle_create_account(self):
        pass


class Navigation(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        title_label = tk.Label(self, text="Navigation page", font=("Arial", 24))
        title_label.pack(pady=20)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        send_messages_btn = tk.Button(
            button_frame,
            text="Send Messages",
            command=lambda: controller.show_frame(Chat),
            width=20,
            height=2
        )
        send_messages_btn.pack(pady=10)

        read_messages_btn = tk.Button(
            button_frame,
            text="Read Messages",
            command=lambda: controller.show_frame(MessageDisplay),
            width=20,
            height=2
        )
        read_messages_btn.pack(pady=10)

        search_account = tk.Button(
            button_frame,
            text="Search Accounts",
            command=lambda: controller.show_frame(SearchAccount),
            width=20,
            height=2
        )
        search_account.pack(pady=10)

        logout_btn = tk.Button(
            self,
            text="Logout",
            command=lambda: controller.show_frame(Onboarding),
            width=10
        )
        logout_btn.pack(pady=20)

        delete_account_btn = tk.Button(
            self,
            text="Delete Account",
            command=self.on_delete_account(),
            width=10
        )
        delete_account_btn.pack(pady=20)

    def on_delete_account(self):
        state = self.controller.get_state()
        # todo: delete account
        self.controller.show_frame(Onboarding)
        pass

    def handle_logout(self):
        state = self.controller.get_state()
        state.current_user = None
        self.controller.show_frame(Onboarding)

class Chat(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

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

    def on_button_click(self):
        username = self.username_textbox.get()
        message = self.entry_textbox.get()
        state = self.controller.get_state()
        if message and username in state.accounts:
            # (TODO): validation
            success = True

            if success:
                self.status_label.config(
                    text="Email sent successfully!",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text="Failed to send email.",
                    fg="red"
                )

            self.entry_textbox.delete(0, tk.END)
            self.username_textbox.delete(0, tk.END)
        else:
            self.status_label.config(
                text="Please fill in both username and message.",
                fg="red"
            )

class MessageDisplay(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

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

        self.messages = [
            "Message 1",
            "Message 2",
            "Message 3"
        ]

        for msg in self.messages:
            self.message_list.insert(tk.END, msg)

    def refrresh_messages(self):
        # (TODO): Implement this method
        state = self.controller.get_state()
        state.get_messages()
        pass

    def display_message(self, event):

        if not self.message_list.curselection():
            return

        selection = self.message_list.curselection()[0]
        full_message = self.messages[selection]
        self.message_content.config(state='normal')
        self.message_content.delete(1.0, tk.END)
        self.message_content.insert(1.0, full_message)
        self.message_content.config(state='disabled')

    def delete_message(self):
        if self.message_list.curselection():
            selection = self.message_list.curselection()[0]
            self.message_list.delete(selection)
            self.message_content.config(state='normal')
            self.message_content.delete(1.0, tk.END)
            self.message_content.config(state='disabled')
        pass


class SearchAccount(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

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
        state = self.controller.get_state()
        state.search_accounts()

        self.after(100, self.display_accounts)

    def display_accounts(self, filter_text=None):
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)

        state = self.controller.get_state()
        displayed_accounts = state.accounts

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
