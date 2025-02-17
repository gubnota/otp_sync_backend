import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class AES256Cipher:
    def __init__(self, secret_phrase):
        self.secret_phrase = secret_phrase.encode()

    def _derive_key(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=65536,  # Match Kotlin's iteration count
            backend=default_backend()
        )
        return kdf.derive(self.secret_phrase)

    def encrypt(self, plaintext):
        salt = os.urandom(16)
        key = self._derive_key(salt)
        nonce = os.urandom(12)  # GCM typically uses a 12-byte nonce
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return base64.b64encode(salt + nonce + ciphertext + encryptor.tag).decode('utf-8')

    def decrypt(self, encrypted_text):
        encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        tag = encrypted_data[-16:]
        ciphertext = encrypted_data[28:-16]
        key = self._derive_key(salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode('utf-8')
