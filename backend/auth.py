import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt

SECRET = "W3SECURE_SECRET_CHANGE_ME"
ALGO = "HS256"

def hash_password(password: str):
    return bcrypt.hash(password)

def verify_password(password: str, password_hash: str):
    return bcrypt.verify(password, password_hash)

def create_token(user_id: int, username: str, role: str):
    payload = {
        "sub": username,
        "uid": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str):
    return jwt.decode(token, SECRET, algorithms=[ALGO])
