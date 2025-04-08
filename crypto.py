import os
import base64
import ctypes
import shutil
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from argon2.low_level import hash_secret_raw, Type

def derive_key(master_password: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=master_password.encode(),
        salt=salt,
        time_cost=4,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        type=Type.ID
    )

# Шифрование пароля
def encrypt_password(password: str, key: bytes) -> str:
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_password = encryptor.update(password.encode()) + encryptor.finalize()
    return base64.b64encode(iv + encryptor.tag + encrypted_password).decode()

# Дешифрование пароля
def decrypt_password(encrypted_password: str, key: bytes) -> str:
    data = base64.b64decode(encrypted_password)
    iv, tag, encrypted_password = data[:12], data[12:28], data[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_password) + decryptor.finalize()

# Безопасное удаление пароля из памяти
def secure_delete(data: bytes):
    try:
        ptr = ctypes.create_string_buffer(data)
        ctypes.memset(ptr, 0, len(data))
    except Exception:
        pass

def clear_password(password: str):
    try:
        password_bytes = password.encode()
        secure_delete(password_bytes)
        password = " " * len(password)
        shutil.get_terminal_size()
    except Exception:
        pass