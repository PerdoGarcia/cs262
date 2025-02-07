import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Application Switcher")
        self.geometry("800x600")
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for f in (SignIn, Chat):

            frame = f(container, self)
            self.frames[f] = frame
            frame.grid(row=0, column=0, sticky="nsew")


        self.show_frame(SignIn)


    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def switch_applications(self):
        pass

    def run(self):
        self.mainloop()



class SignIn(tk.Frame):
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

        self.button = tk.Button(self, text="Sign In", command=self.on_button_click)
        self.button.grid(row=2, column=1)

    def on_button_click(self):
        # self.textbox.delete(1.0, tk.END)
        # self.textbox.insert(tk.END, f"Hello, World! {datetime.now()}")
        self.controller.show_frame(Chat)

    def on_check_click(self):
        messagebox.showinfo("Check", "Check clicked")


class Chat(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.entry_textbox = tk.Entry(self)
        self.entry_textbox.grid(row=4, column=2,rowspan=1, columnspan=1, )
        # we need a lock
        self.message_list = []

        self.button = tk.Button(self, text="Enter Me", command=self.on_button_click)
        self.button.grid(row=4, column=4)

        self.messages = tk.Text(self, state='disabled')
        self.messages.grid(row=0, column=3)


    def on_button_click(self):
        message = self.entry_textbox.get()
        if message:
            self.add_message(message)
            self.entry_textbox.delete(0, tk.END)

    def add_message(self, message):
        self.message_list.append(message)
        self.update_message_display()

    def update_message_display(self):
        self.messages.config(state='normal')
        self.messages.delete(1.0, tk.END)
        for message in self.message_list:
            self.messages.insert(tk.END, f"{message}\n")
        self.messages.config(state='disabled')



if __name__ == "__main__":
    print("Hello, World!")
    app = App()
    app.run()
