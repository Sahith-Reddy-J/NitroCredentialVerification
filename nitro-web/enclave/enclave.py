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
            print("generating nonce")
            return f"{datetime.utcnow().isoformat()}|{self.nonce_counter}"

    def get_public_key(self) -> str:
        print("getting public key")
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def sign_skill(self, student_id: str, skill: str) -> dict:
        nonce = self._generate_nonce()
        payload = f"{student_id}|{skill}|{nonce}".encode()
        print("signing skill")
        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("signature generated")
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
            # Read complete JSON data
            print("Waiting for data...")
            data = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                # Check for balanced JSON braces
                if data.count(b'{') == data.count(b'}') and data.count(b'{') > 0:
                    break
            
            if not data:
                continue

            print(f"Received raw data: {data.decode()}")
            request = json.loads(data.decode())
            
            if request.get("action") == "get_pubkey":
                response = signer.get_public_key()
            else:
                response = signer.sign_skill(
                    request["student_id"],
                    request["skill"]
                )
            
            conn.sendall(json.dumps(response).encode())
            
        except json.JSONDecodeError as e:
            print(f"JSON Error: {str(e)}")
            conn.sendall(json.dumps({"error": "Invalid JSON format"}).encode())
        except Exception as e:
            print(f"Processing Error: {str(e)}")
            conn.sendall(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

if __name__ == "__main__":
    vsock_server()