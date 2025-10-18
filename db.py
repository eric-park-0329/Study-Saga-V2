
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
    
    # items.image_path
    if not _has_col(x, "items", "image_path"):
        try:
            x.execute("ALTER TABLE items ADD COLUMN image_path TEXT")
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
    CREATE TABLE IF NOT EXISTS study_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        start_time INTEGER,
        end_time INTEGER,
        duration_minutes INTEGER,
        crystals_earned INTEGER DEFAULT 0,
        completed INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        rarity TEXT,
        boost_exp_pct INTEGER DEFAULT 0,
        boost_crystal_pct INTEGER DEFAULT 0,
        description TEXT,
        image_path TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        acquired_at INTEGER,
        equipped INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS achievements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        description TEXT,
        progress INTEGER DEFAULT 0,
        goal INTEGER DEFAULT 100,
        completed INTEGER DEFAULT 0,
        completed_at INTEGER
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

def update_user_settings(uid, nickname, gender, dark_mode, daily_goal):
    c=_c(); x=c.cursor()
    x.execute('''UPDATE users SET nickname=?, gender=?, dark_mode=?, daily_goal_minutes=? 
                 WHERE id=?''', (nickname, gender, dark_mode, daily_goal, uid))
    c.commit(); c.close()

def get_user(uid):
    c=_c(); x=c.cursor()
    x.execute('SELECT * FROM users WHERE id=?', (uid,))
    r=x.fetchone(); c.close()
    return dict(r) if r else None

def update_crystals(uid, amount):
    c=_c(); x=c.cursor()
    x.execute('UPDATE users SET crystals=crystals+? WHERE id=?', (amount, uid))
    c.commit()
    x.execute('SELECT crystals FROM users WHERE id=?', (uid,))
    new_val = x.fetchone()['crystals']
    c.close()
    return new_val

def add_study_session(uid, duration_minutes, crystals_earned):
    c=_c(); x=c.cursor()
    now = int(time.time())
    x.execute('''INSERT INTO study_sessions(user_id, start_time, end_time, duration_minutes, crystals_earned)
                 VALUES (?, ?, ?, ?, ?)''', (uid, now-duration_minutes*60, now, duration_minutes, crystals_earned))
    c.commit(); c.close()

def get_study_sessions(uid, days=7):
    c=_c(); x=c.cursor()
    cutoff = int(time.time()) - days*24*3600
    x.execute('''SELECT * FROM study_sessions WHERE user_id=? AND start_time>=? 
                 ORDER BY start_time DESC''', (uid, cutoff))
    r = [dict(row) for row in x.fetchall()]
    c.close()
    return r

def init_items():
    """Initialize default items in database"""
    c=_c(); x=c.cursor()
    x.execute('SELECT COUNT(*) as cnt FROM items')
    if x.fetchone()['cnt'] == 0:
        items = [
            # Boost items
            ('Magic Book', 'boost', 'bronze', 5, 10, 'A mystical tome that boosts learning', None),
            ('Crystal Staff', 'boost', 'silver', 10, 15, 'Ancient staff radiating power', None),
            ('Golden Crown', 'boost', 'gold', 20, 25, 'Crown of ultimate wisdom', None),
            ('Study Potion', 'consumable', 'bronze', 3, 5, 'Temporary focus boost', None),
            ('Lucky Charm', 'boost', 'silver', 0, 20, 'Increases crystal drops', None),
            ('Epic Scroll', 'boost', 'gold', 25, 20, 'Legendary knowledge scroll', None),
            # Cosmetic items (character customization)
            ('Red Cape', 'cosmetic', 'silver', 0, 0, 'A stylish red cape for heroes', 'attached_assets/assets/cape_red.png'),
            ('Short Hair', 'cosmetic', 'bronze', 0, 0, 'Trendy short hairstyle', 'attached_assets/assets/hairstyle_short.png'),
            ('Basic Hat', 'cosmetic', 'bronze', 0, 0, 'Simple but stylish hat', 'attached_assets/assets/hat_basic.png'),
        ]
        x.executemany('''INSERT INTO items(name, type, rarity, boost_exp_pct, boost_crystal_pct, description, image_path)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', items)
        c.commit()
    c.close()

def get_items(rarity=None):
    c=_c(); x=c.cursor()
    if rarity and rarity != 'all':
        x.execute('SELECT * FROM items WHERE rarity=?', (rarity,))
    else:
        x.execute('SELECT * FROM items')
    r = [dict(row) for row in x.fetchall()]
    c.close()
    return r

def get_inventory(uid):
    c=_c(); x=c.cursor()
    x.execute('''SELECT i.id, i.user_id, i.item_id, i.acquired_at, i.equipped,
                        it.name, it.type, it.rarity, it.boost_exp_pct, it.boost_crystal_pct, it.description
                 FROM inventory i 
                 JOIN items it ON i.item_id = it.id 
                 WHERE i.user_id=?
                 ORDER BY i.acquired_at DESC''', (uid,))
    r = [dict(row) for row in x.fetchall()]
    c.close()
    return r

def add_to_inventory(uid, item_id):
    c=_c(); x=c.cursor()
    now = int(time.time())
    x.execute('INSERT INTO inventory(user_id, item_id, acquired_at) VALUES (?, ?, ?)', (uid, item_id, now))
    c.commit(); c.close()

def get_achievements(uid):
    c=_c(); x=c.cursor()
    x.execute('SELECT * FROM achievements WHERE user_id=? ORDER BY completed DESC, id ASC', (uid,))
    r = [dict(row) for row in x.fetchall()]
    c.close()
    return r

def init_achievements(uid):
    """Initialize default achievements for a user"""
    c=_c(); x=c.cursor()
    x.execute('SELECT COUNT(*) as cnt FROM achievements WHERE user_id=?', (uid,))
    if x.fetchone()['cnt'] == 0:
        achs = [
            (uid, 'First Study', 'Complete your first study session', 0, 1),
            (uid, 'Study Warrior', 'Study for 10 hours total', 0, 600),
            (uid, 'Crystal Collector', 'Earn 1000 crystals', 0, 1000),
            (uid, 'Gacha Master', 'Perform 50 gacha rolls', 0, 50),
            (uid, 'Weekly Hero', 'Complete 5 study sessions in a week', 0, 5),
        ]
        x.executemany('''INSERT INTO achievements(user_id, name, description, progress, goal)
                         VALUES (?, ?, ?, ?, ?)''', achs)
        c.commit()
    c.close()

def update_achievement(uid, name, increment=1):
    """Update achievement progress and mark as completed if goal reached"""
    c=_c(); x=c.cursor()
    
    # Get current achievement
    x.execute('SELECT * FROM achievements WHERE user_id=? AND name=?', (uid, name))
    ach = x.fetchone()
    
    if not ach:
        c.close()
        return
    
    ach = dict(ach)
    new_progress = ach['progress'] + increment
    
    # Check if completed
    if new_progress >= ach['goal'] and not ach['completed']:
        now = int(time.time())
        x.execute('''UPDATE achievements SET progress=?, completed=1, completed_at=? 
                     WHERE user_id=? AND name=?''', (new_progress, now, uid, name))
    else:
        x.execute('''UPDATE achievements SET progress=? 
                     WHERE user_id=? AND name=?''', (new_progress, uid, name))
    
    c.commit()
    c.close()

def get_total_study_minutes(uid):
    """Get total study minutes for user"""
    c=_c(); x=c.cursor()
    x.execute('SELECT SUM(duration_minutes) as total FROM study_sessions WHERE user_id=?', (uid,))
    result = x.fetchone()
    c.close()
    return result['total'] or 0

def get_total_crystals_earned(uid):
    """Get total crystals earned from study sessions"""
    c=_c(); x=c.cursor()
    x.execute('SELECT SUM(crystals_earned) as total FROM study_sessions WHERE user_id=?', (uid,))
    result = x.fetchone()
    c.close()
    return result['total'] or 0

def set_achievement_progress(uid, name, new_progress):
    """Set achievement progress to specific value and mark completed if goal reached"""
    c=_c(); x=c.cursor()
    
    # Get current achievement
    x.execute('SELECT * FROM achievements WHERE user_id=? AND name=?', (uid, name))
    ach = x.fetchone()
    
    if not ach:
        c.close()
        return
    
    ach = dict(ach)
    
    # Check if should be completed
    if new_progress >= ach['goal'] and not ach['completed']:
        now = int(time.time())
        x.execute('''UPDATE achievements SET progress=?, completed=1, completed_at=? 
                     WHERE user_id=? AND name=?''', (new_progress, now, uid, name))
    else:
        x.execute('''UPDATE achievements SET progress=? 
                     WHERE user_id=? AND name=?''', (new_progress, uid, name))
    
    c.commit()
    c.close()
