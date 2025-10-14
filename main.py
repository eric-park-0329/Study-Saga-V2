from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
from kivy.core.window import Window
Window.size = (420, 860)

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.uix.widget import Widget

from studysaga.services.notifications import notify_info
from studysaga.services.gacha import GachaMachine
from studysaga.services.pomodoro import PomodoroController
import sqlite3, os, time, datetime, json, math, random
from io import BytesIO

from studysaga.db import DB
from sprite_renderer_ref import SpriteRendererRef

class PixelBorder(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(lambda dt: self._redraw(), 0)
    
    def _redraw(self, *args):
        from kivy.graphics import Color, Rectangle
        self.canvas.before.clear()
        w, h = self.size
        x, y = self.pos
        border = 3
        
        with self.canvas.before:
            Color(0.18, 0.12, 0.08, 1)
            Rectangle(pos=(x, y), size=(w, h))
            Color(0.25, 0.18, 0.12, 1)
            Rectangle(pos=(x+border, y+border), size=(w-2*border, h-2*border))

class GameIcon(Widget):
    kind = StringProperty("hero")
    equipment = {}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=lambda *_: self._redraw(),
                  size=lambda *_: self._redraw(),
                  kind=lambda *_: self._redraw())
        Clock.schedule_once(lambda dt: self._redraw(), 0)
    
    def set_equipment(self, equipment):
        self.equipment = equipment
        self._redraw()
    
    def hex_to_rgb(self, hex_color):
        if not hex_color or hex_color == 'None':
            return (0.5, 0.5, 0.5, 1)
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)) + (1,)
    
    def _redraw(self):
        from kivy.graphics import Color, Rectangle
        from kivy.graphics.texture import Texture
        self.canvas.clear()
        w, h = self.size
        x, y = self.pos
        px = max(1, int(w / 16))
        
        with self.canvas:
            if self.kind == "hero":
                # Use PIL-based renderer for hero character
                try:
                    # Build appearance from equipment
                    appearance = {
                        "sex": self.equipment.get('gender', 'female'),
                        "skin_color": self.equipment.get('skin_color', '#F5DEB3'),
                        "hair_color": (self.equipment.get('hair') or {}).get('color', '#8B4513'),
                        "shirt_color": (self.equipment.get('shirt') or {}).get('color', '#4169E1'),
                        "pants_color": (self.equipment.get('pants') or {}).get('color', '#4682B4'),
                        "shoes_color": (self.equipment.get('shoes') or {}).get('color', '#8B4513'),
                        "belt_color": "#A1742C",
                        "has_glasses": self.equipment.get('glasses') is not None,
                        "glasses_color": (self.equipment.get('glasses') or {}).get('color', '#000000'),
                        "has_mustache": self.equipment.get('mustache') is not None,
                        "facial_hair_color": (self.equipment.get('mustache') or {}).get('color', '#2C1B18')
                    }
                    
                    # Render using SpriteRendererRef
                    renderer = SpriteRendererRef(sex=appearance["sex"], scale=1)
                    pil_img = renderer.render(appearance)
                    
                    # Convert PIL image to Kivy texture
                    pil_img = pil_img.convert('RGBA')
                    img_data = pil_img.tobytes()
                    texture = Texture.create(size=(pil_img.width, pil_img.height), colorfmt='rgba')
                    texture.blit_buffer(img_data, colorfmt='rgba', bufferfmt='ubyte')
                    texture.flip_vertical()
                    
                    # Calculate aspect ratio to fit in widget
                    img_w, img_h = pil_img.size
                    aspect = img_w / img_h
                    if w / h > aspect:
                        draw_h = h
                        draw_w = h * aspect
                    else:
                        draw_w = w
                        draw_h = w / aspect
                    
                    draw_x = x + (w - draw_w) / 2
                    draw_y = y + (h - draw_h) / 2
                    
                    Color(1, 1, 1, 1)
                    Rectangle(texture=texture, pos=(draw_x, draw_y), size=(draw_w, draw_h))
                except Exception as e:
                    # Fallback to simple colored square if rendering fails
                    import traceback
                    Color(0.8, 0.2, 0.2, 1)
                    Rectangle(pos=(x, y), size=(w, h))
                    print(f"Hero render error: {e}")
                    traceback.print_exc()
            
            elif self.kind == "tree":
                Color(0.45, 0.3, 0.2, 1)
                Rectangle(pos=(x + 7*px, y), size=(2*px, 8*px))
                Color(0.25, 0.6, 0.3, 1)
                Rectangle(pos=(x + 5*px, y + 8*px), size=(6*px, 2*px))
                Rectangle(pos=(x + 4*px, y + 10*px), size=(8*px, 2*px))
                Rectangle(pos=(x + 5*px, y + 12*px), size=(6*px, 2*px))
                Color(0.2, 0.5, 0.25, 1)
                Rectangle(pos=(x + 6*px, y + 14*px), size=(4*px, px))
            
            elif self.kind == "crystal":
                Color(0.4, 0.85, 1.0, 1)
                Rectangle(pos=(x + 7*px, y + 12*px), size=(2*px, 2*px))
                Color(0.3, 0.7, 0.9, 1)
                Rectangle(pos=(x + 6*px, y + 10*px), size=(4*px, 2*px))
                Rectangle(pos=(x + 5*px, y + 8*px), size=(6*px, 2*px))
                Rectangle(pos=(x + 6*px, y + 6*px), size=(4*px, 2*px))
                Color(0.5, 0.95, 1.0, 1)
                Rectangle(pos=(x + 7*px, y + 8*px), size=(2*px, px))
            
            elif self.kind == "scroll":
                Color(0.95, 0.9, 0.75, 1)
                Rectangle(pos=(x + 4*px, y + 5*px), size=(8*px, 6*px))
                Color(0.8, 0.7, 0.5, 1)
                Rectangle(pos=(x + 3*px, y + 4*px), size=(2*px, 8*px))
                Rectangle(pos=(x + 11*px, y + 4*px), size=(2*px, 8*px))
            
            elif self.kind == "tome":
                Color(0.6, 0.15, 0.15, 1)
                Rectangle(pos=(x + 4*px, y + 4*px), size=(8*px, 8*px))
                Color(0.9, 0.8, 0.7, 1)
                Rectangle(pos=(x + 7*px, y + 4*px), size=(2*px, 8*px))
                Color(0.7, 0.2, 0.2, 1)
                Rectangle(pos=(x + 5*px, y + 5*px), size=(px, px))
            
            elif self.kind == "cape":
                Color(0.95, 0.75, 0.2, 1)
                Rectangle(pos=(x + 5*px, y + 8*px), size=(6*px, 4*px))
                Rectangle(pos=(x + 6*px, y + 4*px), size=(4*px, 4*px))
                Color(1, 0.85, 0.3, 1)
                Rectangle(pos=(x + 6*px, y + 9*px), size=(px, px))
            
            elif self.kind == "pouch":
                Color(0.65, 0.45, 0.25, 1)
                Rectangle(pos=(x + 5*px, y + 4*px), size=(6*px, 6*px))
                Color(0.5, 0.35, 0.2, 1)
                Rectangle(pos=(x + 6*px, y + 10*px), size=(4*px, 2*px))
                Color(0.75, 0.6, 0.4, 1)
                Rectangle(pos=(x + 7*px, y + 6*px), size=(2*px, 2*px))

class Star(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(lambda dt: self._redraw(), 0)
    
    def _redraw(self, *args):
        from kivy.graphics import Color, Rectangle
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, random.uniform(0.6, 0.9))
            Rectangle(pos=self.pos, size=(2, 2))

KV = r'''
#:import dp kivy.metrics.dp
#:import Factory kivy.factory.Factory
#:import NoTransition kivy.uix.screenmanager.NoTransition

<PixelButton@Button>:
    background_normal: ''
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: 0.25, 0.18, 0.12, 1
        Rectangle:
            pos: self.x, self.y
            size: self.width, self.height
        Color:
            rgba: 0.4, 0.3, 0.2, 1
        Rectangle:
            pos: self.x + 2, self.y + 2
            size: self.width - 4, self.height - 4
        Color:
            rgba: 0.55, 0.4, 0.25, 1 if self.state == 'normal' else (0.45, 0.33, 0.2, 1)
        Rectangle:
            pos: self.x + 4, self.y + 4
            size: self.width - 8, self.height - 8
    color: 1, 0.95, 0.85, 1
    font_size: '16sp'

<PixelLabel@Label>:
    color: 1, 0.95, 0.85, 1

<Header@BoxLayout>:
    size_hint_y: None
    height: dp(60)
    padding: dp(8), 0
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.15, 0.1, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.25, 0.18, 0.12, 1
        Rectangle:
            pos: self.x, self.y + 2
            size: self.width, self.height - 4
    PixelButton:
        text: "←"
        size_hint_x: None
        width: dp(50)
        opacity: 1 if app.can_go_back else 0
        disabled: not app.can_go_back
        on_release: app.go_back()
    PixelLabel:
        text: "⚔ Study Saga ⚔"
        font_size: '20sp'
        bold: True
        color: 1, 0.85, 0.4, 1
    Widget:
    PixelLabel:
        text: app.stats_text
        font_size: '13sp'
        size_hint_x: None
        width: self.texture_size[0] + dp(8)

<HomeScreen@Screen>:
    name: "home"
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        FloatLayout:
            size_hint_y: 0.5
            canvas.before:
                Color:
                    rgba: 0.08, 0.05, 0.12, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.15, 0.1, 0.18, 1
                Rectangle:
                    pos: self.x, self.y
                    size: self.width, self.height * 0.4
            GameIcon:
                kind: "hero"
                size_hint: None, None
                size: dp(80), dp(100)
                pos_hint: {'center_x': 0.5, 'center_y': 0.55}
            GameIcon:
                kind: "tree"
                size_hint: None, None
                size: dp(48), dp(60)
                pos_hint: {'center_x': 0.28, 'y': 0.05}
            GameIcon:
                kind: "tree"
                size_hint: None, None
                size: dp(42), dp(54)
                pos_hint: {'center_x': 0.72, 'y': 0.08}
        BoxLayout:
            padding: dp(16)
            spacing: dp(14)
            orientation: 'vertical'
            PixelLabel:
                text: "⚡ Welcome, Adventurer! ⚡"
                font_size: '20sp'
                size_hint_y: None
                height: dp(36)
                bold: True
                color: 1, 0.85, 0.4, 1
            PixelLabel:
                text: "Study to gain EXP & crystals!\\nConquer dungeons and unlock rewards!"
                color: 0.9, 0.85, 0.7, 1
                halign: 'center'
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1] + dp(8)
            GridLayout:
                cols: 2
                spacing: dp(12)
                size_hint_y: None
                height: dp(200)
                PixelButton:
                    text: "⚔ Study"
                    on_release: app.goto("study")
                PixelButton:
                    text: "🎲 Gacha"
                    on_release: app.goto("gacha")
                PixelButton:
                    text: "🎒 Inventory"
                    on_release: app.goto("inventory")
                PixelButton:
                    text: "👑 Boss"
                    on_release: app.goto("boss")
            PixelButton:
                size_hint_y: None
                height: dp(48)
                text: "⚙ Settings"
                on_release: app.goto("settings")

<InventoryScreen@Screen>:
    name: "inventory"
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        ScrollView:
            GridLayout:
                id: inv_grid
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(16)
                spacing: dp(10)

<StudyScreen@Screen>:
    name: "study"
    on_pre_enter: app.prepare_study_screen()
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(18)
            Widget:
                size_hint_y: 0.1
            PixelLabel:
                text: "⏰ Study Timer ⏰"
                font_size: '26sp'
                size_hint_y: None
                height: dp(42)
                bold: True
                color: 1, 0.85, 0.4, 1
            BoxLayout:
                size_hint_y: None
                height: dp(100)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.1, 0.08, 1
                    Rectangle:
                        pos: self.x + dp(30), self.y
                        size: self.width - dp(60), self.height
                    Color:
                        rgba: 0.25, 0.18, 0.12, 1
                    Rectangle:
                        pos: self.x + dp(34), self.y + 4
                        size: self.width - dp(68), self.height - 8
                PixelLabel:
                    text: app.study_time_text
                    font_size: '56sp'
                    bold: True
                    color: 0.4, 0.9, 1.0, 1
            BoxLayout:
                size_hint_y: None
                height: dp(60)
                spacing: dp(14)
                padding: dp(20), 0
                PixelButton:
                    text: "⏸ Pause" if app.pomo_running else "▶ Start"
                    on_release: app.toggle_pomo()
                    font_size: '18sp'
                PixelButton:
                    text: "↻ Reset"
                    on_release: app.pomo_reset()
                    font_size: '18sp'
            Widget:
            PixelLabel:
                text: "💡 Tip: Adjust timer in Settings"
                color: 0.7, 0.65, 0.5, 1
                size_hint_y: None
                height: dp(28)

<GachaScreen@Screen>:
    name: "gacha"
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(14)
            PixelLabel:
                text: "🎲 Gacha Machine 🎲"
                font_size: '26sp'
                size_hint_y: None
                height: dp(42)
                bold: True
                color: 1, 0.85, 0.4, 1
            PixelLabel:
                text: app.gacha_result
                size_hint_y: None
                height: dp(70)
                font_size: '15sp'
            PixelButton:
                text: "🥉 Bronze Roll (10💎)"
                size_hint_y: None
                height: dp(56)
                on_release: app.roll_gacha('bronze')
            PixelButton:
                text: "🥈 Silver Roll (30💎)"
                size_hint_y: None
                height: dp(56)
                on_release: app.roll_gacha('silver')
            PixelButton:
                text: "🥇 Gold Roll (60💎)"
                size_hint_y: None
                height: dp(56)
                on_release: app.roll_gacha('gold')
            Widget:

<BossScreen@Screen>:
    name: "boss"
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(14)
            PixelLabel:
                text: "👑 Weekly Boss 👑"
                font_size: '26sp'
                size_hint_y: None
                height: dp(42)
                bold: True
                color: 1, 0.85, 0.4, 1
            PixelLabel:
                text: app.weekly_text
                size_hint_y: None
                height: dp(70)
                font_size: '16sp'
            PixelButton:
                text: "🏆 Claim Reward"
                size_hint_y: None
                height: dp(58)
                on_release: app.claim_weekly()
            Widget:

<SettingsScreen@Screen>:
    name: "settings"
    on_pre_enter: app.populate_settings_form()
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.12, 0.08, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Header:
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                PixelLabel:
                    text: "⚙ Settings ⚙"
                    font_size: '26sp'
                    size_hint_y: None
                    height: dp(42)
                    bold: True
                    color: 1, 0.85, 0.4, 1
                PixelLabel:
                    text: "Configure your adventure"
                    size_hint_y: None
                    height: dp(32)
                    color: 0.9, 0.85, 0.7, 1
                GridLayout:
                    cols: 2
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height
                    PixelLabel:
                        text: "Study minutes"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_study
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: dp(40)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                    PixelLabel:
                        text: "Break minutes"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_break
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: dp(40)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                    PixelLabel:
                        text: "Daily goal (min)"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_daily
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: dp(40)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                    PixelLabel:
                        text: "Weekly goal (min)"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_weekly
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: dp(40)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                    PixelLabel:
                        text: "Focus mode"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Switch:
                        id: sw_focus
                        size_hint_y: None
                        height: dp(40)
                    PixelLabel:
                        text: "Background counting"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Switch:
                        id: sw_bg
                        size_hint_y: None
                        height: dp(40)
                    PixelLabel:
                        text: "Character Gender"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: dp(8)
                        PixelButton:
                            id: btn_female
                            text: "♀ Female"
                            on_release: app.set_gender_ui('female')
                            canvas.before:
                                Color:
                                    rgba: (0.6, 0.3, 0.6, 1) if app.db.get_player().get('gender') == 'female' else (0.25, 0.18, 0.12, 1)
                        PixelButton:
                            id: btn_male
                            text: "♂ Male"
                            on_release: app.set_gender_ui('male')
                            canvas.before:
                                Color:
                                    rgba: (0.3, 0.5, 0.7, 1) if app.db.get_player().get('gender') == 'male' else (0.25, 0.18, 0.12, 1)
                    PixelLabel:
                        text: "Blocked packages"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_blocked
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                    PixelLabel:
                        text: "Allowed packages"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_allowed
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                        background_normal: ''
                        background_color: 0.2, 0.15, 0.1, 1
                        foreground_color: 1, 0.95, 0.85, 1
                PixelButton:
                    text: "💾 Save Settings"
                    size_hint_y: None
                    height: dp(52)
                    on_release: app.apply_settings_from_ui()

<Root>:
    HomeScreen:
    InventoryScreen:
    StudyScreen:
    GachaScreen:
    BossScreen:
    SettingsScreen:

'''

class Root(ScreenManager):
    pass

class StudySagaApp(App):
    stats_text = StringProperty("Lvl 1 • 0 EXP • 0💎")
    weekly_text = StringProperty("0 / 600 min this week")
    gacha_result = StringProperty("")
    can_go_back = BooleanProperty(False)
    study_time_text = StringProperty("00:00")
    pomo_running = BooleanProperty(False)
    focus_mode_enabled = BooleanProperty(False)
    background_count = BooleanProperty(False)
    blocked_packages = ListProperty([])
    allowed_packages = ListProperty([])
    _pomo_ev = None
    _pomo_remaining = 0
    _pomo_total = 0
    _pomo_last_ts = None
    _paused_at = None
    
    def build(self):
        self.title = "Study Saga"
        self.db = DB("studysaga.db")
        self.player = self.db.ensure_player()
        self.gacha = GachaMachine(self.db)
        self.pomo = PomodoroController(self, self.db)
        self.update_stats()
        self.refresh_weekly()
        try:
            ui = Builder.load_string(KV)
            if ui is None:
                ui = Root()
        except Exception as e:
            import traceback
            traceback.print_exc()
            from kivy.uix.label import Label
            return Label(text=f"KV load error: {e}")
        return ui

    def on_start(self):
        if not self.root or not hasattr(self.root, "get_screen"):
            return
        self.refresh_inventory()
        self.update_character()
        Window.bind(on_keyboard=self._on_keyboard)
    
    def update_character(self):
        equipment = self.db.get_equipment()
        home_screen = self.root.get_screen("home")
        for child in home_screen.walk():
            if isinstance(child, GameIcon) and child.kind == "hero":
                child.set_equipment(equipment)
                break

    def on_pause(self):
        if self.pomo_running:
            self._paused_at = time.time()
        return True

    def on_resume(self):
        if self.pomo_running and self.background_count:
            now = time.time()
            last = self._paused_at or self._pomo_last_ts
            if last:
                elapsed = int(max(0, now - last))
                if elapsed > 0:
                    self._pomo_remaining -= elapsed
                    if self._pomo_remaining <= 0:
                        self._pomo_remaining = 0
                        self.study_time_text = self._format_time(0)
                        self.pomo_pause()
                        studied = max(1, self._pomo_total // 60)
                        exp, crystals = self.reward_for_study(studied)
                        notify_info("Study complete", f"+{exp} EXP, +{crystals}💎")
                    else:
                        self.study_time_text = self._format_time(self._pomo_remaining)
        self._paused_at = None

    def _on_keyboard(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            self.go_back()
            return True
        return False

    def goto(self, name):
        self.root.current = name
        self.can_go_back = (name != "home")

    def go_back(self):
        if self.root.current != "home":
            self.root.current = "home"
        self.can_go_back = False

    def update_stats(self):
        self.player = self.db.get_player()
        self.stats_text = f"Lvl {self.player['level']} • {self.player['exp']} EXP • {self.player['crystals']}💎"

    def refresh_weekly(self):
        total = self.db.weekly_minutes()
        self.weekly_text = f"{total} / {self.db.get_setting_int('weekly_goal', 600)} min this week"

    def claim_weekly(self):
        total = self.db.weekly_minutes()
        goal = self.db.get_setting_int('weekly_goal', 600)
        if total >= goal:
            if self.db.is_weekly_claimed():
                notify_info("Weekly", "Already claimed this week.")
                return
            reward = 300
            self.db.add_rewards(0, reward)
            self.db.set_weekly_claimed()
            self.update_stats()
            self.refresh_weekly()
            notify_info("Weekly reward claimed!", f"+{reward}💎")
        else:
            notify_info("Too early!", "Not enough study time yet.")

    def reward_for_study(self, minutes: int):
        minutes = max(0, int(minutes))
        base_exp = minutes
        base_crystals = minutes // 5
        boosts = self.db.get_equipped_boosts() if hasattr(self.db, "get_equipped_boosts") else {'exp_pct': 0, 'crystal_pct': 0}
        exp = int(round(base_exp * (1 + boosts.get('exp_pct', 0) / 100.0)))
        crystals = int(round(base_crystals * (1 + boosts.get('crystal_pct', 0) / 100.0)))
        self.db.add_rewards(exp, crystals)
        self.update_stats()
        return exp, crystals

    def _format_time(self, secs: int) -> str:
        secs = max(0, int(secs))
        m, s = divmod(secs, 60)
        return f"{m:02d}:{s:02d}"

    def prepare_study_screen(self):
        self.focus_mode_enabled = bool(int(self.db.get_setting('focus_mode') or 0)) if hasattr(self.db, 'get_setting') else False
        self.background_count = bool(int(self.db.get_setting('background_count') or 0)) if hasattr(self.db, 'get_setting') else False
        try:
            blocked = self.db.get_setting('blocked_packages') if hasattr(self.db, 'get_setting') else '[]'
            allowed = self.db.get_setting('allowed_packages') if hasattr(self.db, 'get_setting') else '[]'
            self.blocked_packages = json.loads(blocked) if blocked else []
            self.allowed_packages = json.loads(allowed) if allowed else []
        except Exception:
            self.blocked_packages = []
            self.allowed_packages = []

        if self._pomo_total <= 0 or self._pomo_remaining <= 0:
            mins = self.db.get_setting_int('study_minutes', 25)
            self._pomo_total = mins * 60
            self._pomo_remaining = self._pomo_total
        self.study_time_text = self._format_time(self._pomo_remaining)

    def toggle_pomo(self):
        if self.pomo_running:
            self.pomo_pause()
        else:
            self.pomo_start()

    def pomo_start(self):
        if self._pomo_ev is None:
            self._pomo_ev = Clock.schedule_interval(self._pomo_tick, 1.0)
        self.pomo_running = True
        self._pomo_last_ts = time.time()
        try:
            Window.allow_screensaver = False
        except Exception:
            pass
        if self.focus_mode_enabled:
            try:
                from kivy.utils import platform
                if platform == 'android':
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    activity = PythonActivity.mActivity
                    activity.startLockTask()
            except Exception:
                pass

    def pomo_pause(self):
        if self._pomo_ev is not None:
            self._pomo_ev.cancel()
            self._pomo_ev = None
        self.pomo_running = False
        try:
            Window.allow_screensaver = True
        except Exception:
            pass
        if self.focus_mode_enabled:
            try:
                from kivy.utils import platform
                if platform == 'android':
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    activity = PythonActivity.mActivity
                    activity.stopLockTask()
            except Exception:
                pass

    def pomo_reset(self):
        if self._pomo_ev:
            self._pomo_ev.cancel()
            self._pomo_ev = None
        self.pomo_running = False
        mins = self.db.get_setting_int('study_minutes', 25)
        self._pomo_total = mins * 60
        self._pomo_remaining = self._pomo_total
        self.study_time_text = self._format_time(self._pomo_remaining)
        try:
            Window.allow_screensaver = True
        except Exception:
            pass

    def _pomo_tick(self, dt):
        self._pomo_remaining -= 1
        self.study_time_text = self._format_time(self._pomo_remaining)
        if self._pomo_remaining <= 0:
            self._pomo_ev.cancel()
            self._pomo_ev = None
            self.pomo_running = False
            studied = max(1, self._pomo_total // 60)
            exp, crystals = self.reward_for_study(studied)
            self.refresh_weekly()
            notify_info("Study Complete!", f"+{exp} EXP, +{crystals}💎")
            try:
                Window.allow_screensaver = True
            except Exception:
                pass

    def refresh_inventory(self):
        items = self.db.list_inventory()
        equipment = self.db.get_equipment()
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        grid = self.root.get_screen("inventory").ids.inv_grid
        grid.clear_widgets()
        if not items:
            lbl = Label(text="No items yet. Roll gacha to get items!", color=(0.9, 0.85, 0.7, 1))
            grid.add_widget(lbl)
        else:
            for it in items:
                row = BoxLayout(size_hint_y=None, height=60, spacing=8)
                row.canvas.before.clear()
                with row.canvas.before:
                    from kivy.graphics import Color, Rectangle
                    Color(0.25, 0.18, 0.12, 1)
                    Rectangle(pos=row.pos, size=row.size)
                row.bind(pos=lambda w, *_: self._update_inv_bg(w), size=lambda w, *_: self._update_inv_bg(w))
                
                rarity_color = {'S': (1, 0.85, 0.3), 'A': (0.8, 0.5, 1), 'B': (0.4, 0.8, 1), 'C': (0.7, 0.7, 0.7)}.get(it['rarity'], (1,1,1))
                
                slot_icon = {
                    'hair': '💇', 'shirt': '👕', 'pants': '👖', 'shoes': '👟', 
                    'glasses': '🕶️', 'mustache': '🥸', 'boost': '⚡'
                }.get(it['slot'] or it['type'], '📦')
                name_lbl = Label(text=f"{slot_icon} [{it['rarity']}] {it['name']}", color=rarity_color, size_hint_x=0.5)
                row.add_widget(name_lbl)
                
                boost_txt = ""
                if it['boost_exp_pct'] > 0:
                    boost_txt += f"+{it['boost_exp_pct']}% EXP "
                if it['boost_crystal_pct'] > 0:
                    boost_txt += f"+{it['boost_crystal_pct']}% 💎"
                info_lbl = Label(text=boost_txt if boost_txt else "", color=(0.9, 0.85, 0.7, 1), size_hint_x=0.3)
                row.add_widget(info_lbl)
                
                # Check if this item is equipped
                slot = it['slot']
                is_equipped = False
                if slot and equipment.get(slot) and equipment[slot].get('id') == it['id']:
                    is_equipped = True
                
                if slot or it['type'] == 'skin':
                    if is_equipped:
                        btn = Button(text="✓ Equipped", size_hint_x=0.2, background_normal='', background_color=(0.6, 0.5, 0.3, 1))
                        btn.bind(on_release=lambda _, s=slot: self.unequip_item_and_update(s))
                    else:
                        btn = Button(text="Equip", size_hint_x=0.2, background_normal='', background_color=(0.4, 0.6, 0.3, 1))
                        btn.bind(on_release=lambda _, item_id=it['id']: self.equip_item_and_update(item_id))
                    row.add_widget(btn)
                grid.add_widget(row)

    def _update_inv_bg(self, widget):
        widget.canvas.before.clear()
        with widget.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.25, 0.18, 0.12, 1)
            Rectangle(pos=widget.pos, size=widget.size)

    def equip_item_and_update(self, item_id):
        self.db.equip_item(item_id)
        notify_info("Equipped!", "Item equipped successfully!")
        self.update_character()
        self.refresh_inventory()
    
    def unequip_item_and_update(self, slot):
        self.db.unequip_item(slot)
        notify_info("Unequipped!", f"Removed {slot} item")
        self.update_character()
        self.refresh_inventory()
    
    def set_gender_ui(self, gender):
        self.db.set_gender(gender)
        notify_info("Gender Updated!", f"Character gender set to {gender}")
        self.update_character()
        self.update_stats()

    def roll_gacha(self, tier):
        success, item = self.gacha.roll(tier)
        if not success:
            self.gacha_result = "Not enough crystals!"
        else:
            rarity_color = {'S': '⭐', 'A': '🟣', 'B': '🔵', 'C': '⚪'}.get(item['rarity'], '⚪')
            self.gacha_result = f"{rarity_color} Got: {item['name']} [{item['rarity']}]!"
            self.refresh_inventory()
        self.update_stats()

    def populate_settings_from_ui(self):
        return

    def populate_settings_form(self):
        screen = self.root.get_screen("settings")
        screen.ids.in_study.text = str(self.db.get_setting_int('study_minutes', 25))
        screen.ids.in_break.text = str(self.db.get_setting_int('break_minutes', 5))
        screen.ids.in_daily.text = str(self.db.get_setting_int('daily_goal', 120))
        screen.ids.in_weekly.text = str(self.db.get_setting_int('weekly_goal', 600))
        screen.ids.sw_focus.active = bool(int(self.db.get_setting('focus_mode') or 0))
        screen.ids.sw_bg.active = bool(int(self.db.get_setting('background_count') or 0))
        screen.ids.in_blocked.text = self.db.get_setting('blocked_packages') or ''
        screen.ids.in_allowed.text = self.db.get_setting('allowed_packages') or ''

    def apply_settings_from_ui(self):
        screen = self.root.get_screen("settings")
        self.db.set_setting('study_minutes', screen.ids.in_study.text or '25')
        self.db.set_setting('break_minutes', screen.ids.in_break.text or '5')
        self.db.set_setting('daily_goal', screen.ids.in_daily.text or '120')
        self.db.set_setting('weekly_goal', screen.ids.in_weekly.text or '600')
        self.db.set_setting('focus_mode', '1' if screen.ids.sw_focus.active else '0')
        self.db.set_setting('background_count', '1' if screen.ids.sw_bg.active else '0')
        self.db.set_setting('blocked_packages', screen.ids.in_blocked.text or '')
        self.db.set_setting('allowed_packages', screen.ids.in_allowed.text or '')
        notify_info("Settings", "Settings saved successfully!")
        self.refresh_weekly()

if __name__ == '__main__':
    StudySagaApp().run()
