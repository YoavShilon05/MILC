import threading
import tkinter, tkinter.messagebox, tkinter.simpledialog

import pystray
from pystray import MenuItem as Item
from pystray import Menu
from PIL import Image
from plyer import notification

import AssiNet
import Connection
from Settings import *
from AssiClient import Client

_tk = tkinter.Tk()
_tk.withdraw()

class Tray():
    def __init__(self, connection: Connection.Connection):
        self.conn = connection
        self.client = Client(username, self.conn)

    def download_files(self):
        for f in self.client.receive_files():
            if f == "!stop":
                break

            target = f.split('/')[2]
            basename = os.path.basename(f.rstrip('/'))
            self.conn.receive_file(target, basename.encode())
            notification.notify(title="MILC", message=f'Received new file "{basename}"', app_icon=f"{home}/MILC.ico")

        self.client.__exit__(None, None, None)

    def create_project(self):
        name = tkinter.simpledialog.askstring("New Project", "What is the name of the new project?")
        if name is None:
            return

        folders = map(lambda f: f.rstrip('/'), self.conn.get_remote_files("~/assi-pkg"))

        if name in folders:
            tkinter.messagebox.showerror("Error", "Invalid project name")
            return

        canceled = False

        def get_users_prompt():
            tk = tkinter.Tk()
            users = self.conn.get_users()
            checkmarks = {}

            vars = {}
            for u in users:
                var = tkinter.BooleanVar(tk, value=True)
                box = tkinter.Checkbutton(tk, text=u, variable=var)
                vars[u] = var
                checkmarks[u] = box
                box.pack()

            def ok_():
                tk.quit()
                tk.destroy()

            ok = tkinter.Button(tk, command=ok_, text="Ok", padx=20, pady=5)
            ok.pack()

            def cancel_():
                nonlocal canceled
                canceled = True
                tk.quit()
                tk.destroy()

            cancel = tkinter.Button(tk, command=cancel_, text="Cancel", padx=20, pady=5)
            cancel.pack()
            tk.mainloop()

            if canceled: return

            return list(filter(lambda u: u not in folders and vars[u].get(), vars.keys()))

        users = get_users_prompt()
        if canceled: return
        while len(users) <= 1:
            tkinter.messagebox.showerror("Error", "Cannot create project with less than 2 people.")
            users = get_users_prompt()
            if canceled: return

        self.conn.ssh.exec_command(f"mkdir ~/assi-pkg/{name}")
        self.conn.ssh.exec_command(f'echo "{name}:{",".join(users)}" >> ~/assi-pkg/projects.txt')
        self.conn.update_users()

    def run_tray(self):
        self.conn.receive(True)

        thread = threading.Thread(target=self.download_files)
        thread.start()

        def on_send(*args):
            self.conn.send_root()

        def on_recv(*args):
            self.conn.receive(False)

        def on_leave(icon, *args):
            icon.stop()
            AssiNet.send(self.client.client, b"!stop")
            thread.join(5)

        def settings(*args):
            os.system(f"start {settings_path}")

        def send_project(p: str):
            self.client.send_file(f"{root}\\{p}", p)

        def construct_projects():
            for p in self.conn.get_projects():
                yield Item(p, lambda: send_project(p))

        # name, img, hovertxt, menu
        icon = pystray.Icon("MILC", Image.open(f"{home}/MILC.ico"), "Hi mom, please press this icon to open up the options menu <3",
                            pystray.Menu(Item("Send root folder", on_send, default=True),
                            Item("Update root folder", on_recv),
                            Item("Create project", self.create_project),
                            Item("Update users and projects", self.conn.update_users),
                            Item("Send project", Menu(construct_projects)),
                            Item("Settings", settings),
                            Item("Leave Exit MILC", on_leave)))

        icon.run()