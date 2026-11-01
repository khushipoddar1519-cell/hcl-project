"""Simple file-based authentication (salted SHA-256 hashes)."""
import hashlib
import json
import secrets
from . import config

DEMO_ACCOUNTS = {
    "user": ("khushi", "user123"),
    "admin": ("admin", "admin123"),
}


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _make_user(name, email, role, password):
    salt = secrets.token_hex(8)
    return {"name": name, "email": email, "role": role, "salt": salt, "hash": _hash(password, salt)}


def _seed():
    users = {
        "khushi": _make_user("Khushi Poddar", "khushi@hotelanalytics.com", "User", "user123"),
        "admin": _make_user("Admin", "admin@hotelanalytics.com", "Administrator", "admin123"),
    }
    save_users(users)
    return users


def load_users() -> dict:
    try:
        if config.USERS_JSON.exists():
            return json.loads(config.USERS_JSON.read_text())
    except Exception:
        pass
    return _seed()


def save_users(users: dict):
    config.USERS_JSON.write_text(json.dumps(users, indent=2))


def authenticate(identifier: str, password: str):
    """Return (username, user_dict) or None. Accepts username or e-mail."""
    identifier = (identifier or "").strip().lower()
    if not identifier or not password:
        return None
    for uname, u in load_users().items():
        if identifier in (uname.lower(), u.get("email", "").lower()):
            if secrets.compare_digest(_hash(password, u["salt"]), u["hash"]):
                return uname, {k: v for k, v in u.items() if k not in ("salt", "hash")} | {"username": uname}
    return None


def add_user(username, name, email, role, password):
    users = load_users()
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    if username in users:
        return False, "That username already exists."
    users[username] = _make_user(name or username.title(), email, role, password)
    save_users(users)
    return True, "User created."


def delete_user(username):
    users = load_users()
    if username in users:
        admins = [u for u, v in users.items() if v["role"] == "Administrator"]
        if users[username]["role"] == "Administrator" and len(admins) <= 1:
            return False, "You cannot delete the last administrator."
        users.pop(username)
        save_users(users)
        return True, "User deleted."
    return False, "User not found."


def set_password(username, new_password):
    users = load_users()
    if username not in users:
        return False
    salt = secrets.token_hex(8)
    users[username]["salt"] = salt
    users[username]["hash"] = _hash(new_password, salt)
    save_users(users)
    return True


def reset_password(identifier, recovery_key, new_password):
    if recovery_key.strip() != config.RECOVERY_KEY:
        return False, "Invalid recovery key."
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    identifier = identifier.strip().lower()
    for uname, u in load_users().items():
        if identifier in (uname.lower(), u.get("email", "").lower()):
            set_password(uname, new_password)
            return True, "Password updated. You can log in now."
    return False, "No account found with that username / e-mail."
