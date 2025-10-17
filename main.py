
import os, time
os.environ["KIVY_NO_ARGS"]="1"
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.lang import Builder

import db as DB
import auth as AUTH

Window.clearcolor = (0.12,0.13,0.16,1)

# Load KV files
Builder.load_file('auth.kv')
Builder.load_file('home.kv')
Builder.load_file('study.kv')
Builder.load_file('inventory.kv')
Builder.load_file('gacha.kv')
Builder.load_file('settings.kv')
Builder.load_file('achievements.kv')

class AuthScreen(Screen):
    pass

class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=20, spacing=8)
        self.hello = Label(text="Hi!", font_size="22sp", size_hint_y=None, height=36)
        
        # Back to auth button
        btn_logout = Button(text="Logout", size_hint_y=None, height=36)
        btn_logout.bind(on_release=lambda _: App.get_running_app().go("auth"))
        
        # Navigation buttons
        btns = BoxLayout(size_hint_y=None, height=44, spacing=10)
        for name in ["Study","Gacha","Inventory","Settings","Achievements"]:
            b = Button(text=name)
            b.bind(on_release=lambda _b, n=name.lower(): App.get_running_app().go(n))
            btns.add_widget(b)
        
        root.add_widget(self.hello)
        root.add_widget(btns)
        root.add_widget(btn_logout)
        self.add_widget(root)

# Define other screens (will be styled by KV files)
class StudyScreen(Screen):
    pass

class InventoryScreen(Screen):
    pass

class GachaScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class AchievementsScreen(Screen):
    pass

# Theme object for KV files
class Theme:
    bg = (0.12, 0.13, 0.16, 1)
    card = (0.18, 0.19, 0.22, 1)
    text = (0.95, 0.95, 0.97, 1)
    muted = (0.65, 0.65, 0.67, 1)
    accent = (0.2, 0.6, 0.86, 1)
    accent_text = (1, 1, 1, 1)
    bronze = (0.8, 0.5, 0.2, 1)
    silver = (0.75, 0.75, 0.78, 1)
    gold = (1.0, 0.84, 0.0, 1)

class StudySagaApp(App):
    user=None; profile={}; token=""; crystals=100
    theme = Theme()
    
    def build(self):
        DB.bootstrap()
        self.sm = ScreenManager(transition=NoTransition())
        
        # Add all screens
        self.auth = AuthScreen(name="auth")
        self.home = HomeScreen(name="home")
        self.study_screen = StudyScreen(name="study")
        self.inventory_screen = InventoryScreen(name="inventory")
        self.gacha_screen = GachaScreen(name="gacha")
        self.settings_screen = SettingsScreen(name="settings")
        self.achievements_screen = AchievementsScreen(name="achievements")
        
        self.sm.add_widget(self.auth)
        self.sm.add_widget(self.home)
        self.sm.add_widget(self.study_screen)
        self.sm.add_widget(self.inventory_screen)
        self.sm.add_widget(self.gacha_screen)
        self.sm.add_widget(self.settings_screen)
        self.sm.add_widget(self.achievements_screen)
        
        self.sm.current = "auth"
        return self.sm

    def go(self, name): 
        if name in [s.name for s in self.sm.screens]:
            self.sm.current = name
        else:
            print(f"Screen '{name}' not found!")

    def set_msg(self, txt): 
        try:
            self.auth.ids.msg.text = txt
        except:
            pass

    def do_register(self, email, pw, gender='female'):
        ok, msg = AUTH.register(email.strip(), pw.strip(), (gender or 'female').strip())
        self.set_msg(msg)
        if ok:
            self.set_msg("Registration successful! Please login.")

    def do_login(self, email, pw):
        ok, msg, user = AUTH.login(email.strip(), pw.strip())
        self.set_msg(msg)
        if not ok: 
            return
        # Save profile and switch to Home
        self.user = user
        self.token = user["token"]
        self.crystals = user.get("crystals", 100)
        self.profile = {
            "id": user["id"],
            "email": user["email"],
            "nickname": user.get("nickname",""),
            "gender": user.get("gender","female")
        }
        self.home.hello.text = f"Hi, {self.profile.get('nickname','User')}! ({self.profile.get('gender','?')})"
        self.go("home")

    # Placeholder functions for KV files
    def pomodoro_start(self, work_min, break_min, cycles):
        print(f"Pomodoro: {work_min}min work, {break_min}min break, {cycles} cycles")
        
    def study_start(self, minutes):
        print(f"Study session: {minutes} minutes")
    
    def study_stop(self):
        print("Study session stopped")
        
    def do_gacha(self, tier):
        print(f"Gacha roll: {tier}")
        
    def refresh_inventory(self, search="", tier="all"):
        print(f"Refresh inventory: search={search}, tier={tier}")

if __name__=="__main__":
    StudySagaApp().run()
