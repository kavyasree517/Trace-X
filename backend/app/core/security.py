"""Cryptographic utilities, address canonicalization, and access token helpers."""

import hashlib
import os
import secrets
from datetime import UTC, datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from eth_utils.address import is_address, to_checksum_address

from app.core.config import get_settings


def canonicalize_address(address: str) -> str:
    """Validate and convert an address to canonical EIP-55 checksum format."""
    clean_addr = address.strip()
    if not is_address(clean_addr):
        raise ValueError(f"Invalid Ethereum address: {address}")
    return str(to_checksum_address(clean_addr))


def generate_case_reference(counter: int) -> str:
    """Generate a standard case reference formatted as TX-YYYY-NNNNNN."""
    year = datetime.now(UTC).year
    return f"TX-{year}-{counter:06d}"


def generate_access_token() -> str:
    """Generate a random 128-bit hex access token."""
    return secrets.token_hex(16)


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of a secret access token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_encryption_key() -> bytes:
    settings = get_settings()
    # Derive 256-bit key from settings secret
    return hashlib.sha256(settings.APP_SECRET_KEY.encode("utf-8")).digest()


def encrypt_text(plaintext: str) -> str:
    """Encrypt sensitive plaintext using AES-256-GCM with a random nonce."""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return f"{nonce.hex()}:{ciphertext.hex()}"


def decrypt_text(payload: str) -> str:
    """Decrypt AES-256-GCM ciphertext payload formatted as nonce:ciphertext."""
    parts = payload.split(":", 1)
    if len(parts) != 2:
        raise ValueError("Invalid encrypted payload format")
    nonce = bytes.fromhex(parts[0])
    ciphertext = bytes.fromhex(parts[1])
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode("utf-8")
