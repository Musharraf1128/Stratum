"""
Crypto utility for encrypting/decrypting API keys at rest.
Uses Fernet symmetric encryption from the `cryptography` library.

Key source priority:
  1. STRATUM_SECRET_KEY environment variable
  2. .stratum_key file (auto-generated in dev mode)

The .stratum_key file should be gitignored and never committed.
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

    # Priority 1: environment variable
    env_key = os.getenv("STRATUM_SECRET_KEY")
    if env_key:
        key = env_key.encode("utf-8")
    elif _KEY_FILE.exists():
        # Priority 2: key file (dev mode fallback)
        key = _KEY_FILE.read_bytes().strip()
    else:
        # Auto-generate key file for dev mode
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
