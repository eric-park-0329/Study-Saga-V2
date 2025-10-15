import os, io
from pathlib import Path
os.environ["KIVY_NO_ARGS"] = "1"
APP_DIR = Path(__file__).resolve().parent
try: os.chdir(APP_DIR)
except Exception: pass

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, Color, InstructionGroup
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, ListProperty
from kivy.core.image import Image as CoreImage
from kivy.uix.video import Video
from kivy.animation import Animation

from sprite_renderer_ref import SpriteRendererRef
from studysaga import db as dbmod
from studysaga import auth as authmod

class VideoBackground(Widget):
    def __init__(self, source:str, **kwargs):
        super().__init__(**kwargs)
        self.video = Video(source=source, state='stop', options={'eof':'loop'})
        self.video.allow_stretch = True
        self.video.keep_ratio = False
        self.video.volume = 0.0
        self.add_widget(self.video)
        self.bind(size=self._sync, pos=self._sync)
        Clock.schedule_once(lambda *_: self._start(), 0)
    def _sync(self, *a):
        self.video.size = self.size
        self.video.pos = self.pos
    def _start(self):
        try:
            self.video.state = 'play'
        except Exception as e:
            print("[WARN] Video play failed:", e)

class ProceduralBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self._instr = InstructionGroup()
        self.canvas.add(self._instr)
        self._stars = [(i*37 % 1000, (i*97)%600, (0.6+0.4*((i*53)%10)/10.0)) for i in range(220)]
        Clock.schedule_interval(self._tick, 1/60)
        self.bind(pos=self._redraw, size=self._redraw)
    def _redraw(self, *a): self._tick(0)
    def _tick(self, dt):
        import math
        self._t += dt
        w, h = self.width, self.height
        self._instr.clear()
        Color(0.03,0.04,0.06,1.0); Rectangle(pos=self.pos, size=self.size)
        for i in range(4):
            amp = 20+ i*10
            y = self.y + h*(0.2 + 0.15*i) + math.sin(self._t*0.6 + i)*amp
            a = 0.08 + i*0.03
            Color(0.35,0.55,0.95, a)
            Rectangle(pos=(self.x, y), size=(w, h*0.12))
        for i,(sx,sy,tw) in enumerate(self._stars):
            px = (self.x + ((sx + self._t*20) % max(w,1)))
            py = self.y + (sy % max(h,1))
            a = 0.15 + 0.25*abs(math.sin(self._t*tw + i))
            Color(0.8,0.9,1.0,a); Rectangle(pos=(px,py), size=(2,2))

class GachaFX(Widget):
    angle = NumericProperty(0)
    scale = NumericProperty(1)
    color = ListProperty([1,1,1,0.2])
    def start_spin(self, rarity: str):
        colors = {
            "Common": (1,1,1,0.15),
            "Rare": (0.6,0.8,1,0.25),
            "Epic": (0.7,0.6,1,0.35),
            "Legendary": (1,0.84,0.2,0.45),
        }
        self.color = colors.get(rarity, (1,1,1,0.2))
        self.angle = 0
        self.scale = 0.6
        a1 = Animation(angle=360, scale=1.2, d=0.6, t='out_cubic')
        a2 = Animation(angle=720, scale=1.0, d=0.6, t='out_back')
        (a1 + a2).start(self)

class AuthScreen(Screen):
    status = StringProperty("")
    status_msg = StringProperty("")
    def on_status(self, *a): 
        if self.status_msg != self.status: self.status_msg = self.status
    def on_status_msg(self, *a):
        if self.status != self.status_msg: self.status = self.status_msg

class HomeScreen(Screen): pass
class StudyScreen(Screen): status = StringProperty("")
class GachaScreen(Screen): status = StringProperty(""); result_image = ObjectProperty(None)
class InventoryScreen(Screen): pass
class SettingsScreen(Screen): pass
class GenderSelectScreen(Screen): pass

# Load kv files
for rel in ("ui/auth.kv","ui/home.kv","ui/study.kv","ui/gacha.kv","ui/inventory.kv","ui/settings.kv","ui/gender_select.kv"):
    p = APP_DIR/rel
    if p.exists(): Builder.load_file(str(p))

class StudySagaApp(App):
    session_token = None; username = None; user_id = None
    def build(self):
        Window.clearcolor = (0,0,0,1)
        try: dbmod.bootstrap(); dbmod.cleanup_expired_sessions(30)
        except Exception as e: print("[WARN] DB bootstrap:", e)
        root = FloatLayout()
        self.sm = ScreenManager(transition=NoTransition(), size_hint=(1,1), pos=(0,0))

        for name, cls in [("auth",AuthScreen),("home",HomeScreen),("study",StudyScreen),
                          ("gacha",GachaScreen),("inventory",InventoryScreen),
                          ("settings",SettingsScreen),("gender",GenderSelectScreen)]:
            self.sm.add_widget(cls(name=name))

        # Background layer: try video; else procedural
        bg_path = str((APP_DIR / "assets" / "bg.mov").resolve())
        try:
            if os.path.exists(bg_path):
                root.add_widget(VideoBackground(source=bg_path, size_hint=(1,1)))
            else:
                raise FileNotFoundError
        except Exception:
            root.add_widget(ProceduralBackground(size_hint=(1,1)))

        root.add_widget(self.sm)
        return root

    def _set_auth_status(self, msg:str):
        try: self.sm.get_screen("auth").status = msg
        except Exception: pass

    def _refresh_home(self):
        if self.user_id is None: return
        try:
            home = self.sm.get_screen("home")
            if hasattr(home,"ids"):
                if "crystals" in home.ids:
                    home.ids["crystals"].text = f"Crystals: {dbmod.get_crystals(self.user_id)}"
                if "welcome" in home.ids and self.username:
                    gender, nick = dbmod.get_profile(self.user_id)
                    title = nick or self.username
                    home.ids["welcome"].text = f"Welcome, {title}!"
                if "avatar_img" in home.ids:
                    gender, _nick = dbmod.get_profile(self.user_id)
                    loadout = dbmod.get_loadout(self.user_id)
                    r = SpriteRendererRef(pixel_scale=6); r.set_gender(gender)
                    for slot,item in loadout.items(): r.set_layer(slot, item)
                    buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
                    home.ids["avatar_img"].texture = CoreImage(buf, ext="png").texture
        except Exception as e:
            print("[WARN] _refresh_home:", e)

    # auth
    def signup(self, username, password, nickname, gender):
        u=(username or "").strip(); p=(password or "").strip()
        n=(nickname or "").strip(); g=(gender or "male").strip().lower()
        if not u or not p:
            self._set_auth_status("[color=ffcc66]Enter username & password[/color]"); return
        ok,msg = authmod.register(u,p)
        if not ok:
            self._set_auth_status(f"[color=ff6666]Sign-up failed: {msg}[/color]"); return
        # set profile
        con_uid = self._get_user_id(u)  # local helper
        if con_uid:
            dbmod.set_gender(con_uid, g if g in ("male","female") else "male")
            if n: dbmod.set_nickname(con_uid, n)
        self._set_auth_status("[color=66ff99]Sign-up success. Now login.[/color]")

    def _get_user_id(self, username):
        # resolve user id from username
        try:
            con = dbmod._get_conn(); cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE username=?", (username,))
            row = cur.fetchone(); con.close()
            return row[0] if row else None
        except Exception: return None

    def login(self, username, password):
        u=(username or "").strip(); p=(password or "").strip()
        if not u or not p: self._set_auth_status("[color=ffcc66]Enter username & password[/color]"); return
        ok, tok_or_msg = authmod.login(u,p)
        if ok:
            self.session_token = tok_or_msg; self.username = u; self.user_id = dbmod.get_user_id_by_token(self.session_token)
            self._set_auth_status("[color=66ff99]Login success![/color]"); self.go_home()
        else: self._set_auth_status(f"[color=ff6666]Login failed: {tok_or_msg}[/color]")

    # nav
    def go_home(self): self.sm.current="home"; self._refresh_home()
    def go_study(self): self.sm.current="study"
    def go_gacha(self):
        self.sm.current="gacha"
        try:
            scr = self.sm.get_screen("gacha")
            if "crystals" in scr.ids: scr.ids["crystals"].text = f"Crystals: {dbmod.get_crystals(self.user_id)}"
        except Exception: pass
    def go_inventory(self):
        self.sm.current="inventory"
        try:
            inv = dbmod.list_inventory(self.user_id); scr = self.sm.get_screen("inventory")
            from kivy.uix.button import Button
            def add_many(box_id, items, slot):
                box = scr.ids.get(box_id); 
                if not box: return
                box.clear_widgets()
                for it in items:
                    btn = Button(text=it, size_hint=(None,None), size=(120,40))
                    btn.bind(on_release=lambda b,i=it: self.equip(slot,i))
                    box.add_widget(btn)
            for s,box in [("hair","hair_box"),("top","top_box"),("bottom","bottom_box"),("shoes","shoes_box"),("accessory","acc_box")]:
                add_many(box, inv.get(s, []), s)
        except Exception as e:
            print("[WARN] inventory populate:", e)
    def go_settings(self): self.sm.current="settings"
    def go_gender(self): self.sm.current="gender"
    def logout(self):
        self.session_token=None; self.username=None; self.user_id=None; self.sm.current="auth"

    # gacha / equip / gender
    def gacha_roll(self):
        if self.user_id is None: return
        ok, slot, item, crystals, rarity = dbmod.gacha_roll_once(self.user_id)
        scr = self.sm.get_screen("gacha")
        try:
            if hasattr(scr.ids, "fx") and scr.ids.get("fx"):
                scr.ids["fx"].start_spin(rarity)
        except Exception as e:
            print("[WARN] gacha fx:", e)
        scr.status = (f"[color=66ff99]{rarity} {slot}: {item}[/color]" if ok else "[color=ff6666]Not enough crystals.[/color]")
        try:
            if "crystals" in scr.ids: scr.ids["crystals"].text = f"Crystals: {crystals}"
            from PIL import Image
            r = SpriteRendererRef(pixel_scale=6)
            gender, _ = dbmod.get_profile(self.user_id)
            r.set_gender(gender)
            r.set_layer(slot, item)
            buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
            tex = CoreImage(buf, ext="png").texture
            if "result_img" in scr.ids: scr.ids["result_img"].texture = tex
        except Exception: pass
        self._refresh_home()

    def gacha_roll_10(self):
        if self.user_id is None: return
        ok, results, crystals = dbmod.gacha_roll_ten(self.user_id)
        scr = self.sm.get_screen("gacha")
        if not ok:
            scr.status = "[color=ff6666]Not enough crystals for 10x.[/color]"
        else:
            summary = ", ".join([f"{r}:{s}" for (s, _i, r) in results[:3]]) + (" ..." if len(results)>3 else "")
            scr.status = f"[color=66ff99]10x result: {summary}[/color]"
        try:
            if "crystals" in scr.ids: scr.ids["crystals"].text = f"Crystals: {crystals}"
        except Exception: pass
        self._refresh_home()

    def equip(self, slot, item):
        if self.user_id is None: return
        dbmod.set_loadout(self.user_id, slot, item); self._refresh_home()

    def set_gender(self, gender):
        if self.user_id is None: return
        dbmod.set_gender(self.user_id, gender); self._refresh_home()

if __name__ == "__main__":
    StudySagaApp().run()
