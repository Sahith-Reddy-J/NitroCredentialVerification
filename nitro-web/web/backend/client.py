import socket
import json

def sign_skill(data: dict) -> dict:
    with socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) as sock:
        sock.connect((16, 5000))
        sock.sendall(json.dumps(data).encode())
        return json.loads(sock.recv(512).decode())

def get_public_key() -> str:
    with socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) as sock:
        sock.connect((16, 5000))
        sock.sendall(json.dumps({"action": "get_pubkey"}).encode())
        return sock.recv(1024).decode()