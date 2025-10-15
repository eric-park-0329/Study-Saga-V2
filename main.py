import os, io
from pathlib import Path
os.environ["KIVY_NO_ARGS"]="1"
APP_DIR = Path(__file__).resolve().parent
try: os.chdir(APP_DIR)
except Exception: pass

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.graphics import Rectangle, Color, InstructionGroup
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, ListProperty

from sprite_renderer_ref import SpriteRendererRef
from studysaga import db as dbmod
from studysaga import auth as authmod

# -------- Background --------
class Starfield(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._t = 0.0
        self._instr = InstructionGroup(); self.canvas.add(self._instr)
        import random
        self._stars = [(random.random(), random.random(), 0.6+0.4*random.random()) for _ in range(240)]
        Clock.schedule_interval(self._tick, 1/60)
        self.bind(pos=self._tick, size=self._tick)
    def _tick(self, *a):
        import math
        self._t += 0.016
        w,h = max(1,self.width), max(1,self.height)
        self._instr.clear()
        Color(0.03,0.04,0.06,1); Rectangle(pos=self.pos, size=self.size)
        for i in range(4):
            amp = 18 + i*10; a = 0.07 + i*0.03
            y = self.y + h*(0.2 + 0.15*i) + math.sin(self._t*0.5 + i)*amp
            Color(0.35,0.55,0.95, a); Rectangle(pos=(self.x, y), size=(w, h*0.12))
        for i,(sx,sy,tw) in enumerate(self._stars):
            px = self.x + ((sx*w + self._t*20) % w); py = self.y + (sy*h)
            a = 0.15 + 0.25*abs(math.sin(self._t*tw + i))
            Color(0.8,0.9,1.0,a); Rectangle(pos=(px,py), size=(2,2))

# -------- FX --------
class GachaFX(Widget):
    angle = NumericProperty(0); scale = NumericProperty(1); color = ListProperty([1,1,1,0.2])
    def burst(self, rarity="Common"):
        colors = {"Common":(1,1,1,0.15),"Rare":(0.6,0.8,1,0.25),"Epic":(0.7,0.6,1,0.35),"Legendary":(1,0.84,0.2,0.45)}
        self.color = colors.get(rarity,(1,1,1,0.2)); self.angle = 0; self.scale = 0.6
        (Animation(angle=360, scale=1.2, d=0.5, t='out_cubic') + Animation(angle=720, scale=1.0, d=0.5, t='out_back')).start(self)

# -------- Screens --------
class AuthScreen(Screen):
    status = StringProperty("")
    status_msg = StringProperty("")
class HomeScreen(Screen): pass
class StudyScreen(Screen):
    status = StringProperty("Timer: 00:00")
class GachaScreen(Screen):
    status = StringProperty("")
class InventoryScreen(Screen): pass
class SettingsScreen(Screen): pass

# Load KV
for rel in ("ui/auth.kv","ui/home.kv","ui/study.kv","ui/gacha.kv","ui/inventory.kv","ui/settings.kv"):
    p = APP_DIR/rel
    if p.exists(): Builder.load_file(str(p))

class StudySagaApp(App):
    session_token=None; username=None; user_id=None
    inv_slot = "hair"
    def build(self):
        dbmod.bootstrap(); dbmod.cleanup_expired_sessions(30)
        root = FloatLayout()
        self.sm = ScreenManager(transition=NoTransition())
        for name, cls in [("auth",AuthScreen),("home",HomeScreen),("study",StudyScreen),
                          ("gacha",GachaScreen),("inventory",InventoryScreen),("settings",SettingsScreen)]:
            self.sm.add_widget(cls(name=name))
        root.add_widget(Starfield(size_hint=(1,1)))
        root.add_widget(self.sm)
        return root

    # Auth
    def signup(self, u,p,nick,gender):
        u=(u or "").strip(); p=(p or "").strip(); nick=(nick or "").strip()
        ok,msg = authmod.register(u,p)
        if not ok:
            self.sm.get_screen("auth").status = f"[color=ffcc66]Sign-up failed: {msg}[/color]"; return
        uid = self._uid_by_name(u)
        if uid:
            dbmod.set_gender(uid, "female" if gender=="female" else "male")
            if nick: dbmod.set_nickname(uid, nick)
        self.sm.get_screen("auth").status = "[color=66ff99]Sign-up success. Please login.[/color]"

    def login(self, u,p):
        ok,tok = authmod.login((u or "").strip(), (p or "").strip())
        if not ok:
            self.sm.get_screen("auth").status = "[color=ff6666]Login failed[/color]"; return
        self.session_token = tok; self.username=u
        self.user_id = dbmod.get_user_id_by_token(self.session_token)
        self.go_home()

    def _uid_by_name(self, u):
        try:
            con = dbmod._get_conn(); cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE username=?", (u,))
            r=cur.fetchone(); con.close(); return r[0] if r else None
        except Exception: return None

    # Nav
    def go_home(self):
        self.sm.current="home"; Clock.schedule_once(lambda *_: self._refresh_home(),0)
    def go_study(self): self.sm.current="study"
    def go_gacha(self):
        self.sm.current="gacha"
        scr=self.sm.get_screen("gacha")
        scr.ids.crystals.text = f"Crystals: {dbmod.get_crystals(self.user_id)}"
    def go_inventory(self):
        self.sm.current="inventory"; Clock.schedule_once(lambda *_: self.inv_select(self.inv_slot),0)
    def go_settings(self):
        self.sm.current="settings"
        scr=self.sm.get_screen("settings")
        g,nick = dbmod.get_profile(self.user_id)
        scr.ids.nick_input.text = nick or ""
        scr.ids.gender_male.state = "down" if g=="male" else "normal"
        scr.ids.gender_female.state = "down" if g=="female" else "normal"
    def logout(self): self.session_token=None; self.username=None; self.user_id=None; self.sm.current="auth"

    # Home avatar
    def _refresh_home(self):
        if self.user_id is None: return
        try:
            home = self.sm.get_screen("home")
            g,nick = dbmod.get_profile(self.user_id)
            home.ids.welcome.text = f"Welcome, {(nick or self.username)}!"
            home.ids.crystals.text = f"Crystals: {dbmod.get_crystals(self.user_id)}"
            loadout = dbmod.get_loadout(self.user_id)
            r = SpriteRendererRef(scale=6); r.set_gender(g)
            for s,i in loadout.items():
                if i: r.set_layer(s,i)
            if not any(loadout.values()):
                items = dbmod.default_items()
                starter = {"hair": items["hair"][0], "top": items["top"][0], "bottom": items["bottom"][0], "shoes": items["shoes"][0]}
                for s,i in starter.items(): dbmod.set_loadout(self.user_id,s,i); r.set_layer(s,i)
            buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
            home.ids.avatar.texture = CoreImage(buf, ext="png").texture
        except Exception as e:
            print("[WARN] refresh_home:", e)

    # Study
    def study_start(self):
        scr = self.sm.get_screen("study")
        self._study_t = 0; self._study_ev = Clock.schedule_interval(self._study_tick, 1.0)
        scr.status = "Timer: 00:00"
    def study_pause(self):
        if getattr(self,'_study_ev',None): self._study_ev.cancel(); self._study_ev=None
    def _study_tick(self, dt):
        self._study_t = getattr(self,'_study_t',0)+1
        m,s = divmod(self._study_t,60)
        scr = self.sm.get_screen("study"); scr.status = f"Timer: {m:02d}:{s:02d}"
        if self._study_t % 60 == 0 and self.user_id:
            cur = dbmod.get_crystals(self.user_id); dbmod.set_crystals(self.user_id, cur+5)
            self._refresh_home()

    # Inventory
    def inv_select(self, slot):
        self.inv_slot = slot
        scr = self.sm.get_screen("inventory")
        grid = scr.ids.grid; grid.clear_widgets()
        inv = dbmod.list_inventory(self.user_id)
        items = inv.get(slot, [])
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.image import Image
        from kivy.uix.button import Button
        if not items:
            # show some defaults as disabled preview
            for name in dbmod.default_items()[slot][:12]:
                cell = BoxLayout(orientation='vertical', size_hint_y=None, height='120dp', padding=5, spacing=4)
                # thumbnail
                buf = io.BytesIO(); r = SpriteRendererRef(scale=4); g,_ = dbmod.get_profile(self.user_id); r.set_gender(g); r.set_layer(slot,name)
                r.render().save(buf, format="PNG"); buf.seek(0)
                cell.add_widget(Image(texture=CoreImage(buf, ext="png").texture, size_hint=(1,None), height='84dp'))
                cell.add_widget(Button(text="Not owned", disabled=True, size_hint=(1,None), height='28dp'))
                grid.add_widget(cell)
            return
        for name in items:
            cell = BoxLayout(orientation='vertical', size_hint_y=None, height='120dp', padding=5, spacing=4)
            buf = io.BytesIO(); r = SpriteRendererRef(scale=4); g,_ = dbmod.get_profile(self.user_id); r.set_gender(g); r.set_layer(slot,name)
            r.render().save(buf, format="PNG"); buf.seek(0)
            cell.add_widget(Image(texture=CoreImage(buf, ext="png").texture, size_hint=(1,None), height='84dp'))
            b = Button(text="Equip", size_hint=(1,None), height='28dp')
            b.bind(on_release=lambda btn, s=slot, it=name: self._equip(s,it))
            cell.add_widget(b); grid.add_widget(cell)
    def _equip(self, slot, item):
        dbmod.set_loadout(self.user_id, slot, item); self._refresh_home()

    # Gacha
    def gacha_roll(self, times=1):
        scr = self.sm.get_screen("gacha")
        if times==1:
            ok, res, crystals = dbmod.roll_once(self.user_id)
            if not ok: scr.status = "[color=ff6666]Not enough crystals[/color]"; return
            slot,item,rarity = res
            scr.ids.fx.burst(rarity); self._animate_chest(rarity); self._show_item_preview(slot,item)
            scr.ids.crystals.text = f"Crystals: {crystals}"
        else:
            ok, results, crystals = dbmod.roll_ten(self.user_id)
            if not ok: scr.status = "[color=ff6666]Not enough crystals for 10x[/color]"; return
            scr.ids.fx.burst("Epic"); self._animate_chest("Epic")
            if results: slot,item,rarity = results[0]; self._show_item_preview(slot,item)
            scr.ids.crystals.text = f"Crystals: {crystals}"
        self._refresh_home()

    def _show_item_preview(self, slot, item):
        scr = self.sm.get_screen("gacha")
        g,_ = dbmod.get_profile(self.user_id); r = SpriteRendererRef(scale=5); r.set_gender(g); r.set_layer(slot,item)
        buf = io.BytesIO(); r.render().save(buf, format="PNG"); buf.seek(0)
        scr.ids.result.texture = CoreImage(buf, ext="png").texture
        scr.status = f"[color=66ff99]New {slot}: {item}[/color]"

    def _animate_chest(self, rarity="Common"):
        scr = self.sm.get_screen("gacha")
        gl = scr.ids.glow; gl.opacity = 0.0; gl.scale = 0.8
        col = {"Common":(1,1,1,0.25),"Rare":(0.6,0.8,1,0.35),"Epic":(0.7,0.6,1,0.45),"Legendary":(1,0.84,0.2,0.6)}.get(rarity,(1,1,1,0.3))
        gl.color = col; Animation(opacity=1.0, scale=1.1, d=0.25).start(gl)
        chest = scr.ids.chest
        a1 = Animation(scale=1.05, d=0.15, t='out_back'); a2 = Animation(scale=1.0, d=0.1)
        def open_lid(*_): chest.source = "assets/chest_open.png"
        a1.bind(on_complete=lambda *_: open_lid()); (a1 + a2).start(chest)

    # Settings
    def save_settings(self, nickname, male_state, female_state):
        if self.user_id is None: return
        nick = (nickname or "").strip()
        if nick: dbmod.set_nickname(self.user_id, nick)
        if female_state=='down': dbmod.set_gender(self.user_id, "female")
        elif male_state=='down': dbmod.set_gender(self.user_id, "male")
        self._refresh_home()

if __name__ == "__main__":
    StudySagaApp().run()
