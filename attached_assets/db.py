
import sqlite3, time

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
  equipped_glasses INTEGER,
  equipped_mustache INTEGER,
  hair_color TEXT DEFAULT '#8B4513',
  skin_color TEXT DEFAULT '#F5DEB3',
  gender TEXT NOT NULL DEFAULT 'male',
  created_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  slot TEXT,
  rarity TEXT NOT NULL,
  boost_exp_pct INTEGER NOT NULL DEFAULT 0,
  boost_crystal_pct INTEGER NOT NULL DEFAULT 0,
  color TEXT,
  owned INTEGER NOT NULL DEFAULT 0,
  sprite_key TEXT
);
CREATE TABLE IF NOT EXISTS inventory(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  owned_ts INTEGER NOT NULL
);
"""

DEFAULT_ITEMS = [
  ("Short Hair", "hair", "hair", "C", 0, 0, "#8B4513", 1, "hair:short"),
  ("Curly Hair", "hair", "hair", "B", 0, 0, "#B6462B", 0, "hair:curly"),
  ("Long Hair",  "hair", "hair", "B", 0, 0, "#6A4CB3", 0, "hair:long"),
  ("Ponytail",   "hair", "hair", "A", 0, 0, "#2C7FA3", 0, "hair:ponytail"),
  ("Blue Shirt", "shirt","shirt","C", 0, 0, "#4169E1", 1, "shirt:tunic"),
  ("Green Shirt","shirt","shirt","B", 0, 0, "#228B22", 0, "shirt:tunic"),
  ("Gold Armor", "shirt","shirt","S", 5, 5, "#DAA520", 0, "shirt:armor"),
  ("Blue Pants", "pants","pants","C", 0, 0, "#4682B4", 1, "pants:pants"),
  ("Black Pants","pants","pants","B", 0, 0, "#2F4F4F", 0, "pants:pants"),
  ("Skirt",      "pants","pants","B", 0, 0, "#6A4CB3", 0, "pants:skirt"),
  ("Brown Boots","shoes","shoes","C", 0, 0, "#8B4513", 1, "shoes:boots"),
  ("Black Boots","shoes","shoes","B", 0, 0, "#1C1C1C", 0, "shoes:boots"),
  ("Round Glasses","cosmetic","glasses","B",0,0,"#000000",0,"glasses:round"),
  ("Square Glasses","cosmetic","glasses","A",0,0,"#333333",0,"glasses:square"),
  ("Classic Mustache","cosmetic","mustache","B",0,0,"#2C1B18",0,"mustache:classic"),
]

class DB:
  def __init__(self, path):
    self.conn = sqlite3.connect(path, check_same_thread=False)
    self.conn.row_factory = sqlite3.Row
    self._init_db()

  def _init_db(self):
    cur = self.conn.cursor()
    cur.executescript(SCHEMA)
    # migrations
    cur.execute("PRAGMA table_info(player)")
    cols = [row[1] for row in cur.fetchall()]
    for col, stmt in [
        ('equipped_glasses', "ALTER TABLE player ADD COLUMN equipped_glasses INTEGER"),
        ('equipped_mustache',"ALTER TABLE player ADD COLUMN equipped_mustache INTEGER"),
        ('gender',           "ALTER TABLE player ADD COLUMN gender TEXT NOT NULL DEFAULT 'male'"),
        ('hair_color',       "ALTER TABLE player ADD COLUMN hair_color TEXT DEFAULT '#8B4513'"),
        ('skin_color',       "ALTER TABLE player ADD COLUMN skin_color TEXT DEFAULT '#F5DEB3'"),
    ]:
        if col not in cols: cur.execute(stmt)

    cur.execute("PRAGMA table_info(items)")
    ic = [row[1] for row in cur.fetchall()]
    if 'sprite_key' not in ic:
        cur.execute("ALTER TABLE items ADD COLUMN sprite_key TEXT")

    cur.execute("SELECT id FROM player WHERE id=1")
    if not cur.fetchone():
        cur.execute("INSERT INTO player(id,level,exp,crystals,created_ts) VALUES (1,1,0,0,strftime('%s','now'))")

    for it in DEFAULT_ITEMS:
        cur.execute("SELECT id FROM items WHERE name=?", (it[0],))
        if not cur.fetchone():
            if 'sprite_key' in ic:
                cur.execute("INSERT INTO items(name,type,slot,rarity,boost_exp_pct,boost_crystal_pct,color,owned,sprite_key) VALUES (?,?,?,?,?,?,?,?,?)", it)
            else:
                cur.execute("INSERT INTO items(name,type,slot,rarity,boost_exp_pct,boost_crystal_pct,color,owned) VALUES (?,?,?,?,?,?,?,?)", it[:-1])
            if it[7]==1:
                cur.execute("INSERT INTO inventory(item_id, owned_ts) VALUES (?, strftime('%s','now'))", (cur.lastrowid,))
    self.conn.commit()

  def get_player(self):
    return dict(self.conn.execute("SELECT * FROM player WHERE id=1").fetchone())

  def get_equipment(self):
    p = self.get_player()
    eq = {}
    for slot,col in [
      ('hair','equipped_hair'),('shirt','equipped_shirt'),
      ('pants','equipped_pants'),('shoes','equipped_shoes'),
      ('glasses','equipped_glasses'),('mustache','equipped_mustache')
    ]:
      if p.get(col):
        r = self.conn.execute("SELECT * FROM items WHERE id=?", (p[col],)).fetchone()
        eq[slot] = dict(r) if r else None
    eq['hair_color'] = p.get('hair_color','#8B4513')
    eq['skin_color'] = p.get('skin_color','#F5DEB3')
    eq['gender'] = p.get('gender','male')
    return eq

  def build_appearance(self):
    p = self.get_player()
    eq = self.get_equipment()
    def color(slot, default_hex):
      return (eq.get(slot) or {}).get('color', default_hex)
    return {
      "sex": eq['gender'],
      "skin_color": eq['skin_color'],
      "hair_color": color('hair', p.get('hair_color','#8B4513')),
      "shirt_color": color('shirt', '#4169E1'),
      "pants_color": color('pants', '#4682B4'),
      "shoes_color": color('shoes', '#8B4513'),
      "has_glasses": eq.get('glasses') is not None,
      "glasses_color": color('glasses', '#000000'),
      "has_mustache": eq.get('mustache') is not None,
      "facial_hair_color": color('mustache', '#2C1B18')
    }
