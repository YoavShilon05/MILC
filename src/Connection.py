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
        def delete_subkeys(key0, current_key):
            # stolen from https://stackoverflow.com/questions/38205784/python-how-to-delete-registry-key-and-subkeys-from-hklm-getting-error-5
            with (winreg.OpenKey(key0, current_key, 0, winreg.KEY_ALL_ACCESS)) as key:
                info_key = winreg.QueryInfoKey(key)
                for x in range(info_key[0]):
                    sub_key = winreg.EnumKey(key, 0)
                    try: winreg.DeleteKey(key, sub_key)
                    except OSError: delete_subkeys(key0, "\\".join([current_key, sub_key]))

        def add(path, u, arg='%1'):
            with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}")) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"Send to {u}")
                winreg.SetValueEx(key, "Icon", None, winreg.REG_EXPAND_SZ, rf"%appdata%\MILC\MILC.ico")
            with (winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{path}\shell\MILCTo\shell\SendTo{u}\command")) as key:
                winreg.SetValueEx(key, "", None, winreg.REG_EXPAND_SZ, f'%appdata%\MILC\MILC.exe "sendto" "{arg}" "{u}"')

        _, stdout, _ = self.ssh.exec_command("ls ~/assi-pkg/")

        delete_subkeys(winreg.HKEY_CLASSES_ROOT, r"*\shell\MILCTo\shell")
        delete_subkeys(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\MILCTo\shell")
        delete_subkeys(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\MILCTo\shell")

        for u in stdout.read().decode().split('\n'):
            if u == '' or u == username or u == "projects.txt": continue
            add("*", u)
            add("Directory", u)
            add("Directory\\Background", u, '%w')

    @staticmethod
    def backup():
        source_folder = localroot
        destination_folder = f"{localroot}/.assi-backup"
        os.system("rmdir " + destination_folder.replace('/', '\\') + " /s /q")

        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

    def get_users(self):
        _, folders, _ = self.ssh.exec_command("ls ~/assi-pkg/")
        _, projects, _ = self.ssh.exec_command("cat ~/assi-pkg/projects.txt")
        project_names = list(map(lambda p : p.split(':')[0], projects.read().decode().split("\n")))
        return list(filter(lambda f: f not in project_names and f != "projects.txt", folders.read().decode().split("\n")))

    def send(self, dir : str):
        if os.path.normpath(dir) not in localroot:
            if os.path.isfile(dir):
                file = os.path.basename(dir)
                shutil.copyfile(dir, localroot + "/" if garbage is not "" else "" + garbage + "/" + file)
            elif os.path.isdir(dir):
                folder = os.path.basename(dir)
                dst = localroot + garbage + "/" + folder
                if os.path.isdir(dst):
                    remove_tree(dst)
                os.mkdir(dst)
                copy_tree(dir, dst)

        self.ssh.exec_command(f"rm -rf {remote}/*")

    def send_root(self):
        files = os.listdir(localroot)

        for f in files:
            if f.startswith(".") or f in self.get_projects(): continue
            self.scp.put(f"{localroot}/{f}", (remote + "/" + f).encode(), True, True)

    def clear_root(self):
        files = os.listdir(localroot)
        for f in files:
            if not f.startswith("."):
                path = localroot.replace('/', '\\') + f"\\{f}"
                if os.path.isfile(path):
                    os.system(f"del {path}")
                elif os.path.isdir(path):
                    os.system(f"rmdir {path} /s /q")

    def receive_file(self, target: str, file: bytes): #target = projectname/username, target=Yoav
        src = f"~/assi-pkg/{target}/".encode() + file
        if file.endswith(b"/"): src += b"."

        folder = f"{localroot}/{target}"
        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

        dst = f"{folder}/{file.decode()}" if target != username else f"{folder}/{payload}/{file.decode()}"
        if os.path.isdir(dst):
            remove_tree(dst)
        elif os.path.isfile(dst):
            os.remove(dst)

        self.scp.get(src, dst, True, True)

    def get_remote_files(self, folder: str) -> list[str]:
        _, stdout, _ = self.ssh.exec_command(f"ls -p {folder}")
        return stdout.read().decode().split('\n')

    def receive_target(self, target):
        stdin, stdout, stderr = self.ssh.exec_command(f"ls -p ~/assi-pkg/{target}")
        files = stdout.read().split(b"\n")[:-1]
        for f in files:
            if f.startswith(b"."): continue
            self.receive_file(target, f)

    def get_projects(self) -> list[str]:
        _, stdout, _ = self.ssh.exec_command("cat ~/assi-pkg/projects.txt")
        return [p.split(':')[0] for p in
                list(filter(lambda l: l != "" and username in l.split(':')[1].split(','),
                            stdout.read().decode().split('\n')))]

    def receive(self, startup=False):
        if not startup:
            ok = tkinter.messagebox.askokcancel("Warning!",
                "Pulling mid-session might result in data loss!\nAre you sure you want to proceed?")
            if not ok:
                return

        self.backup()
        self.clear_root()
        self.receive_target(username)

        # for p in self.get_projects():
        #     self.receive_target(p)
