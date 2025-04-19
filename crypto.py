import os
import base64
import hashlib
import logging
from typing import Optional
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from config import ARGON2_PARAMS, SALT_FILE, MASTER_HASH_FILE

logger = logging.getLogger(__name__)


class Crypto:
    """Handles encryption, decryption, and master password verification."""

    def __init__(self):
        self.ph = PasswordHasher(
            time_cost=ARGON2_PARAMS["time_cost"],
            memory_cost=ARGON2_PARAMS["memory_cost"],
            parallelism=ARGON2_PARAMS["parallelism"],
            hash_len=ARGON2_PARAMS["hash_len"]
        )

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        """Derives an encryption key from the master password and salt."""
        return self.ph.hash(master_password.encode(), salt=salt).encode()[:32]

    def encrypt_password(self, password: str, key: bytes) -> str:
        """Encrypts a password using AES-256-GCM."""
        try:
            iv = os.urandom(12)
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_password = encryptor.update(password.encode()) + encryptor.finalize()
            return base64.b64encode(iv + encryptor.tag + encrypted_password).decode()
        except Exception as e:
            raise RuntimeError(f"Encryption failed: {e}")

    def decrypt_password(self, encrypted_password: str, key: bytes) -> str:
        """Decrypts an encrypted password using AES-256-GCM."""
        try:
            data = base64.b64decode(encrypted_password)
            iv, tag, encrypted_password = data[:12], data[12:28], data[28:]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return (decryptor.update(encrypted_password) + decryptor.finalize()).decode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Decryption failed: {e}")

    def save_salt(self, salt: bytes):
        """Saves the salt with a hash for integrity checking."""
        salt_hash = hashlib.sha256(salt).hexdigest()
        with open(SALT_FILE, "wb") as f:
            f.write(salt + salt_hash.encode())

    def get_salt(self) -> bytes:
        """Retrieves or generates a salt with integrity verification."""
        try:
            if not os.path.exists(SALT_FILE):
                salt = os.urandom(16)
                self.save_salt(salt)
                return salt
            with open(SALT_FILE, "rb") as f:
                data = f.read()
                if len(data) < 80:
                    logger.error(f"Salt file too short: {len(data)} bytes")
                    salt = os.urandom(16)
                    self.save_salt(salt)
                    return salt
                salt, stored_hash = data[:16], data[16:].decode('utf-8')
                if hashlib.sha256(salt).hexdigest() != stored_hash:
                    logger.error("Salt file corrupted")
                    salt = os.urandom(16)
                    self.save_salt(salt)
                    return salt
            return salt
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Salt file error: {e}")
            salt = os.urandom(16)
            self.save_salt(salt)
            return salt

    def hash_master_password(self, master_password: str, salt: bytes) -> str:
        """Hashes the master password using Argon2."""
        return self.ph.hash(master_password.encode(), salt=salt)

    def save_master_hash(self, master_password: str, salt: bytes):
        """Saves the hash of the master password."""
        master_hash = self.hash_master_password(master_password, salt)
        with open(MASTER_HASH_FILE, "w") as f:
            f.write(master_hash)

    def verify_master_password(self, master_password: str, salt: bytes) -> bool:
        """Verifies the master password against the stored hash."""
        if not os.path.exists(MASTER_HASH_FILE):
            self.save_master_hash(master_password, salt)
            return True
        try:
            with open(MASTER_HASH_FILE, "r") as f:
                stored_hash = f.read()
            self.ph.verify(stored_hash, master_password.encode())
            return True
        except Exception as e:
            logger.error(f"Master password verification failed: {e}")
            return False