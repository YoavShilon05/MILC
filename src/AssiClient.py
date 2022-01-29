import os
import pickle
from AssiNet import *
import Connection
from Settings import *

class Client:
    def __init__(self, username: str, connection: Connection.Connection, sending=False):
        self.username = username
        self.conn = connection
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
        dst = f"{self.HOME}/{target}"
        if target not in self.conn.get_projects():
            dst += f"/{payload}"
        path = f"{dst}/{basename}"
        self.conn.ssh.exec_command(f"mkdir -p {dst}")

        if os.path.isdir(file):
            self.conn.ssh.exec_command(f"rm -rf {path}")

        self.conn.scp.put(file, path.encode(), True, True)

        send(self.client, pickle.dumps((target, path)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
