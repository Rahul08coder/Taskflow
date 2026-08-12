# =====================================================
# Password Hashing & Session Token Utilities
# =====================================================

"""
Password hashing and session-token helpers.

Deliberately uses only Python's standard library (hashlib, os, secrets) —
no bcrypt/passlib — to avoid the wheel-availability problems seen earlier
with packages that need C extensions on newer Python versions.

Hashing scheme: PBKDF2-HMAC-SHA256, 100,000 iterations, random 16-byte salt.
Stored format: "<salt_hex>$<hash_hex>"
"""

import hashlib
import os
import secrets

# Number of iterations for PBKDF2 - higher = more secure but slower
PBKDF2_ITERATIONS = 100_000

# Hash plaintext password using PBKDF2 with random salt
def hash_password(password: str) -> str:
    """Hash a plaintext password. Never store the raw password anywhere."""
    salt = os.urandom(16)  # Generate random 16-byte salt
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"  # Store salt and hash together

# Verify password against stored hash
def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plaintext password against a hash produced by hash_password()."""
    if not stored_hash or "$" not in stored_hash:
        return False
    salt_hex, hash_hex = stored_hash.split("$", 1)  # Split salt and hash
    try:
        salt = bytes.fromhex(salt_hex)  # Convert salt from hex
    except ValueError:
        return False
    # Hash the provided password with same salt and compare
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return derived.hex() == hash_hex

# Generate random session token for authentication
def generate_session_token() -> str:
    """A random, unguessable session token — no expiry baked in."""
    return secrets.token_hex(32)  # 64 character hex string (32 bytes)