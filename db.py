
import sqlite3, os, time, hashlib, secrets

DB_PATH=os.environ.get('STUDYSAGA_DB','studysaga.sqlite3')

def _c():
    c=sqlite3.connect(DB_PATH)
    c.row_factory=sqlite3.Row
    return c

def _has_col(cur, table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r["name"]==col for r in cur.fetchall())

def _migrate():
    c=_c(); x=c.cursor()
    # sessions.expires_at
    x.execute("PRAGMA table_info(sessions)")
    cols=[r["name"] for r in x.fetchall()]
    if "expires_at" not in cols:
        try:
            x.execute("ALTER TABLE sessions ADD COLUMN expires_at INTEGER")
            c.commit()
        except sqlite3.OperationalError:
            pass
    # users schema: ensure columns exist
    need_cols=[("nickname","TEXT DEFAULT ''"),
               ("gender","TEXT DEFAULT 'female'"),
               ("crystals","INTEGER DEFAULT 100"),
               ("dark_mode","INTEGER DEFAULT 0"),
               ("daily_goal_minutes","INTEGER DEFAULT 60")]
    x.execute("PRAGMA table_info(users)")
    ucols=[r["name"] for r in x.fetchall()]
    for name, decl in need_cols:
        if name not in ucols:
            try:
                x.execute(f"ALTER TABLE users ADD COLUMN {name} {decl}")
                c.commit()
            except sqlite3.OperationalError:
                pass
    c.close()

def bootstrap():
    c=_c(); x=c.cursor()
    x.executescript('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password_hash TEXT,
        nickname TEXT DEFAULT '',
        gender TEXT DEFAULT 'female',
        crystals INTEGER DEFAULT 100,
        dark_mode INTEGER DEFAULT 0,
        daily_goal_minutes INTEGER DEFAULT 60
    );
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER,
        expires_at INTEGER
    );
    ''')
    c.commit(); c.close()
    _migrate()

def _hash(p): return hashlib.sha256(('studysaga'+p).encode()).hexdigest()

def create_user(email,pw):
    c=_c(); x=c.cursor()
    try:
        x.execute('INSERT INTO users(email,password_hash) VALUES (?,?)',(email,_hash(pw)))
        c.commit(); ok=True
    except sqlite3.IntegrityError:
        ok=False
    c.close(); return ok

def auth_user(email,pw):
    c=_c(); x=c.cursor(); x.execute('SELECT * FROM users WHERE email=?',(email,)); r=x.fetchone(); c.close()
    if not r or r['password_hash']!=_hash(pw): return None
    return dict(r)

def issue_session(uid,hours=720):
    t=secrets.token_urlsafe(24); exp=int(time.time())+hours*3600
    c=_c(); x=c.cursor()
    # insert with expires_at regardless (column is ensured in _migrate)
    x.execute('INSERT OR REPLACE INTO sessions(token,user_id,expires_at) VALUES (?,?,?)',(t,uid,exp))
    c.commit(); c.close(); return t

def set_gender(uid, gender):
    c=_c(); x=c.cursor()
    x.execute('UPDATE users SET gender=? WHERE id=?',(gender,uid))
    c.commit(); c.close()
