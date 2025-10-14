import time, secrets
from typing import Tuple
from .db import _get_conn

try:
    import bcrypt
except Exception:
    bcrypt = None

PW_COST = 12

def _hash_password(plain: str) -> bytes:
    if bcrypt is None:
        return ("plain:" + plain).encode("utf-8")
    salt = bcrypt.gensalt(rounds=PW_COST)
    return bcrypt.hashpw(plain.encode("utf-8"), salt)

def _verify_password(plain: str, hashed: bytes) -> bool:
    if bcrypt is None:
        return hashed == ("plain:" + plain).encode("utf-8")
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed)
    except Exception:
        return False

def register(username: str, password: str) -> Tuple[bool,str]:
    if not username or not password:
        return False, "missing fields"
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        con.close(); return False, "username taken"
    hp = _hash_password(password)
    cur.execute("INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
                (username, hp, int(time.time())))
    con.commit(); con.close()
    return True, "ok"

def login(username: str, password: str) -> Tuple[bool,str]:
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        con.close(); return False, "invalid credentials"
    uid, ph = row[0], row[1]
    ok = _verify_password(password, ph if isinstance(ph,(bytes,bytearray)) else ph.encode("utf-8"))
    if not ok:
        con.close(); return False, "invalid credentials"
    token = secrets.token_hex(32)
    cur.execute("INSERT INTO sessions(token, user_id, created_at) VALUES (?,?,?)",
                (token, uid, int(time.time())))
    con.commit(); con.close()
    return True, token
