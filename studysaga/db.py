import os, sqlite3, time, random
from typing import Dict, List, Optional, Tuple
from pathlib import Path

DB_PATH = os.environ.get("STUDYSAGA_DB", "studysaga.sqlite3")
GACHA_COST = 50
TEN_ROLL_COST = 480  # 10% 할인

SLOTS = ["hair","top","bottom","shoes","accessory"]
RARITY_WEIGHTS = [("Common",70), ("Rare",20), ("Epic",8), ("Legendary",2)]

def get_conn():
    return sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)

def _get_conn():
    return get_conn()

def bootstrap():
    con = get_conn(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash BLOB,
        created_at INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS economy(
        user_id INTEGER PRIMARY KEY,
        crystals INTEGER DEFAULT 300
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        slot TEXT,
        item TEXT,
        rarity TEXT DEFAULT 'Common',
        created_at INTEGER
    )""")
    try: cur.execute("ALTER TABLE inventory ADD COLUMN rarity TEXT DEFAULT 'Common'")
    except sqlite3.OperationalError: pass
    cur.execute("""CREATE TABLE IF NOT EXISTS loadout(
        user_id INTEGER,
        slot TEXT,
        item TEXT,
        PRIMARY KEY(user_id, slot)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS profile(
        user_id INTEGER PRIMARY KEY,
        gender TEXT DEFAULT 'male',
        nickname TEXT DEFAULT ''
    )""")
    con.commit(); con.close()

def cleanup_expired_sessions(max_age_days: int = 30):
    cutoff = int(time.time()) - max_age_days*24*3600
    con = get_conn(); cur = con.cursor()
    cur.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff,))
    con.commit(); con.close()

def get_user_id_by_token(token: str) -> Optional[int]:
    if not token: return None
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT user_id FROM sessions WHERE token=?", (token,))
    row = cur.fetchone(); con.close()
    return row[0] if row else None

# economy
def get_crystals(user_id: int) -> int:
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO economy(user_id, crystals) VALUES(?, 300)", (user_id,))
    con.commit()
    cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,))
    row = cur.fetchone(); con.close()
    return row[0] if row else 0

def spend_crystals(user_id: int, amount: int) -> Tuple[bool,int]:
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO economy(user_id, crystals) VALUES(?, 300)", (user_id,))
    cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,))
    have = (cur.fetchone() or [0])[0]
    if have < amount:
        con.close(); return False, have
    cur.execute("UPDATE economy SET crystals = crystals - ? WHERE user_id=?", (amount, user_id))
    con.commit()
    cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,))
    left = (cur.fetchone() or [0])[0]
    con.close(); return True, left

# inventory
def add_item(user_id: int, slot: str, item: str, rarity: str = "Common"):
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT INTO inventory(user_id, slot, item, rarity, created_at) VALUES (?,?,?,?,?)",
                (user_id, slot, item, rarity, int(time.time())))
    con.commit(); con.close()

def list_inventory(user_id: int) -> Dict[str, List[str]]:
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT slot, item FROM inventory WHERE user_id=?", (user_id,))
    rows = cur.fetchall(); con.close()
    out = {s:[] for s in SLOTS}
    for s,i in rows:
        out.setdefault(s, []).append(i)
    return out

def set_loadout(user_id: int, slot: str, item: Optional[str]):
    con = get_conn(); cur = con.cursor()
    if item is None:
        cur.execute("DELETE FROM loadout WHERE user_id=? AND slot=?", (user_id, slot))
    else:
        cur.execute("INSERT OR REPLACE INTO loadout(user_id, slot, item) VALUES (?,?,?)", (user_id, slot, item))
    con.commit(); con.close()

def get_loadout(user_id: int) -> Dict[str, Optional[str]]:
    out = {s:None for s in SLOTS}
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT slot, item FROM loadout WHERE user_id=?", (user_id,))
    for s,i in cur.fetchall():
        out[s]=i
    con.close()
    return out

# profile
def set_gender(user_id: int, gender: str):
    if gender not in ("male","female"): gender = "male"
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, gender) VALUES (?,?)", (user_id, gender))
    cur.execute("UPDATE profile SET gender=? WHERE user_id=?", (gender, user_id))
    con.commit(); con.close()

def set_nickname(user_id: int, nickname: str):
    nickname = (nickname or "").strip()
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, nickname) VALUES (?,?)", (user_id, nickname))
    cur.execute("UPDATE profile SET nickname=? WHERE user_id=?", (nickname, user_id))
    con.commit(); con.close()

def get_profile(user_id: int) -> Tuple[str,str]:
    con = get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, gender, nickname) VALUES (?, 'male', '')", (user_id,))
    con.commit()
    cur.execute("SELECT gender, nickname FROM profile WHERE user_id=?", (user_id,))
    row = cur.fetchone(); con.close()
    return (row[0], row[1] or "") if row else ("male","")

# items
def default_items() -> Dict[str, List[str]]:
    base = Path(__file__).resolve().parent.parent / "assets"
    out = {s: [] for s in SLOTS}
    for s in SLOTS:
        for p in base.glob(f"{s}_*.png"):
            out[s].append(p.name)
    return out

# gacha helpers
def _weighted_choice(pairs):
    total = sum(w for _,w in pairs)
    r = random.uniform(0, total); upto = 0
    for name, weight in pairs:
        if upto + weight >= r:
            return name
        upto += weight
    return pairs[-1][0]

def gacha_roll_once(user_id: int, items=None, cost=None):
    items = items or default_items()
    cost = GACHA_COST if cost is None else cost
    ok, crystals = spend_crystals(user_id, cost)
    if not ok:
        return False, "", "not_enough_crystals", crystals, "Common"
    rarity = _weighted_choice(RARITY_WEIGHTS)
    slot = random.choice(list(items.keys()))
    if not items.get(slot):
        return False, "", "no_items", crystals, "Common"
    item = random.choice(items[slot])
    add_item(user_id, slot, item, rarity)
    return True, slot, item, crystals, rarity

def gacha_roll_ten(user_id: int, items=None, cost=None):
    items = items or default_items()
    cost = TEN_ROLL_COST if cost is None else cost
    ok, crystals = spend_crystals(user_id, cost)
    if not ok:
        return False, [], crystals
    results = []
    for _ in range(10):
        rarity = _weighted_choice(RARITY_WEIGHTS)
        slot = random.choice(list(items.keys()))
        item = random.choice(items[slot])
        add_item(user_id, slot, item, rarity)
        results.append((slot, item, rarity))
    new_crystals = get_crystals(user_id)
    return True, results, new_crystals
