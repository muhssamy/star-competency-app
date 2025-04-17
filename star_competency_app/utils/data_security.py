# star_competency_app/utils/data_security.py
import base64
import hashlib
import os

from cryptography.fernet import Fernet

from star_competency_app.config.settings import get_settings

settings = get_settings()


def get_encryption_key():
    """Get or generate the encryption key."""
    key = settings.ENCRYPTION_KEY
    if not key:
        # Generate a key if not provided
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return key


def encrypt_sensitive_data(data):
    """Encrypt sensitive data."""
    if not data:
        return None

    key = get_encryption_key()
    cipher_suite = Fernet(key.encode())
    encrypted_data = cipher_suite.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()


def decrypt_sensitive_data(encrypted_data):
    """Decrypt sensitive data."""
    if not encrypted_data:
        return None

    key = get_encryption_key()
    cipher_suite = Fernet(key.encode())
    decrypted_data = cipher_suite.decrypt(base64.urlsafe_b64decode(encrypted_data))
    return decrypted_data.decode()


def hash_identifier(identifier):
    """Hash an identifier for logging (one-way)."""
    salt = settings.HASH_SALT.encode()
    return hashlib.sha256(salt + str(identifier).encode()).hexdigest()
