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

# 불필요/중복이었던 스키마 및 로컬 DB 클래스 정의 제거
# 실제 DB는 studysaga.db의 DB 클래스를 사용
from studysaga.db import DB

# 폰트 없이도 보이는 간단한 벡터 아이콘
class GameIcon(Widget):
    kind = StringProperty("hero")  # hero, tree, crystal, scroll, tome, cape, pouch
    color = ListProperty([0.9, 0.95, 1.0, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=lambda *_: self._redraw(),
                  size=lambda *_: self._redraw(),
                  kind=lambda *_: self._redraw(),
                  color=lambda *_: self._redraw())
        Clock.schedule_once(lambda dt: self._redraw(), 0)

    def _redraw(self):
        from kivy.graphics import Color, Line, Ellipse, Rectangle, RoundedRectangle
        self.canvas.clear()
        w, h = self.size
        x, y = self.pos
        with self.canvas:
            Color(*self.color)

            if self.kind == "hero":
                # 머리
                Ellipse(pos=(x + w*0.35, y + h*0.7), size=(w*0.3, w*0.3))
                # 몸통/팔/다리
                Line(points=[x + w*0.5, y + h*0.7, x + w*0.5, y + h*0.25], width=1.5)
                Line(points=[x + w*0.5, y + h*0.55, x + w*0.3, y + h*0.45], width=1.5)
                Line(points=[x + w*0.5, y + h*0.55, x + w*0.7, y + h*0.45], width=1.5)
                Line(points=[x + w*0.5, y + h*0.25, x + w*0.35, y + h*0.05], width=1.5)
                Line(points=[x + w*0.5, y + h*0.25, x + w*0.65, y + h*0.05], width=1.5)

            elif self.kind == "tree":
                # 줄기
                Color(0.55, 0.33, 0.15, 1)
                Rectangle(pos=(x + w*0.43, y), size=(w*0.14, h*0.35))
                # 수관
                Color(0.2, 0.65, 0.35, 1)
                Ellipse(pos=(x + w*0.1, y + h*0.25), size=(w*0.8, h*0.55))
                Ellipse(pos=(x + w*0.2, y + h*0.45), size=(w*0.6, h*0.45))

            elif self.kind == "crystal":
                # 다이아몬드(선)
                Color(0.3, 0.8, 1.0, 1)
                Line(points=[
                    x + w*0.5, y + h*0.95,
                    x + w*0.9, y + h*0.5,
                    x + w*0.5, y + h*0.05,
                    x + w*0.1, y + h*0.5,
                    x + w*0.5, y + h*0.95
                ], width=2)

            elif self.kind == "scroll":
                Color(0.95, 0.9, 0.7, 1)
                Rectangle(pos=(x + w*0.15, y + h*0.25), size=(w*0.7, h*0.5))
                Color(0.85, 0.8, 0.6, 1)
                Ellipse(pos=(x + w*0.05, y + h*0.2), size=(w*0.2, h*0.6))
                Ellipse(pos=(x + w*0.75, y + h*0.2), size=(w*0.2, h*0.6))

            elif self.kind == "tome":
                Color(0.6, 0.2, 0.2, 1)
                Rectangle(pos=(x + w*0.15, y + h*0.15), size=(w*0.7, h*0.7))
                Color(0.9, 0.85, 0.8, 1)
                Line(points=[x + w*0.5, y + h*0.15, x + w*0.5, y + h*0.85], width=2)

            elif self.kind == "cape":
                Color(0.95, 0.75, 0.2, 1)
                RoundedRectangle(pos=(x + w*0.2, y + h*0.1), size=(w*0.6, h*0.8), radius=[(0,0), (0,0), (w*0.2,w*0.2), (w*0.2,w*0.2)])

            elif self.kind == "pouch":
                Color(0.65, 0.45, 0.2, 1)
                Ellipse(pos=(x + w*0.15, y + h*0.1), size=(w*0.7, h*0.65))
                Color(0.5, 0.3, 0.12, 1)
                Line(circle=(x + w*0.5, y + h*0.7, w*0.28), width=2)

KV = r'''
#:import dp kivy.metrics.dp
#:import Factory kivy.factory.Factory
#:import NoTransition kivy.uix.screenmanager.NoTransition

<Header@BoxLayout>:
    size_hint_y: None
    height: dp(54)
    padding: dp(10), 0
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.14, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Button:
        text: "◀"
        size_hint_x: None
        width: dp(48)
        opacity: 1 if app.can_go_back else 0
        disabled: not app.can_go_back
        on_release: app.go_back()
    Label:
        text: "Study Saga"
        font_size: '20sp'
        color: 1, 1, 1, 1
    Widget:
    Label:
        text: app.stats_text
        color: .9, .9, .9, 1
        font_size: '14sp'

<HomeScreen@Screen>:
    name: "home"
    BoxLayout:
        orientation: 'vertical'
        Header:
        FloatLayout:
            size_hint_y: 0.5
            canvas.before:
                Color:
                    rgba: 0.08, 0.1, 0.16, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.12, 0.16, 0.22, 1
                Rectangle:
                    pos: self.x, self.y
                    size: self.width, self.height * 0.35
            GameIcon:
                kind: "hero"
                size_hint: None, None
                size: dp(72), dp(96)
                pos_hint: {'center_x': 0.5, 'center_y': 0.6}
            GameIcon:
                kind: "tree"
                size_hint: None, None
                size: dp(36), dp(48)
                pos_hint: {'center_x': 0.32, 'y': 0.05}
            GameIcon:
                kind: "tree"
                size_hint: None, None
                size: dp(32), dp(44)
                pos_hint: {'center_x': 0.68, 'y': 0.06}
        BoxLayout:
            padding: dp(16)
            spacing: dp(12)
            orientation: 'vertical'
            Label:
                text: "Welcome, Adventurer!"
                font_size: '22sp'
                size_hint_y: None
                height: dp(40)
            Label:
                text: "Study minutes fuel your dungeon runs. Earn crystals & EXP, then roll gacha!"
                color: .8, .8, .85, 1
                halign: 'center'
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1] + dp(8)
            GridLayout:
                cols: 2
                spacing: dp(10)
                size_hint_y: None
                height: dp(220)
                Button:
                    text: "▶ Study"
                    on_release: app.goto("study")
                Button:
                    text: "🎰 Gacha"
                    on_release: app.goto("gacha")
                Button:
                    text: "🎒 Inventory"
                    on_release: app.goto("inventory")
                Button:
                    text: "👑 Weekly Boss"
                    on_release: app.goto("boss")
            Button:
                size_hint_y: None
                height: dp(48)
                text: "⚙ Settings"
                on_release: app.goto("settings")

<InventoryScreen@Screen>:
    name: "inventory"
    BoxLayout:
        orientation: 'vertical'
        Header:
        ScrollView:
            GridLayout:
                id: inv_grid
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(16)
                spacing: dp(8)

<StudyScreen@Screen>:
    name: "study"
    on_pre_enter: app.prepare_study_screen()
    BoxLayout:
        orientation: 'vertical'
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(16)
            Label:
                text: "Study Timer"
                font_size: '24sp'
                size_hint_y: None
                height: dp(40)
            Label:
                text: app.study_time_text
                font_size: '48sp'
                size_hint_y: None
                height: dp(80)
                color: 1, 1, 1, 1
            BoxLayout:
                size_hint_y: None
                height: dp(56)
                spacing: dp(12)
                Button:
                    text: "⏯ Pause" if app.pomo_running else "▶ Start"
                    on_release: app.toggle_pomo()
                Button:
                    text: "⟲ Reset"
                    on_release: app.pomo_reset()
            Label:
                text: "Tip: Adjust durations in Settings."
                color: .8, .8, .85, 1
                size_hint_y: None
                height: dp(24)

<GachaScreen@Screen>:
    name: "gacha"
    BoxLayout:
        orientation: 'vertical'
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(12)
            Label:
                text: "Gacha Machine"
                font_size: '24sp'
                size_hint_y: None
                height: dp(40)
            Label:
                text: app.gacha_result
                size_hint_y: None
                height: dp(60)
            Button:
                text: "Bronze Roll (10💎)"
                size_hint_y: None
                height: dp(50)
                on_release: app.roll_gacha('bronze')
            Button:
                text: "Silver Roll (30💎)"
                size_hint_y: None
                height: dp(50)
                on_release: app.roll_gacha('silver')
            Button:
                text: "Gold Roll (60💎)"
                size_hint_y: None
                height: dp(50)
                on_release: app.roll_gacha('gold')
            Widget:

<BossScreen@Screen>:
    name: "boss"
    BoxLayout:
        orientation: 'vertical'
        Header:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(12)
            Label:
                text: "Weekly Boss"
                font_size: '24sp'
                size_hint_y: None
                height: dp(40)
            Label:
                text: app.weekly_text
                size_hint_y: None
                height: dp(60)
            Button:
                text: "Claim Reward"
                size_hint_y: None
                height: dp(50)
                on_release: app.claim_weekly()
            Widget:

<SettingsScreen@Screen>:
    name: "settings"
    on_pre_enter: app.populate_settings_form()
    BoxLayout:
        orientation: 'vertical'
        Header:
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Settings"
                    font_size: '24sp'
                    size_hint_y: None
                    height: dp(40)
                Label:
                    text: "Configure your study timer and goals"
                    size_hint_y: None
                    height: dp(30)
                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height
                    Label:
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
                    Label:
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
                    Label:
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
                    Label:
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
                    Label:
                        text: "Focus mode"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Switch:
                        id: sw_focus
                        size_hint_y: None
                        height: dp(40)
                    Label:
                        text: "Background counting"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Switch:
                        id: sw_bg
                        size_hint_y: None
                        height: dp(40)
                    Label:
                        text: "Blocked packages (comma-separated)"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_blocked
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                    Label:
                        text: "Allowed packages (comma-separated)"
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: in_allowed
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                Button:
                    text: "Save"
                    size_hint_y: None
                    height: dp(48)
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
    # 집중/백그라운드 옵션
    focus_mode_enabled = BooleanProperty(False)
    background_count = BooleanProperty(False)
    blocked_packages = ListProperty([])
    allowed_packages = ListProperty([])
    # 타이머 내부 상태
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
            # KV에 최상위 인스턴스가 없으면 Root를 직접 생성
            if ui is None:
                ui = Root()
        except Exception as e:
            import traceback
            traceback.print_exc()
            from kivy.uix.label import Label
            # 오류를 화면에 직접 표시하여 원인 파악
            return Label(text=f"KV load error: {e}")
        return ui

    def on_start(self):
        # 이제 self.root가 보장됨
        if not self.root or not hasattr(self.root, "get_screen"):
            # UI가 정상적으로 로드되지 않으면 초기화 스킵
            return
        self.refresh_inventory()
        # 안드로이드 하드웨어 뒤로가기 처리
        Window.bind(on_keyboard=self._on_keyboard)

    def on_pause(self):
        # 앱이 백그라운드로 갈 때 타임스탬프 저장
        if self.pomo_running:
            self._paused_at = time.time()
        return True

    def on_resume(self):
        # 앱이 포어그라운드로 돌아올 때 경과시간 반영(백그라운드 카운팅 옵션이 켜진 경우)
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
        # 27 = Android/데스크탑 ESC(Back)
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

    # 주간 통계/보상 로직 정리: DB의 weekly_minutes / set_weekly_claimed 사용
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
            reward = 300  # 주간 보상
            # give_crystals가 없으므로 add_rewards로 크리스탈만 지급
            self.db.add_rewards(0, reward)
            self.db.set_weekly_claimed()
            self.update_stats()
            self.refresh_weekly()
            notify_info("Weekly reward claimed!", f"+{reward}💎")
        else:
            notify_info("Too early!", "Not enough study time yet.")

    # 스터디 보상 계산(부스트 반영)
    def reward_for_study(self, minutes: int):
        minutes = max(0, int(minutes))
        # 기본 보상: EXP = 분수, 크리스탈 = 분당 1개/5분(내림)
        base_exp = minutes
        base_crystals = minutes // 5
        boosts = self.db.get_equipped_boosts() if hasattr(self.db, "get_equipped_boosts") else {'exp_pct': 0, 'crystal_pct': 0}
        exp = int(round(base_exp * (1 + boosts.get('exp_pct', 0) / 100.0)))
        crystals = int(round(base_crystals * (1 + boosts.get('crystal_pct', 0) / 100.0)))
        # DB에 적용
        self.db.add_rewards(exp, crystals)
        self.update_stats()
        return exp, crystals

    # ===== Pomodoro-like 간단 타이머 제어 =====
    def _format_time(self, secs: int) -> str:
        secs = max(0, int(secs))
        m, s = divmod(secs, 60)
        return f"{m:02d}:{s:02d}"

    def prepare_study_screen(self):
        # 설정 반영
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

        # 타이머 초기 남은 시간 설정 및 UI 동기화
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
        # 화면 꺼짐 방지
        try:
            Window.allow_screensaver = False
        except Exception:
            pass
        # 집중 모드: 가능한 경우 앱 화면 고정(사용자 동의 필요)
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
        # 화면 꺼짐 허용 복원
        try:
            Window.allow_screensaver = True
        except Exception:
            pass
        # 화면 고정 해제 시도
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
        self.pomo_pause()
        mins = self.db.get_setting_int('study_minutes', 25)
        self._pomo_total = mins * 60
        self._pomo_remaining = self._pomo_total
        self._pomo_last_ts = None
        self._paused_at = None
        self.study_time_text = self._format_time(self._pomo_remaining)

    def _pomo_tick(self, dt):
        self._pomo_remaining -= 1
        self._pomo_last_ts = time.time()
        if self._pomo_remaining <= 0:
            self.pomo_pause()
            studied = max(1, self._pomo_total // 60)
            exp, crystals = self.reward_for_study(studied)
            notify_info("Study complete", f"+{exp} EXP, +{crystals}💎")
            self._pomo_remaining = 0
        self.study_time_text = self._format_time(self._pomo_remaining)

    # ===== Settings 화면 채우기/적용 =====
    def populate_settings_form(self):
        try:
            scr = self.root.get_screen("settings")
        except Exception:
            return
        ids = scr.ids
        # 기본 시간/목표
        ids.in_study.text = str(self.db.get_setting_int('study_minutes', 25))
        ids.in_break.text = str(self.db.get_setting_int('break_minutes', 5))
        ids.in_daily.text = str(self.db.get_setting_int('daily_goal', 120))
        ids.in_weekly.text = str(self.db.get_setting_int('weekly_goal', 600))
        # 집중/백그라운드 옵션
        focus = bool(int(self.db.get_setting('focus_mode') or 0)) if hasattr(self.db, 'get_setting') else False
        bgcnt = bool(int(self.db.get_setting('background_count') or 0)) if hasattr(self.db, 'get_setting') else False
        if 'sw_focus' in ids:
            ids.sw_focus.active = focus
        if 'sw_bg' in ids:
            ids.sw_bg.active = bgcnt
        # 패키지 목록
        try:
            blocked = self.db.get_setting('blocked_packages') if hasattr(self.db, 'get_setting') else '[]'
            allowed = self.db.get_setting('allowed_packages') if hasattr(self.db, 'get_setting') else '[]'
            blocked_l = json.loads(blocked) if blocked else []
            allowed_l = json.loads(allowed) if allowed else []
        except Exception:
            blocked_l, allowed_l = [], []
        if 'in_blocked' in ids:
            ids.in_blocked.text = ",".join(blocked_l)
        if 'in_allowed' in ids:
            ids.in_allowed.text = ",".join(allowed_l)

    def apply_settings_from_ui(self):
        try:
            scr = self.root.get_screen("settings")
        except Exception:
            return
        ids = scr.ids
        # 기존 저장 루틴 호출
        self.save_settings(ids.in_study.text, ids.in_break.text, ids.in_daily.text, ids.in_weekly.text)
        # 추가 옵션 저장
        def _parse_csv(text):
            return [p.strip() for p in (text or "").split(",") if p.strip()]
        focus = 1 if getattr(ids.get('sw_focus'), 'active', False) else 0
        bgcnt = 1 if getattr(ids.get('sw_bg'), 'active', False) else 0
        blocked_l = _parse_csv(getattr(ids.get('in_blocked'), 'text', ''))
        allowed_l = _parse_csv(getattr(ids.get('in_allowed'), 'text', ''))
        if hasattr(self.db, 'set_setting'):
            self.db.set_setting('focus_mode', focus)
            self.db.set_setting('background_count', bgcnt)
            self.db.set_setting('blocked_packages', json.dumps(blocked_l))
            self.db.set_setting('allowed_packages', json.dumps(allowed_l))
        # 메모리 반영
        self.focus_mode_enabled = bool(focus)
        self.background_count = bool(bgcnt)
        self.blocked_packages = blocked_l
        self.allowed_packages = allowed_l
        notify_info("Settings saved", "Focus/Background options applied.")
        self.goto("home")

    def refresh_inventory(self):
        grid = self.root.get_screen("inventory").ids.inv_grid
        grid.clear_widgets()
        items = self.db.list_inventory()

        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button

        for item in items:
            row = BoxLayout(size_hint_y=None, height=40, spacing=8)
            row.add_widget(Label(text=f"{item['name']} ({item['rarity']}) [{item['type']}]", halign='left'))
            btn = Button(text="Equip" if item['type'] in ('skin','boost') else "Use")

            def _equip(instance, item=item):
                self.db.equip_item(item['id'])
                self.update_stats()
                notify_info("Equipped", f"{item['name']} equipped!")

            btn.bind(on_release=_equip)
            row.add_widget(btn)
            grid.add_widget(row)

    def roll_gacha(self, tier):
        ok, item = self.gacha.roll(tier)
        if not ok:
            self.gacha_result = "Not enough crystals!"
            notify_info("Gacha", "Not enough crystals.")
            return
        self.update_stats()
        self.refresh_inventory()
        self.gacha_result = f"You got: {item['name']} ({item['rarity']})"
        notify_info("Gacha", self.gacha_result)

    def save_settings(self, study_minutes, break_minutes, daily_goal, weekly_goal):
        try:
            self.db.set_setting('study_minutes', int(study_minutes))
            self.db.set_setting('break_minutes', int(break_minutes))
            self.db.set_setting('daily_goal', int(daily_goal))
            self.db.set_setting('weekly_goal', int(weekly_goal))
            # 길이 재적용
            if hasattr(self.pomo, "reload_lengths"):
                self.pomo.reload_lengths()
            else:
                self.pomo.reset()
            self.refresh_weekly()
            notify_info("Settings saved", "Your new settings have been applied.")
            self.goto("home")
        except ValueError:
            notify_info("Error", "Please enter valid numbers.")

if __name__ == "__main__":
    StudySagaApp().run()
