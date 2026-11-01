"""Authentication and session token handling for Hotel Analytics API."""
import hmac
import hashlib
import base64
import json
import time
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from modules import auth, config

SECRET_KEY = "hotel-analytics-secure-secret-key-2026"
security_scheme = HTTPBearer(auto_error=False)

def create_access_token(user_data: dict, expires_in_seconds: int = 86400 * 7) -> str:
    """Create a lightweight HMAC-SHA256 signed bearer token."""
    payload = {
        "sub": user_data.get("username"),
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "role": user_data.get("role"),
        "exp": int(time.time()) + expires_in_seconds
    }
    header_b64 = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    msg = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        msg = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
        
        # Add padding back if necessary
        pad = len(sig_b64) % 4
        if pad:
            sig_b64 += "=" * (4 - pad)
        given_sig = base64.urlsafe_b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, given_sig):
            return None
            
        pad_p = len(payload_b64) % 4
        if pad_p:
            payload_b64 += "=" * (4 - pad_p)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Optional[dict]:
    if not credentials:
        # Default demo user if token is not sent for read operations
        return {"sub": "guest", "name": "Guest Analyst", "role": "User", "email": "guest@hotelanalytics.com"}
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    return payload

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Administrator permissions required")
    return user

