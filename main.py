
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

import db as DB
import auth as AUTH

Window.clearcolor = (0.12,0.13,0.16,1)

class AuthScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=24, spacing=12)
        title = Label(text="StudySaga", font_size="44sp", size_hint_y=None, height=64)
        self.email = TextInput(hint_text="ID / Email", size_hint_y=None, height=44, multiline=False)
        self.pw    = TextInput(hint_text="Password", password=True, size_hint_y=None, height=44, multiline=False)

        # Gender row
        row_gender = BoxLayout(size_hint_y=None, height=44, spacing=10)
        row_gender.add_widget(Label(text="Gender", size_hint_x=0.25))
        self.male = ToggleButton(text="Male", group="gender")
        self.female = ToggleButton(text="Female", group="gender", state="down")
        row_gender.add_widget(self.male); row_gender.add_widget(self.female)

        # Buttons
        row_btn = BoxLayout(size_hint_y=None, height=44, spacing=10)
        btn_login = Button(text="Login")
        btn_reg   = Button(text="Register")
        btn_login.bind(on_release=lambda *_: App.get_running_app().do_login(self.email.text, self.pw.text))
        btn_reg.bind(on_release=lambda *_: App.get_running_app().do_register(self.email.text, self.pw.text, "male" if self.male.state=="down" else "female"))

        row_btn.add_widget(btn_login); row_btn.add_widget(btn_reg)

        self.msg = Label(text="", size_hint_y=None, height=28)

        root.add_widget(title)
        root.add_widget(self.email)
        root.add_widget(self.pw)
        root.add_widget(row_gender)
        root.add_widget(row_btn)
        root.add_widget(self.msg)
        self.add_widget(root)

class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=20, spacing=8)
        self.hello = Label(text="Hi!", font_size="22sp", size_hint_y=None, height=36)
        btns = BoxLayout(size_hint_y=None, height=44, spacing=10)
        for name in ["Study","Gacha","Inventory","Settings","Achievements"]:
            b = Button(text=name); b.bind(on_release=lambda _b, n=name.lower(): App.get_running_app().go(n))
            btns.add_widget(b)
        root.add_widget(self.hello); root.add_widget(btns)
        self.add_widget(root)

class StudySagaApp(App):
    user=None; profile={}; token=""
    def build(self):
        DB.bootstrap()
        self.sm = ScreenManager(transition=NoTransition())
        self.auth = AuthScreen(name="auth")
        self.home = HomeScreen(name="home")
        self.sm.add_widget(self.auth); self.sm.add_widget(self.home)
        self.sm.current = "auth"
        return self.sm

    def go(self, name): 
        if name in [s.name for s in self.sm.screens]:
            self.sm.current = name

    def set_msg(self, txt): 
        if hasattr(self.auth, "msg"): self.auth.msg.text = txt

    def do_register(self, email, pw, gender):
        ok, msg = AUTH.register(email.strip(), pw.strip(), (gender or 'female').strip())
        self.set_msg(msg)

    def do_login(self, email, pw):
        ok, msg, user = AUTH.login(email.strip(), pw.strip())
        self.set_msg(msg)
        if not ok: 
            return
        # Save profile and switch to Home
        self.user = user
        self.token = user["token"]
        self.profile = {
            "id": user["id"],
            "email": user["email"],
            "nickname": user.get("nickname",""),
            "gender": user.get("gender","female")
        }
        self.home.hello.text = f"Hi, {self.profile.get('nickname','')}! ({self.profile.get('gender','?')})"
        self.go("home")  # <-- navigate after successful login

if __name__=="__main__":
    StudySagaApp().run()
