import secrets, time
from .db import _get_conn

try:
    import bcrypt
except Exception:
    bcrypt = None

def _hash(p: str) -> bytes:
    if bcrypt is None: return ("plain:"+p).encode("utf-8")
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt(rounds=12))

def _check(p: str, h: bytes) -> bool:
    if bcrypt is None: return h == ("plain:"+p).encode("utf-8")
    try: return bcrypt.checkpw(p.encode("utf-8"), h)
    except Exception: return False

def register(username: str, password: str):
    if not username or not password: return False, "missing fields"
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        con.close(); return False, "username taken"
    hp = _hash(password)
    cur.execute("INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
                (username, hp, int(time.time())))
    con.commit(); con.close()
    return True, "ok"

def login(username: str, password: str):
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row: con.close(); return False, "invalid"
    uid, ph = row
    if isinstance(ph, str): ph = ph.encode("utf-8")
    ok = _check(password, ph)
    if not ok: con.close(); return False, "invalid"
    tok = secrets.token_hex(32)
    cur.execute("INSERT INTO sessions(token, user_id, created_at) VALUES (?,?,?)",(tok,uid,int(time.time())))
    con.commit(); con.close()
    return True, tok
