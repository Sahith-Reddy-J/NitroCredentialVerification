from client import get_public_key

pubkey = get_public_key()
with open("../public_key.pem", "w") as f:
    f.write(pubkey)