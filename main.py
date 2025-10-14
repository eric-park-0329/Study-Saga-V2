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
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.image import Image as CoreImage

from sprite_renderer_ref import SpriteRendererRef
from studysaga import db as dbmod
from studysaga import auth as authmod

class AnimatedBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self._instr = InstructionGroup()
        self.canvas.add(self._instr)
        Clock.schedule_interval(self._tick, 1/30)
        self.bind(pos=self._redraw, size=self._redraw)
    def _redraw(self, *a): self._tick(0)
    def _tick(self, dt):
        self._t += dt; self._instr.clear()
        Color(0.05,0.07,0.10,1.0); Rectangle(pos=self.pos, size=self.size)
        cols,rows = 32,18; w = max(1,self.width/cols); h = max(1,self.height/rows)
        import math
        for r in range(rows):
            for c in range(cols):
                phase = (c*0.37 + r*0.23); v = 0.08 + 0.06*math.sin(self._t*1.2 + phase)
                a = 0.12 + (0.08 if r%2==0 else 0.03) + v
                Color(0.6,0.8,1.0, min(max(a,0.0), 0.35)); Rectangle(pos=(self.x+c*w,self.y+r*h), size=(w,h))

from kivy.animation import Animation
from kivy.properties import NumericProperty, ListProperty

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
    status = StringProperty(""); status_msg = StringProperty("")
    def on_status(self, *a): 
        if self.status_msg != self.status: self.status_msg = self.status
    def on_status_msg(self, *a):
        if self.status != self.status_msg: self.status = self.status_msg

class HomeScreen(Screen): pass
class StudyScreen(Screen): status = StringProperty("")
class GachaScreen(Screen): 
    status = StringProperty("")
    result_image = ObjectProperty(None)
class InventoryScreen(Screen): pass
class SettingsScreen(Screen): pass
class GenderSelectScreen(Screen): pass

# Load KV files
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
        root.add_widget(AnimatedBackground(size_hint=(1,1)))
        root.add_widget(self.sm); return root

    def _set_auth_status(self, msg:str):
        try: self.sm.get_screen("auth").status = msg
        except Exception: pass

    def _refresh_home(self):
        if self.user_id is None: return
        try:
            home = self.sm.get_screen("home")
            if hasattr(home,"ids") and "crystals" in home.ids:
                home.ids["crystals"].text = f"Crystals: {dbmod.get_crystals(self.user_id)}"
            gender = dbmod.get_gender(self.user_id)
            loadout = dbmod.get_loadout(self.user_id)
            r = SpriteRendererRef(pixel_scale=6); r.set_gender(gender)
            for slot,item in loadout.items(): r.set_layer(slot, item)
            buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
            tex = CoreImage(buf, ext="png").texture
            if "avatar_img" in home.ids: home.ids["avatar_img"].texture = tex
            if "welcome" in home.ids and self.username: home.ids["welcome"].text = f"Welcome, {self.username}!"
        except Exception as e:
            print("[WARN] _refresh_home:", e)

    # auth
    def signup(self, username, password):
        u=(username or "").strip(); p=(password or "").strip()
        if not u or not p: self._set_auth_status("[color=ffcc66]Enter username & password[/color]"); return
        ok,msg = authmod.register(u,p)
        self._set_auth_status("[color=66ff99]Sign-up success. Now login.[/color]" if ok else f"[color=ff6666]Sign-up failed: {msg}[/color]")

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
                    box.add_widget(Button(text=it, on_release=lambda b,i=it: self.equip(slot,i)))
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
        ok, slot, item, crystals, rarity = dbmod.gacha_roll(self.user_id)
        scr = self.sm.get_screen("gacha")
        # Trigger animation effect & show result
        try:
            if hasattr(scr.ids, "fx") and scr.ids.get("fx"):
                scr.ids["fx"].start_spin(rarity)
        except Exception as e:
            print("[WARN] gacha fx:", e)
        scr.status = (f"[color=66ff99]{rarity} {slot}: {item}[/color]" if ok else "[color=ff6666]Not enough crystals.[/color]")
        try:
            if "crystals" in scr.ids: scr.ids["crystals"].text = f"Crystals: {crystals}"
            # result image preview
            from PIL import Image
            r = SpriteRendererRef(pixel_scale=6)
            # show item alone on base gender
            gender = dbmod.get_gender(self.user_id)
            r.set_gender(gender)
            r.set_layer(slot, item)
            buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
            tex = CoreImage(buf, ext="png").texture
            if "result_img" in scr.ids: scr.ids["result_img"].texture = tex
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
