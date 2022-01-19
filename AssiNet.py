import socket

PORT = 5926

def recv(conn: socket.socket) -> bytes:
    ss = conn.recv(16).decode()
    size = int(ss)  # 16 because yoav is mentally retarded
    return conn.recv(size)

def send(conn: socket.socket, msg: bytes):
    size = f"{len(msg):016}" # 16 because yoav is mentally retarded
    conn.send(size.encode() + msg)
