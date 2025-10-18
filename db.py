
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
               ("daily_goal_minutes","INTEGER DEFAULT 60"),
               ("exp","INTEGER DEFAULT 0"),
               ("level","INTEGER DEFAULT 1")]
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


def ensure_admin_user():
    """Create 'admin' user with password 'admin' if missing, and set crystals to 1000."""
    c=_c(); x=c.cursor()
    # find exact email 'admin'
    x.execute('SELECT id FROM users WHERE email=?', ('admin',))
    r = x.fetchone()
    if not r:
        # create admin
        x.execute('INSERT INTO users(email,password_hash,gender,crystals) VALUES (?,?,?,?)',
                  ('admin', _hash('admin'), 'male', 1000))
        c.commit()
    else:
        # update crystals to 1000
        x.execute('UPDATE users SET crystals=? WHERE id=?', (1000, r['id']))
        c.commit()
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
        daily_goal_minutes INTEGER DEFAULT 60,
        exp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
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
    CREATE TABLE IF NOT EXISTS active_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        activated_at INTEGER,
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


def set_crystals(uid, value:int):
    c=_c(); x=c.cursor()
    x.execute('UPDATE users SET crystals=? WHERE id=?',(value, uid))
    c.commit(); c.close()
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


def ensure_item_by_name(name, type_, rarity, bx, bc, desc, img):
    c=_c(); x=c.cursor()
    x.execute('SELECT id FROM items WHERE name=?', (name,))
    row = x.fetchone()
    if not row:
        x.execute('INSERT INTO items(name, type, rarity, boost_exp_pct, boost_crystal_pct, description, image_path) VALUES (?,?,?,?,?,?,?)',
                  (name, type_, rarity, bx, bc, desc, img))
        c.commit()
    c.close()


def init_items():
    """Ensure base items exist (5 per rarity)."""
    try:
        ensure_item_by_name('Focus Tea', 'consumable', 'bronze', 6, 5, 'A warm brew that helps you lock in for a bit.', '')
        ensure_item_by_name('Pomodoro Timer', 'consumable', 'bronze', 8, 3, 'Tick-tock boost to short sprints.', '')
        ensure_item_by_name('Sticky Notes Storm', 'consumable', 'bronze', 5, 7, 'Notes everywhere—your brain loves it.', '')
        ensure_item_by_name('Desk Plant Buddy', 'consumable', 'bronze', 7, 6, 'Tiny chlorophyll, tiny productivity bump.', '')
        ensure_item_by_name('Blue Light Glasses', 'consumable', 'bronze', 9, 4, 'Less eye strain, more brain gain.', '')
        ensure_item_by_name('Midnight Oil', 'consumable', 'silver', 14, 10, 'Burn it wisely: longer focus streaks.', '')
        ensure_item_by_name('Flashcard Frenzy', 'consumable', 'silver', 16, 12, 'Your recall just found second gear.', '')
        ensure_item_by_name('Study Lo-Fi Mix', 'consumable', 'silver', 15, 14, 'Beats to level up your grind.', '')
        ensure_item_by_name('Mind Palace Kit', 'consumable', 'silver', 18, 11, 'Organize thoughts like royalty.', '')
        ensure_item_by_name('Habit Tracker Pro', 'consumable', 'silver', 13, 15, 'Consistency pays dividends.', '')
        ensure_item_by_name('Quantum Coffee', 'consumable', 'gold', 28, 22, 'Superposition of alert + calm.', '')
        ensure_item_by_name('Zen Master Candle', 'consumable', 'gold', 25, 24, 'Tranquility with turbocharged focus.', '')
        ensure_item_by_name('Lightning Keyboard', 'consumable', 'gold', 30, 20, 'Your WPM just crits.', '')
        ensure_item_by_name('Flow State Serum', 'consumable', 'gold', 27, 25, 'Slip into the zone on command.', '')
        ensure_item_by_name('Champion’s Checklist', 'consumable', 'gold', 26, 23, 'Plan it. Crush it. Repeat.', '')
    except Exception as e:
        print('init_items error', e)

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
    """Initialize default achievements for a user - adds any missing achievements"""
    c=_c(); x=c.cursor()
    
    # Get existing achievement names for this user
    x.execute('SELECT name FROM achievements WHERE user_id=?', (uid,))
    existing_names = set(row['name'] for row in x.fetchall())
    
    # Define all achievements
    all_achs = [
        # Beginner achievements (5)
        (uid, 'First Study', 'Complete your first study session', 0, 1),
        (uid, 'Getting Started', 'Study for 30 minutes total', 0, 30),
        (uid, 'First Roll', 'Perform your first gacha roll', 0, 1),
        (uid, 'First Item', 'Acquire your first item', 0, 1),
        (uid, 'Quick Start', 'Complete 3 study sessions', 0, 3),
        
        # Study Time achievements (10)
        (uid, 'Study Rookie', 'Study for 1 hour total', 0, 60),
        (uid, 'Study Novice', 'Study for 2 hours total', 0, 120),
        (uid, 'Study Apprentice', 'Study for 5 hours total', 0, 300),
        (uid, 'Study Warrior', 'Study for 10 hours total', 0, 600),
        (uid, 'Study Expert', 'Study for 20 hours total', 0, 1200),
        (uid, 'Study Master', 'Study for 50 hours total', 0, 3000),
        (uid, 'Study Grandmaster', 'Study for 75 hours total', 0, 4500),
        (uid, 'Study Legend', 'Study for 100 hours total', 0, 6000),
        (uid, 'Study Mythic', 'Study for 150 hours total', 0, 9000),
        (uid, 'Study God', 'Study for 200 hours total', 0, 12000),
        
        # Crystal achievements (6)
        (uid, 'Pocket Change', 'Earn 100 crystals', 0, 100),
        (uid, 'Crystal Collector', 'Earn 1000 crystals', 0, 1000),
        (uid, 'Crystal Hoarder', 'Earn 5000 crystals', 0, 5000),
        (uid, 'Crystal Tycoon', 'Earn 10000 crystals', 0, 10000),
        (uid, 'Crystal Magnate', 'Earn 25000 crystals', 0, 25000),
        (uid, 'Crystal Emperor', 'Earn 50000 crystals', 0, 50000),
        
        # Gacha achievements (5)
        (uid, 'Gacha Beginner', 'Perform 10 gacha rolls', 0, 10),
        (uid, 'Gacha Enthusiast', 'Perform 25 gacha rolls', 0, 25),
        (uid, 'Gacha Master', 'Perform 50 gacha rolls', 0, 50),
        (uid, 'Gacha Addict', 'Perform 100 gacha rolls', 0, 100),
        (uid, 'Gacha Legend', 'Perform 250 gacha rolls', 0, 250),
        
        # Level achievements (5)
        (uid, 'Level 5', 'Reach level 5', 0, 5),
        (uid, 'Level 10', 'Reach level 10', 0, 10),
        (uid, 'Level 25', 'Reach level 25', 0, 25),
        (uid, 'Level 50', 'Reach level 50', 0, 50),
        (uid, 'Level 100', 'Reach level 100', 0, 100),
        
        # Collection achievements (4)
        (uid, 'Collector', 'Own 5 different items', 0, 5),
        (uid, 'Hoarder', 'Own 15 items total', 0, 15),
        (uid, 'Item Master', 'Own 25 items total', 0, 25),
        (uid, 'Treasure Hunter', 'Own all 6 unique items', 0, 6),
        
        # Special achievements (5)
        (uid, 'Lucky Strike', 'Get a gold rarity item from gacha', 0, 1),
        (uid, 'Marathon Runner', 'Complete a 60 minute study session', 0, 1),
        (uid, 'Ultra Marathon', 'Complete a 90 minute study session', 0, 1),
        (uid, 'Power User', 'Activate an item 10 times', 0, 10),
        (uid, 'Consistency King', 'Study for 7 consecutive days', 0, 7),
    ]
    
    # Filter out achievements that already exist
    new_achs = [ach for ach in all_achs if ach[1] not in existing_names]
    
    # Insert only new achievements
    if new_achs:
        x.executemany('''INSERT INTO achievements(user_id, name, description, progress, goal)
                         VALUES (?, ?, ?, ?, ?)''', new_achs)
        c.commit()
        print(f"Added {len(new_achs)} new achievements for user {uid}")
    
    c.close()
    
    # Backfill progress for newly added achievements based on existing data
    backfill_achievement_progress(uid)

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

def update_exp(uid, amount):
    """Add EXP and handle level-ups"""
    c=_c(); x=c.cursor()
    
    # Get current user stats
    x.execute('SELECT exp, level FROM users WHERE id=?', (uid,))
    user = x.fetchone()
    if not user:
        c.close()
        return 1
    
    current_exp = user['exp']
    current_level = user['level']
    new_exp = current_exp + amount
    
    # Calculate level-ups (100 EXP per level)
    exp_per_level = 100
    new_level = current_level
    
    while new_exp >= exp_per_level * new_level:
        new_exp -= exp_per_level * new_level
        new_level += 1
    
    # Update database
    x.execute('UPDATE users SET exp=?, level=? WHERE id=?', (new_exp, new_level, uid))
    c.commit()
    c.close()
    
    return new_level

def get_active_items(uid):
    """Get all active items for a user"""
    c=_c(); x=c.cursor()
    now = int(time.time())
    
    # Get active items that haven't expired
    x.execute('''SELECT ai.*, it.name, it.boost_exp_pct, it.boost_crystal_pct, it.rarity
                 FROM active_items ai
                 JOIN items it ON ai.item_id = it.id
                 WHERE ai.user_id=? AND ai.expires_at > ?''', (uid, now))
    r = [dict(row) for row in x.fetchall()]
    c.close()
    return r

def activate_item(uid, inventory_id):
    """Activate an item from inventory"""
    c=_c(); x=c.cursor()
    
    # Get the item from inventory
    x.execute('''SELECT i.*, it.rarity
                 FROM inventory i
                 JOIN items it ON i.item_id = it.id
                 WHERE i.id=? AND i.user_id=?''', (inventory_id, uid))
    inv_item = x.fetchone()
    
    if not inv_item:
        c.close()
        return False, "Item not found"
    
    inv_item = dict(inv_item)
    
    # Check if item is already active
    now = int(time.time())
    x.execute('''SELECT COUNT(*) as cnt FROM active_items 
                 WHERE user_id=? AND item_id=? AND expires_at > ?''', 
              (uid, inv_item['item_id'], now))
    if x.fetchone()['cnt'] > 0:
        c.close()
        return False, "Item already active"
    
    # Determine duration based on rarity (Bronze: 10min, Silver: 30min, Gold: 60min)
    durations = {'bronze': 10*60, 'silver': 30*60, 'gold': 60*60}
    duration = durations.get(inv_item['rarity'], 10*60)
    expires_at = now + duration
    
    # Activate item
    x.execute('''INSERT INTO active_items(user_id, item_id, activated_at, expires_at)
                 VALUES (?, ?, ?, ?)''', (uid, inv_item['item_id'], now, expires_at))
    
    c.commit()
    c.close()
    return True, "Item activated!"

def clean_expired_items(uid):
    """Remove expired items"""
    c=_c(); x=c.cursor()
    now = int(time.time())
    x.execute('DELETE FROM active_items WHERE user_id=? AND expires_at <= ?', (uid, now))
    c.commit()
    c.close()

def backfill_achievement_progress(uid):
    """Backfill progress for achievements based on existing data"""
    c=_c(); x=c.cursor()
    
    # Get existing user data
    x.execute('SELECT * FROM users WHERE id=?', (uid,))
    user = x.fetchone()
    if not user:
        c.close()
        return
    
    user = dict(user)
    
    # Backfill study time achievements
    total_study_minutes = get_total_study_minutes(uid)
    if total_study_minutes > 0:
        study_achievements = ['Getting Started', 'Study Rookie', 'Study Novice', 'Study Apprentice', 
                            'Study Warrior', 'Study Expert', 'Study Master', 'Study Grandmaster', 
                            'Study Legend', 'Study Mythic', 'Study God']
        for ach_name in study_achievements:
            x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                     (total_study_minutes, uid, ach_name))
    
    # Backfill crystal achievements
    total_crystals = get_total_crystals_earned(uid)
    if total_crystals > 0:
        crystal_achievements = ['Pocket Change', 'Crystal Collector', 'Crystal Hoarder', 
                               'Crystal Tycoon', 'Crystal Magnate', 'Crystal Emperor']
        for ach_name in crystal_achievements:
            x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                     (total_crystals, uid, ach_name))
    
    # Backfill level achievements
    level = user.get('level', 1)
    if level > 1:
        level_achievements = ['Level 5', 'Level 10', 'Level 25', 'Level 50', 'Level 100']
        for ach_name in level_achievements:
            x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                     (level, uid, ach_name))
    
    # Backfill collection achievements
    inventory = get_inventory(uid)
    if len(inventory) > 0:
        total_items = len(inventory)
        unique_items = len(set(i['item_id'] for i in inventory))
        
        x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                 (unique_items, uid, 'Collector'))
        x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                 (unique_items, uid, 'Treasure Hunter'))
        x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                 (total_items, uid, 'Hoarder'))
        x.execute('UPDATE achievements SET progress=? WHERE user_id=? AND name=? AND progress=0',
                 (total_items, uid, 'Item Master'))
    
    # Check and mark completed achievements
    x.execute('SELECT * FROM achievements WHERE user_id=? AND completed=0', (uid,))
    achievements = x.fetchall()
    for ach in achievements:
        ach = dict(ach)
        if ach['progress'] >= ach['goal']:
            now = int(time.time())
            x.execute('UPDATE achievements SET completed=1, completed_at=? WHERE id=?',
                     (now, ach['id']))
    
    c.commit()
    c.close()
