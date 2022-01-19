import os
import pickle
import socket
import tkinter.messagebox
from distutils.dir_util import remove_tree

from scp import SCPClient
from paramiko import SSHClient
from AssiNet import *

class Client:
    def __init__(self, username: str, scp: SCPClient, ssh: SSHClient, sending=False):
        self.username = username
        self.scp = scp
        self.ssh = ssh
        self.HOME = f"~/assi-pkg"
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(("84.229.3.23", PORT))
        send(self.client, self.username.encode() if not sending else "SEND".encode())

    def receive_files(self) -> str:
        while True:
            print('waiting for files')
            yield recv(self.client).decode()
            print("received file")

    def send_file(self, file: str, target: str):
        basename = f"{os.path.basename(file)}"
        payload = f"{self.HOME}/{target}/assi-payload"
        path = f"{payload}/{basename}"
        self.ssh.exec_command(f"mkdir -p {payload}")

        if os.path.isdir(file):
            self.ssh.exec_command(f"rm -rf {path}")

        self.scp.put(file.replace(" ", "_"), path.encode(), True, True)

        send(self.client, pickle.dumps((target, basename)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
