import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

def get_encryption_key():
    """Get or generate encryption key from environment variable."""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    
    # If key is a base64 string, decode it
    try:
        return base64.urlsafe_b64decode(key.encode())
    except:
        # If not base64, derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'meeting_schedule_salt',
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(key.encode()))

def encrypt_token(token: str) -> str:
    """Encrypt a token using AES-256 (Fernet)."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    return encrypted.decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token."""
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_token.encode())
    return decrypted.decode()