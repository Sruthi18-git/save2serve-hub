# [file name]: security.py
# [file location]: root folder
# [Purpose]: Password hashing for security

import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

# Test
if __name__ == "__main__":
    test_pw = "test123"
    hashed = hash_password(test_pw)
    print(f"Original: {test_pw}")
    print(f"Hashed: {hashed}")
    print(f"Verification: {verify_password(test_pw, hashed)}")
    print(f"Wrong password: {verify_password('wrong', hashed)}")