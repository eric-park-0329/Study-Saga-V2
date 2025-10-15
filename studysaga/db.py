import os, sqlite3, time, random
from pathlib import Path
from typing import Optional, Dict, List

DB_PATH = os.environ.get("STUDYSAGA_DB", "studysaga.sqlite3")
GACHA_COST = 50
TEN_ROLL_COST = 480

SLOTS = ["hair","top","bottom","shoes","accessory"]
RARITY_WEIGHTS = [("Common",70), ("Rare",20), ("Epic",8), ("Legendary",2)]

def _get_conn():
    return sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)

def bootstrap():
    con = _get_conn(); cur = con.cursor()
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

def cleanup_expired_sessions(max_days=30):
    cutoff = int(time.time()) - max_days*24*3600
    con = _get_conn(); cur = con.cursor()
    cur.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff,))
    con.commit(); con.close()

def get_user_id_by_token(token: str) -> Optional[int]:
    if not token: return None
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT user_id FROM sessions WHERE token=?", (token,))
    row = cur.fetchone(); con.close()
    return row[0] if row else None

# economy
def get_crystals(user_id: int) -> int:
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO economy(user_id, crystals) VALUES(?, 300)", (user_id,))
    con.commit()
    cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,))
    row = cur.fetchone(); con.close()
    return row[0] if row else 0

def set_crystals(user_id: int, amount: int):
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO economy(user_id, crystals) VALUES(?,?)", (user_id, amount))
    con.commit(); con.close()

def spend(user_id: int, amount: int):
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO economy(user_id, crystals) VALUES(?, 300)", (user_id,))
    cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,))
    have = (cur.fetchone() or [0])[0]
    if have < amount: con.close(); return False, have
    cur.execute("UPDATE economy SET crystals = crystals - ? WHERE user_id=?", (amount, user_id))
    con.commit(); cur.execute("SELECT crystals FROM economy WHERE user_id=?", (user_id,)); left = (cur.fetchone() or [0])[0]
    con.close(); return True, left

# profile
def set_gender(user_id: int, gender: str):
    if gender not in ("male","female"): gender = "male"
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, gender) VALUES (?,?)", (user_id, gender))
    cur.execute("UPDATE profile SET gender=? WHERE user_id=?", (gender, user_id))
    con.commit(); con.close()

def set_nickname(user_id: int, nickname: str):
    nickname = (nickname or "").strip()
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, nickname) VALUES (?,?)", (user_id, nickname))
    cur.execute("UPDATE profile SET nickname=? WHERE user_id=?", (nickname, user_id))
    con.commit(); con.close()

def get_profile(user_id: int):
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO profile(user_id, gender, nickname) VALUES (?, 'male', '')", (user_id,))
    con.commit()
    cur.execute("SELECT gender, nickname FROM profile WHERE user_id=?", (user_id,))
    row = cur.fetchone(); con.close()
    return (row[0], row[1] or "") if row else ("male","")

# inventory
def default_items() -> Dict[str, List[str]]:
    base = Path(__file__).resolve().parent.parent / "assets"
    out = {s: [] for s in SLOTS}
    for s in SLOTS:
        for p in sorted(base.glob(f"{s}_*.png")):
            out[s].append(p.name)
    return out

def add_item(user_id: int, slot: str, item: str, rarity: str):
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT INTO inventory(user_id, slot, item, rarity, created_at) VALUES (?,?,?,?,?)",
                (user_id, slot, item, rarity, int(time.time())))
    con.commit(); con.close()

def list_inventory(user_id: int):
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT slot, item FROM inventory WHERE user_id=?", (user_id,))
    out = {s: [] for s in SLOTS}
    for s,i in cur.fetchall():
        out.setdefault(s, []).append(i)
    con.close(); return out

def set_loadout(user_id: int, slot: str, item: str):
    con = _get_conn(); cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO loadout(user_id, slot, item) VALUES (?,?,?)",(user_id,slot,item))
    con.commit(); con.close()

def get_loadout(user_id: int):
    out = {s: None for s in SLOTS}
    con = _get_conn(); cur = con.cursor()
    cur.execute("SELECT slot, item FROM loadout WHERE user_id=?", (user_id,))
    for s,i in cur.fetchall(): out[s]=i
    con.close(); return out

# gacha
def _weighted_choice(pairs):
    tot = sum(w for _,w in pairs)
    r = random.uniform(0, tot); up=0
    for name,w in pairs:
        if up + w >= r: return name
        up += w
    return pairs[-1][0]

def roll_once(user_id: int, items=None, cost=None):
    items = items or default_items()
    cost = GACHA_COST if cost is None else cost
    ok, crystals = spend(user_id, cost)
    if not ok: return False, None, crystals
    rarity = _weighted_choice(RARITY_WEIGHTS)
    slot = random.choice(list(items.keys()))
    item = random.choice(items[slot])
    add_item(user_id, slot, item, rarity)
    return True, (slot, item, rarity), crystals

def roll_ten(user_id: int, items=None, cost=None):
    items = items or default_items()
    cost = TEN_ROLL_COST if cost is None else cost
    ok, crystals = spend(user_id, cost)
    if not ok: return False, [], crystals
    results=[]
    for _ in range(10):
        rarity = _weighted_choice(RARITY_WEIGHTS)
        slot = random.choice(list(items.keys()))
        item = random.choice(items[slot])
        add_item(user_id, slot, item, rarity)
        results.append((slot,item,rarity))
    return True, results, get_crystals(user_id)
