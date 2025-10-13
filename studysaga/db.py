import sqlite3, os, time, datetime, json, math, random

SCHEMA = """
CREATE TABLE IF NOT EXISTS player(
  id INTEGER PRIMARY KEY CHECK (id=1),
  level INTEGER NOT NULL DEFAULT 1,
  exp INTEGER NOT NULL DEFAULT 0,
  crystals INTEGER NOT NULL DEFAULT 0,
  equipped_skin_id INTEGER,
  equipped_hair INTEGER,
  equipped_shirt INTEGER,
  equipped_pants INTEGER,
  equipped_shoes INTEGER,
  hair_color TEXT DEFAULT '#8B4513',
  skin_color TEXT DEFAULT '#F5DEB3',
  created_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL, -- 'skin', 'boost', 'hair', 'shirt', 'pants', 'shoes'
  slot TEXT, -- 'hair', 'shirt', 'pants', 'shoes'
  rarity TEXT NOT NULL, -- 'C','B','A','S'
  boost_exp_pct INTEGER NOT NULL DEFAULT 0,
  boost_crystal_pct INTEGER NOT NULL DEFAULT 0,
  color TEXT, -- hex color for the item
  owned INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS inventory(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  owned_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  start_ts INTEGER NOT NULL,
  end_ts INTEGER,
  minutes INTEGER,
  phase TEXT NOT NULL -- 'study'/'break'
);
CREATE TABLE IF NOT EXISTS weekly_state(
  id INTEGER PRIMARY KEY CHECK (id=1),
  week_key TEXT NOT NULL,
  claimed INTEGER NOT NULL DEFAULT 0
);
"""

DEFAULT_ITEMS = [
  ("Basic Hair", "hair", "hair", "C", 0, 0, "#8B4513", 1),  # owned by default
  ("Blonde Hair", "hair", "hair", "B", 0, 0, "#FFD700", 0),
  ("Black Hair", "hair", "hair", "B", 0, 0, "#2C1B18", 0),
  ("Red Hair", "hair", "hair", "A", 0, 0, "#D2691E", 0),
  ("Blue Shirt", "shirt", "shirt", "C", 0, 0, "#4169E1", 1),  # owned by default
  ("Red Shirt", "shirt", "shirt", "B", 0, 0, "#DC143C", 0),
  ("Green Shirt", "shirt", "shirt", "B", 0, 0, "#228B22", 0),
  ("Gold Armor", "shirt", "shirt", "S", 5, 5, "#DAA520", 0),
  ("Blue Pants", "pants", "pants", "C", 0, 0, "#4682B4", 1),  # owned by default
  ("Black Pants", "pants", "pants", "B", 0, 0, "#2F4F4F", 0),
  ("Brown Boots", "shoes", "shoes", "C", 0, 0, "#8B4513", 1),  # owned by default
  ("Black Boots", "shoes", "shoes", "B", 0, 0, "#1C1C1C", 0),
  ("Scholar's Scarf", "boost", None, "B", 10, 0, None, 0),
  ("Gem Pouch", "boost", None, "B", 0, 15, None, 0),
  ("Focus Band", "boost", None, "A", 15, 10, None, 0),
  ("Ancient Tome", "boost", None, "S", 25, 25, None, 0),
]

class DB:
  def __init__(self, path):
    self.path = path
    self.conn = sqlite3.connect(self.path, check_same_thread=False)
    self.conn.row_factory = sqlite3.Row
    self._init_db()

  def _init_db(self):
    cur = self.conn.cursor()
    cur.executescript(SCHEMA)
    
    # Add new columns if they don't exist (for migration)
    cur.execute("PRAGMA table_info(player)")
    cols = [row[1] for row in cur.fetchall()]
    if 'equipped_hair' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN equipped_hair INTEGER")
    if 'equipped_shirt' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN equipped_shirt INTEGER")
    if 'equipped_pants' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN equipped_pants INTEGER")
    if 'equipped_shoes' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN equipped_shoes INTEGER")
    if 'hair_color' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN hair_color TEXT DEFAULT '#8B4513'")
    if 'skin_color' not in cols:
      cur.execute("ALTER TABLE player ADD COLUMN skin_color TEXT DEFAULT '#F5DEB3'")
    
    cur.execute("PRAGMA table_info(items)")
    item_cols = [row[1] for row in cur.fetchall()]
    if 'slot' not in item_cols:
      cur.execute("ALTER TABLE items ADD COLUMN slot TEXT")
    if 'color' not in item_cols:
      cur.execute("ALTER TABLE items ADD COLUMN color TEXT")
    
    cur.execute("SELECT id FROM player WHERE id=1")
    if not cur.fetchone():
      cur.execute("INSERT INTO player(id, level, exp, crystals, created_ts) VALUES (1,1,0,0,?)", (int(time.time()),))
    
    self._ensure_default_setting('study_minutes', 25)
    self._ensure_default_setting('break_minutes', 5)
    self._ensure_default_setting('daily_goal', 120)
    self._ensure_default_setting('weekly_goal', 600)
    
    default_hair_id = None
    default_shirt_id = None
    default_pants_id = None
    default_shoes_id = None
    
    for it in DEFAULT_ITEMS:
      cur.execute("SELECT id FROM items WHERE name=?", (it[0],))
      existing = cur.fetchone()
      if not existing:
        cur.execute(
          "INSERT INTO items(name,type,slot,rarity,boost_exp_pct,boost_crystal_pct,color,owned) VALUES (?,?,?,?,?,?,?,?)",
          (it[0], it[1], it[2], it[3], it[4], it[5], it[6], it[7])
        )
        item_id = cur.lastrowid
        # If owned by default, add to inventory
        if it[7] == 1:
          cur.execute("INSERT INTO inventory(item_id, owned_ts) VALUES (?,?)", (item_id, int(time.time())))
          # Track default items for auto-equip
          if it[0] == "Basic Hair":
            default_hair_id = item_id
          elif it[0] == "Blue Shirt":
            default_shirt_id = item_id
          elif it[0] == "Blue Pants":
            default_pants_id = item_id
          elif it[0] == "Brown Boots":
            default_shoes_id = item_id
      else:
        # Track existing default items
        if it[0] == "Basic Hair":
          default_hair_id = existing['id']
        elif it[0] == "Blue Shirt":
          default_shirt_id = existing['id']
        elif it[0] == "Blue Pants":
          default_pants_id = existing['id']
        elif it[0] == "Brown Boots":
          default_shoes_id = existing['id']
    
    # Auto-equip default items if player has none equipped
    cur.execute("SELECT equipped_hair, equipped_shirt, equipped_pants, equipped_shoes FROM player WHERE id=1")
    player_eq = cur.fetchone()
    if player_eq:
      if not player_eq['equipped_hair'] and default_hair_id:
        cur.execute("UPDATE player SET equipped_hair=? WHERE id=1", (default_hair_id,))
      if not player_eq['equipped_shirt'] and default_shirt_id:
        cur.execute("UPDATE player SET equipped_shirt=? WHERE id=1", (default_shirt_id,))
      if not player_eq['equipped_pants'] and default_pants_id:
        cur.execute("UPDATE player SET equipped_pants=? WHERE id=1", (default_pants_id,))
      if not player_eq['equipped_shoes'] and default_shoes_id:
        cur.execute("UPDATE player SET equipped_shoes=? WHERE id=1", (default_shoes_id,))
    
    wk = self._current_week_key()
    cur.execute("SELECT id FROM weekly_state WHERE id=1")
    if not cur.fetchone():
      cur.execute("INSERT INTO weekly_state(id,week_key,claimed) VALUES (1,?,0)", (wk,))
    self.conn.commit()

  def _ensure_default_setting(self, key, value):
    self.conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, str(value)))
    self.conn.execute("UPDATE settings SET value=? WHERE key=? AND value IS NULL", (str(value), key))
    self.conn.commit()

  def _current_week_key(self):
    today = datetime.date.today()
    iso = today.isocalendar()
    return f"{iso[0]}-W{iso[1]}"

  def ensure_player(self):
    self.conn.execute("UPDATE player SET id=1 WHERE id=1")
    self.conn.commit()
    return self.get_player()

  def get_player(self):
    row = self.conn.execute("SELECT * FROM player WHERE id=1").fetchone()
    return dict(row)

  def set_setting(self, key, value):
    self.conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (key, str(value)))
    self.conn.commit()

  def get_setting(self, key, default=None):
    row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row['value'] if row else default

  def get_setting_int(self, key, default):
    row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return int(row['value']) if row else int(default)

  def add_rewards(self, exp, crystals):
    p = self.get_player()
    new_exp = p['exp'] + int(exp)
    new_cr = p['crystals'] + int(crystals)
    level = p['level']
    while new_exp >= level * 100:
      new_exp -= level * 100
      level += 1
    self.conn.execute("UPDATE player SET level=?, exp=?, crystals=? WHERE id=1", (level, new_exp, new_cr))
    self.conn.commit()

  def start_session(self, phase):
    ts = int(time.time())
    self.conn.execute("INSERT INTO sessions(start_ts, phase) VALUES (?,?)", (ts, phase))
    self.conn.commit()
    return ts

  def end_session(self, phase):
    row = self.conn.execute(
      "SELECT id, start_ts FROM sessions WHERE end_ts IS NULL AND phase=? ORDER BY id DESC LIMIT 1",
      (phase,)
    ).fetchone()
    if not row:
      return 0
    now = int(time.time())
    minutes = max(0, int((now - row['start_ts']) / 60))
    self.conn.execute("UPDATE sessions SET end_ts=?, minutes=? WHERE id=?", (now, minutes, row['id']))
    self.conn.commit()
    return minutes

  def today_minutes(self):
    start = int(datetime.datetime.combine(datetime.date.today(), datetime.time.min).timestamp())
    end = int(datetime.datetime.combine(datetime.date.today(), datetime.time.max).timestamp())
    row = self.conn.execute(
      "SELECT COALESCE(SUM(minutes),0) AS m FROM sessions WHERE phase='study' AND end_ts IS NOT NULL AND start_ts BETWEEN ? AND ?",
      (start, end)
    ).fetchone()
    return int(row['m'] or 0)

  def weekly_minutes(self):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    start = int(datetime.datetime.combine(monday, datetime.time.min).timestamp())
    end = start + 7*24*3600 - 1
    row = self.conn.execute(
      "SELECT COALESCE(SUM(minutes),0) AS m FROM sessions WHERE phase='study' AND end_ts IS NOT NULL AND start_ts BETWEEN ? AND ?",
      (start, end)
    ).fetchone()
    wk = self._current_week_key()
    s = self.conn.execute("SELECT week_key FROM weekly_state WHERE id=1").fetchone()
    if s and s['week_key'] != wk:
      self.conn.execute("UPDATE weekly_state SET week_key=?, claimed=0 WHERE id=1", (wk,))
      self.conn.commit()
    return int(row['m'] or 0)

  def is_weekly_claimed(self):
    r = self.conn.execute("SELECT claimed FROM weekly_state WHERE id=1").fetchone()
    return bool(r and r['claimed'])

  def set_weekly_claimed(self):
    self.conn.execute("UPDATE weekly_state SET claimed=1 WHERE id=1")
    self.conn.commit()

  def list_inventory(self):
    rows = self.conn.execute(
      """SELECT items.id, items.name, items.type, items.slot, items.rarity,
                items.boost_exp_pct, items.boost_crystal_pct, items.color, items.owned
         FROM items WHERE owned=1
         ORDER BY CASE rarity
           WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 ELSE 4 END, name"""
    ).fetchall()
    return [dict(r) for r in rows]

  def equip_item(self, item_id):
    it = self.conn.execute("SELECT type, slot FROM items WHERE id=?", (item_id,)).fetchone()
    if not it: return
    
    if it['type'] == 'skin':
      self.conn.execute("UPDATE player SET equipped_skin_id=? WHERE id=1", (item_id,))
    elif it['slot'] == 'hair':
      self.conn.execute("UPDATE player SET equipped_hair=? WHERE id=1", (item_id,))
    elif it['slot'] == 'shirt':
      self.conn.execute("UPDATE player SET equipped_shirt=? WHERE id=1", (item_id,))
    elif it['slot'] == 'pants':
      self.conn.execute("UPDATE player SET equipped_pants=? WHERE id=1", (item_id,))
    elif it['slot'] == 'shoes':
      self.conn.execute("UPDATE player SET equipped_shoes=? WHERE id=1", (item_id,))
    self.conn.commit()
  
  def get_equipment(self):
    p = self.get_player()
    equipment = {}
    
    if p.get('equipped_hair'):
      item = self.conn.execute("SELECT * FROM items WHERE id=?", (p['equipped_hair'],)).fetchone()
      equipment['hair'] = dict(item) if item else None
    if p.get('equipped_shirt'):
      item = self.conn.execute("SELECT * FROM items WHERE id=?", (p['equipped_shirt'],)).fetchone()
      equipment['shirt'] = dict(item) if item else None
    if p.get('equipped_pants'):
      item = self.conn.execute("SELECT * FROM items WHERE id=?", (p['equipped_pants'],)).fetchone()
      equipment['pants'] = dict(item) if item else None
    if p.get('equipped_shoes'):
      item = self.conn.execute("SELECT * FROM items WHERE id=?", (p['equipped_shoes'],)).fetchone()
      equipment['shoes'] = dict(item) if item else None
    
    equipment['hair_color'] = p.get('hair_color', '#8B4513')
    equipment['skin_color'] = p.get('skin_color', '#F5DEB3')
    return equipment

  def get_equipped_boosts(self):
    row = self.conn.execute(
      "SELECT COALESCE(SUM(boost_exp_pct),0) AS e, COALESCE(SUM(boost_crystal_pct),0) AS c FROM items WHERE owned=1 AND type='boost'"
    ).fetchone()
    return {'exp_pct': int(row['e'] or 0), 'crystal_pct': int(row['c'] or 0)}

  def add_item_by_name(self, name):
    it = self.conn.execute("SELECT id FROM items WHERE name=?", (name,)).fetchone()
    if not it: return None
    self.conn.execute("UPDATE items SET owned=1 WHERE id=?", (it['id'],))
    self.conn.execute("INSERT INTO inventory(item_id, owned_ts) VALUES (?,?)", (it['id'], int(time.time())))
    self.conn.commit()
    r = self.conn.execute("SELECT * FROM items WHERE id=?", (it['id'],)).fetchone()
    return dict(r)

  def add_item_id(self, item_id):
    self.conn.execute("UPDATE items SET owned=1 WHERE id=?", (item_id,))
    self.conn.execute("INSERT INTO inventory(item_id, owned_ts) VALUES (?,?)", (item_id, int(time.time())))
    self.conn.commit()
    r = self.conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return dict(r)

  def spend_crystals(self, amount):
    p = self.get_player()
    if p['crystals'] < amount:
      return False
    self.conn.execute("UPDATE player SET crystals=crystals-? WHERE id=1", (amount,))
    self.conn.commit()
    return True

  def pool_by_tier(self, tier):
    rows = self.conn.execute("SELECT * FROM items").fetchall()
    items = [dict(r) for r in rows]
    pool = []
    for it in items:
      r = it['rarity']
      if tier=='bronze':
        w = {'C': 60, 'B': 35, 'A': 5, 'S': 1}.get(r, 0)
      elif tier=='silver':
        w = {'C': 20, 'B': 55, 'A': 22, 'S': 3}.get(r, 0)
      else:
        w = {'C': 5, 'B': 30, 'A': 45, 'S': 20}.get(r, 0)
      pool.extend([it]*w)
    return pool
