import paramiko
from scp import SCPClient
import os, os.path
from distutils.dir_util import copy_tree, remove_tree
from shutil import copyfile

import configparser

import sys

import tkinter
import tkinter.messagebox

from PIL import Image
import pystray
from pystray import MenuItem as Item

tk = tkinter.Tk()
tk.withdraw()


config = configparser.ConfigParser()
path = os.path.expandvars("%appdata%/MILC/settings.ini")
config.read(path)

ip = config["SSH"]["IP"]
ssh_username = config["SSH"]["Username"]
ssh_password = config["SSH"]["Password"]

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.connect(ip, 22, username=ssh_username, password=ssh_password)

# SCPCLient takes a paramiko transport as an argument
scp = SCPClient(ssh.get_transport())


root = config["Local"]["Root"]
garbage = config["Remote"]["GarbageDestination"]
username = config["Remote"]["Username"]

remote = f"~/assi-pkg/{username}"

def connect():
    ssh.exec_command(f"mkdir -p {remote}")

def backup():
    source_folder = root
    destination_folder = f"{root}/.assi-backup"
    os.system("rmdir " + destination_folder.replace('/', '\\') + " /s /q")

    copy_tree(source_folder, destination_folder)
                    # ignore=lambda src, names : filter(lambda name : not name.startswith('.'), names))

def send(dir : str):
    if dir not in root:
        if os.path.isfile(dir):
            file = os.path.basename(dir)
            copyfile(dir, root + garbage + "/" + file)
        elif os.path.isdir(dir):
            folder = os.path.basename(dir)
            dst = root + garbage + "/" + folder
            if os.path.isdir(dst):
                remove_tree(dst)
            os.mkdir(dst)
            copy_tree(dir, dst)

    ssh.exec_command(f"rm -rf {remote}/*")

    files = os.listdir(root)

    for f in files:
        if f.startswith("."): continue
        scp.put(f"{root}/{f}", (remote + "/" + f).encode(), True, True)

def recv(startup=False):

    if not startup:
        ok = tkinter.messagebox.askokcancel("Warning!",
            "Pulling mid-session might result in data loss!\nAre you sure you want to proceed?")
        if not ok:
            return

    backup()

    # clean root
    files = os.listdir(root)
    for f in files:
        if not f.startswith("."):
            path = root.replace('/', '\\') + f"\\{f}"
            if os.path.isfile(path):
                os.system(f"del {path}")
            elif os.path.isdir(path):
                os.system(f"rmdir /S /Q \"{path}\"")



    stdin, stdout, stderr = ssh.exec_command(f"ls {remote}")
    files = stdout.read().split(b"\n")[:-1]
    for f in files:
        if not f.startswith(b"."):
            scp.get(f"{remote}/".encode() + f, f"{root}/{f.decode()}", True, True)

def run_tray():
    recv(True)

    def on_send(*args):
        send(root)

    def on_recv(*args):
        recv(False)

    def on_leave(icon, *args):
        icon.stop()

    home = os.path.expandvars("%appdata%/MILC/")

    # name, img, hovertxt, menu
    icon = pystray.Icon("MILC", Image.open(home + "MILC.ico"), "Hi mom, please press this icon to open up the options menu <3",
                        pystray.Menu(Item("Send root folder", on_send, default=True),
                        Item("Update root folder", on_recv),
                        Item("Leave Exit MILC", on_leave)))

    icon.run()

if __name__ == "__main__":
    # expected args -
    # init - connection
    # send, dir - send
    # startup - recv, startup
    # recv - recv
    # tray - run MILC in tray

    match (sys.argv[1]):
        case "init":
            connect()
        case "send":
            send(sys.argv[2].replace("\\\\", "/").replace("\\", "/"))
        case "startup":
            recv(True)
        case "recv":
            recv()
        case "tray":
            run_tray()
        case _:
            raise ValueError("Beware! The Value entered for the above argument while running this very program has resulted "
                            "in a fatal error! please take the nessecary steps to make sure this type of argument won't be "
                            "passed to this program any more.")
