import hashlib
users = {}
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
def register_user(username: str, password: str) -> bool:
    if username in users:
        return False
    users[username] = hash_password(password)
    return True
def login_user(username: str, password: str) -> bool:
    if username in users and users[username] == hash_password(password):
        return True
    return False
