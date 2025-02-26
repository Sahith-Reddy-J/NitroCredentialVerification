import socket
import json

def sign_skill(data: dict) -> dict:
    try:
        with socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) as sock:
            sock.connect((16, 5000))  # CID 16 for parent->enclave
            
            # Send complete JSON
            payload = json.dumps(data, ensure_ascii=False)
            print(f"Sending payload: {payload}")
            sock.sendall(payload.encode('utf-8'))
            
            # Receive full response
            response = b''
            while True:
                chunk = sock.recv(512)
                print(f"Received chunk: {chunk}")
                if not chunk:
                    break
                response += chunk
                # Check for JSON termination
                if response.count(b'{') == response.count(b'}'):
                    break
            print(f"Full response: {response}")
            return json.loads(response.decode('utf-8'))
            
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        raise
    except Exception as e:
        print(f"VSOCK Communication Error: {str(e)}")
        raise

def get_public_key() -> str:
    try:
        with socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) as sock:
            sock.connect((16, 5000))
            sock.sendall(json.dumps({"action": "get_pubkey"}).encode())
            
            response = b''
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
                if response.endswith(b'-----END PUBLIC KEY-----\n'):
                    break
            
            return response.decode('utf-8')
    except Exception as e:
        print(f"Public Key Fetch Error: {str(e)}")
        raise