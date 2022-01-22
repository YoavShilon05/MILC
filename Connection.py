import shutil
import tkinter.messagebox
import winreg
from distutils.dir_util import remove_tree, copy_tree

import paramiko
from scp import SCPClient

from Settings import *

class Connection:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.connect(ip, 22, username=ssh_username, password=ssh_password)

        # SCPCLient takes a paramiko transport as an argument
        self.scp = SCPClient(self.ssh.get_transport())

    def install(self):
        self.ssh.exec_command(f"mkdir -p {remote}")

    def update_users(self):
        def add(path, u, arg='%1'):
            with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}")) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"Send to {u}")
                winreg.SetValueEx(key, "Icon", None, winreg.REG_EXPAND_SZ, rf"%appdata%\MILC\MILC.ico")
            with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}\command")) as key:
                winreg.SetValueEx(key, "", None, winreg.REG_EXPAND_SZ, f'%appdata%\MILC\MILC.exe "sendto" "{arg}" "{u}"')

        _, stdout, _ = self.ssh.exec_command("ls ~/assi-pkg/")
        for u in stdout.read().split(b'\n'):
            u = u.decode()
            if u == '' or u == username: continue
            add("*", u)
            add("Directory", u)
            add("Directory\\Background", u, '%w')

    @staticmethod
    def backup():
        source_folder = root
        destination_folder = f"{root}/.assi-backup"
        os.system("rmdir " + destination_folder.replace('/', '\\') + " /s /q")

        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

    def get_users(self):
        _, folders, _ = self.ssh.exec_command("ls ~/assi-pkg/")
        _, projects, _ = self.ssh.exec_command("cat ~/assi-pkg/projects.txt")
        project_names = list(map(lambda p : p.split(':')[0], projects.read().decode().split("\n")))
        return list(filter(lambda f: f not in project_names, folders.read().decode().split("\n")))

    def send(self, dir : str):
        if os.path.normpath(dir) not in root:
            if os.path.isfile(dir):
                file = os.path.basename(dir)
                shutil.copyfile(dir, root + garbage + "/" + file)
            elif os.path.isdir(dir):
                folder = os.path.basename(dir)
                dst = root + garbage + "/" + folder
                if os.path.isdir(dst):
                    remove_tree(dst)
                os.mkdir(dst)
                copy_tree(dir, dst)

        self.ssh.exec_command(f"rm -rf {remote}/*")

        files = os.listdir(root)

        for f in files:
            if f.startswith("."): continue
            self.scp.put(f"{root}/{f}", (remote + "/" + f).encode(), True, True)

    def recv(self, startup=False):

        if not startup:
            ok = tkinter.messagebox.askokcancel("Warning!",
                "Pulling mid-session might result in data loss!\nAre you sure you want to proceed?")
            if not ok:
                return

        self.backup()

        # clean root
        files = os.listdir(root)
        for f in files:
            if not f.startswith("."):
                path = root.replace('/', '\\') + f"\\{f}"
                if os.path.isfile(path):
                    os.system(f"del {path}")
                elif os.path.isdir(path):
                    os.system(f"rmdir {path} /s /q")



        stdin, stdout, stderr = self.ssh.exec_command(f"ls {remote}")
        files = stdout.read().split(b"\n")[:-1]
        for f in files:
            if not f.startswith(b"."):
                self.scp.get(f"{remote}/".encode() + f, f"{root}/{f.decode()}", True, True)