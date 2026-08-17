import hashlib
import hmac
import secrets
import json
import base64
import time
from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.registration import Admin
from app.config import settings

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2_sha256${salt}${key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        if hashed.startswith("pbkdf2_sha256$"):
            _, salt, key_hex = hashed.split("$", 2)
            check_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hmac.compare_digest(check_key.hex(), key_hex)
        elif hashed.startswith("pbkdf2:sha256:"):
            # Werkzeug legacy format
            parts = hashed.split("$")
            iterations = int(parts[0].split(":")[-1])
            salt = parts[1]
            key_hex = parts[2]
            check_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
            return hmac.compare_digest(check_key.hex(), key_hex)
        elif "$" in hashed:
            parts = hashed.split("$")
            salt = parts[0]
            key_hex = parts[1]
            check_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hmac.compare_digest(check_key.hex(), key_hex)
        else:
            return password == hashed
    except Exception:
        return False

def generate_admin_token(admin_id: int, rollnumber: str, role: str) -> str:
    payload = {
        "admin_id": admin_id,
        "rollnumber": rollnumber,
        "role": role,
        "exp": int(time.time()) + (86400 * 7) # 7 days
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"

def verify_admin_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        padded_b64 = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_b64).decode('utf-8'))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

def get_current_admin(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Admin:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:].strip()
        
    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
        
    admin = db.query(Admin).filter(Admin.id == payload.get("admin_id")).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin user not found")
        
    return admin

def seed_super_admin(db: Session):
    try:
        superadmin = db.query(Admin).filter(Admin.role == 'superadmin').first()
        if not superadmin:
            default_roll = settings.DEFAULT_SUPERADMIN_ROLL
            default_pass = settings.DEFAULT_SUPERADMIN_PASS
            new_super = Admin(
                rollnumber=default_roll,
                role='superadmin',
                password_hash=hash_password(default_pass)
            )
            db.add(new_super)
            db.commit()
            print(f"[AUTH] Super Admin initialized: Roll={default_roll}")
    except Exception as e:
        print(f"[AUTH] Error seeding super admin: {e}")
