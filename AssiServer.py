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


def handle_client(conn: socket.socket):
    name, file = pickle.loads(recv(conn))
    send(NAMES[name], file.encode())

while True:
    client, client_ip = server.accept()
    print(f"{client_ip} connected")
    name = recv(client).decode()
    if name != "SEND":
        NAMES[name] = client
    thread = threading.Thread(target=handle_client, args=(client,))
    thread.start()