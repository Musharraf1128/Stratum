"""
Crypto utility for encrypting/decrypting API keys at rest.
Uses Fernet symmetric encryption from the `cryptography` library.

The server key is auto-generated on first run and stored in `.stratum_key`.
This file should be gitignored and never committed.
"""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_KEY_FILE = Path(".stratum_key")
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Load or create the server encryption key."""
    global _fernet
    if _fernet is not None:
        return _fernet

    if _KEY_FILE.exists():
        key = _KEY_FILE.read_bytes().strip()
    else:
        key = Fernet.generate_key()
        _KEY_FILE.write_bytes(key)
        # Restrict permissions (owner-only)
        try:
            os.chmod(_KEY_FILE, 0o600)
        except OSError:
            pass  # Windows doesn't support chmod the same way

    _fernet = Fernet(key)
    return _fernet


def encrypt_key(plain_text: str) -> str:
    """Encrypt a plain-text API key → base64-encoded encrypted string."""
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_key(encrypted_text: str) -> str:
    """Decrypt an encrypted API key → plain-text string."""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Failed to decrypt API key — server key may have changed")
