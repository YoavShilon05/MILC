import threading
import tkinter, tkinter.messagebox, tkinter.simpledialog
import winreg
from distutils.dir_util import remove_tree

import pystray
from pystray import MenuItem as Item
from PIL import Image
from plyer import notification

import Connection
from Settings import *
from AssiClient import Client

_tk = tkinter.Tk()
_tk.withdraw()

class Tray():
    def __init__(self, connection : Connection.Connection):
        self.conn = connection

        self.client = Client(username, self.conn)

    def download_files(self):
        self.stop_download = False
        for f in self.client.receive_files():
            if self.stop_download: break

            basename = os.path.basename(f)
            dst = f"{root}/assi-payload/{basename}"
            if os.path.isdir(dst):
                remove_tree(dst)
            elif os.path.isfile(dst):
                os.remove(dst)

            self.conn.scp.get(f.encode(), dst, True, True)
            notification.notify(title="MILC", message=f'Received new file "{basename}"', app_icon=f"{home}/MILC.ico")

        self.client.__exit__(None, None, None)

    def create_project(self):
        name = tkinter.simpledialog.askstring("New Project", "What is the name of the new project?")
        if name == None:
            return

        _, projects, _ = self.conn.ssh.exec_command("cat ~/assi-pkg/projects.txt")
        _, folders, _ = self.conn.ssh.exec_command("ls ~/assi-pkg")

        if name in map(lambda p: p.split(':')[0],
                       projects.read().decode().split("\n")) or name in folders.read().decode().split("\n"):
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

            if canceled:
                return

            return list(filter(lambda u: vars[u].get(), vars.keys()))

        if canceled:
            return

        users = get_users_prompt()

        self.conn.ssh.exec_command(f"mkdir ~/assi-pkg/{name}")
        self.conn.ssh.exec_command(f'echo "{name}:{",".join(users)}" >> ~/assi-pkg/projects.txt')
        self.conn.update_users()

    def run_tray(self):
        self.conn.recv(True)

        thread = threading.Thread(target=self.download_files)
        thread.start()

        def on_send(*args):
            self.conn.send(root)

        def on_recv(*args):
            self.conn.recv(False)

        def on_leave(icon, *args):
            icon.stop()
            self.stop_download = True
            thread.join(5)

        def settings(*args):
            os.system(f"start {settings_path}")

        # name, img, hovertxt, menu
        icon = pystray.Icon("MILC", Image.open(f"{home}/MILC.ico"), "Hi mom, please press this icon to open up the options menu <3",
                            pystray.Menu(Item("Send root folder", on_send, default=True),
                            Item("Update root folder", on_recv),
                            Item("Create project", self.create_project),
                            Item("Update users and projects", self.conn.update_users),
                            Item("Settings", settings),
                            Item("Leave Exit MILC", on_leave)))

        icon.run()
