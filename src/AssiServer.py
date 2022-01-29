import socket
import threading
import pickle

from AssiNet import *

SERVER = socket.gethostbyname(socket.gethostname())

ADDR = (SERVER, PORT)

NAMES: dict[str, socket.socket] = {}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

with open("/home/assi/assi-pkg/projects.txt") as f:
    folders = f.read().split("\n")
    projects = {}
    for f in folders:
        if f == "": continue
        split = f.split(":")
        projectname = split[0]
        users = split[1].split(',')
        projects[projectname] = users


def on_sendto(conn: socket.socket):
    msg = recv(conn)
    if msg == "!stop":
        send(conn, b"!stop")
    else:
        target, file = pickle.loads(msg)
        if target in projects.keys():
            for name in projects[target]:
                send(NAMES[name], file.encode())
        else:
            send(NAMES[target], file.encode())

while True:
    client, client_ip = server.accept()
    print(f"{client_ip} connected")
    name = recv(client).decode()
    if name != "SEND":
        NAMES[name] = client
    else:
        thread = threading.Thread(target=on_sendto, args=(client,))
        thread.start()