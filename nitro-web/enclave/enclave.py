import socket
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from threading import Lock

class SkillSigner:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.nonce_lock = Lock()
        self.nonce_counter = 0

    def _generate_nonce(self) -> str:
        with self.nonce_lock:
            self.nonce_counter += 1
            return f"{datetime.utcnow().isoformat()}|{self.nonce_counter}"

    def get_public_key(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def sign_skill(self, student_id: str, skill: str) -> dict:
        nonce = self._generate_nonce()
        payload = f"{student_id}|{skill}|{nonce}".encode()
        
        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return {
            "signature": signature.hex(),
            "nonce": nonce
        }

def vsock_server():
    signer = SkillSigner()
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, 5000))
    sock.listen(5)
    
    print("Enclave ready for signing operations...")
    
    while True:
        conn, _ = sock.accept()
        try:
            data = conn.recv(1024)
            if data:
                request = json.loads(data)
                if request.get("action") == "get_pubkey":
                    response = signer.get_public_key()
                else:
                    response = signer.sign_skill(
                        request["student_id"],
                        request["skill"]
                    )
                conn.sendall(json.dumps(response).encode())
        except Exception as e:
            conn.sendall(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

if __name__ == "__main__":
    vsock_server()