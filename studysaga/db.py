import sqlite3, os, time, datetime, json, math, random

SCHEMA = """
CREATE TABLE IF NOT EXISTS player(
  id INTEGER PRIMARY KEY CHECK (id=1),
  level INTEGER NOT NULL DEFAULT 1,
  exp INTEGER NOT NULL DEFAULT 0,
  crystals INTEGER NOT NULL DEFAULT 0,
  equipped_skin_id INTEGER,
  created_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL, -- 'skin' or 'boost'
  rarity TEXT NOT NULL, -- 'C','B','A','S'
  boost_exp_pct INTEGER NOT NULL DEFAULT 0,
  boost_crystal_pct INTEGER NOT NULL DEFAULT 0,
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
  ("Basic Cloak", "skin", "C", 0, 0),
  ("Scholar's Scarf", "boost", "B", 10, 0),
  ("Gem Pouch", "boost", "B", 0, 15),
  ("Focus Band", "boost", "A", 15, 10),
  ("Golden Cape", "skin", "S", 0, 0),
  ("Ancient Tome", "boost", "S", 25, 25),
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
    cur.execute("SELECT id FROM player WHERE id=1")
    if not cur.fetchone():
      cur.execute("INSERT INTO player(id, level, exp, crystals, created_ts) VALUES (1,1,0,0,?)", (int(time.time()),))
    self._ensure_default_setting('study_minutes', 25)
    self._ensure_default_setting('break_minutes', 5)
    self._ensure_default_setting('daily_goal', 120)
    self._ensure_default_setting('weekly_goal', 600)
    for it in DEFAULT_ITEMS:
      cur.execute("SELECT id FROM items WHERE name=?", (it[0],))
      if not cur.fetchone():
        cur.execute(
          "INSERT INTO items(name,type,rarity,boost_exp_pct,boost_crystal_pct,owned) VALUES (?,?,?,?,?,0)",
          (it[0], it[1], it[2], it[3], it[4])
        )
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
      """SELECT items.id, items.name, items.type, items.rarity,
                items.boost_exp_pct, items.boost_crystal_pct, items.owned
         FROM items WHERE owned=1
         ORDER BY CASE rarity
           WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 ELSE 4 END, name"""
    ).fetchall()
    return [dict(r) for r in rows]

  def equip_item(self, item_id):
    it = self.conn.execute("SELECT type FROM items WHERE id=?", (item_id,)).fetchone()
    if not it: return
    if it['type'] == 'skin':
      self.conn.execute("UPDATE player SET equipped_skin_id=? WHERE id=1", (item_id,))
      self.conn.commit()

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
