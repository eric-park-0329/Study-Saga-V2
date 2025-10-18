from kivy.clock import Clock
from studysaga.services.notifications import notify_info

class PomodoroController:
  def __init__(self, app, db):
    self.app = app
    self.db = db
    self.phase = 'idle' # 'study','break'
    self.length_study = db.get_setting_int('study_minutes', 25) * 60
    self.length_break = db.get_setting_int('break_minutes', 5) * 60
    self.left = self.length_study
    self._event = None
    self.phase_title = "Ready to Study"
    self.hint_text = "Press Start to begin a study session."
    self.time_left_str = self._fmt(self.left)

  def reload_lengths(self):
    self.length_study = self.db.get_setting_int('study_minutes', 25) * 60
    self.length_break = self.db.get_setting_int('break_minutes', 5) * 60
    if self.phase == 'study':
      self.left = min(self.left, self.length_study)
    elif self.phase == 'break':
      self.left = min(self.left, self.length_break)
    self.time_left_str = self._fmt(self.left)

  def start(self):
    if self.phase in ('idle','break'):
      self._begin_study()
    elif self.phase == 'study':
      return

  def pause(self):
    if self._event:
      self._event.cancel()
      self._event = None

  def reset(self):
    if self._event:
      self._event.cancel()
    self.phase = 'idle'
    self.left = self.length_study
    self.phase_title = "Ready to Study"
    self.hint_text = "Press Start to begin a study session."
    self.time_left_str = self._fmt(self.left)

  def _begin_study(self):
    self.phase = 'study'
    self.left = self.length_study
    self.phase_title = "Studying..."
    self.hint_text = "Stay focused!"
    self.app.db.start_session('study')
    self._tick()

  def _begin_break(self):
    self.phase = 'break'
    self.left = self.length_break
    self.phase_title = "Break time"
    self.hint_text = "Stretch, hydrate, rest eyes."
    self.app.db.start_session('break')
    notify_info("Break", "Study done! Take a short break.")
    self._tick()

  def _tick(self):
    self.time_left_str = self._fmt(self.left)
    if self.left <= 0:
      if self.phase == 'study':
        minutes = self.app.db.end_session('study')
        exp, cr = self.app.reward_for_study(minutes)
        self.app.refresh_weekly()
        notify_info("Study Complete", f"+{exp} EXP, +{cr}💎")
        self._begin_break()
      elif self.phase == 'break':
        self.app.db.end_session('break')
        notify_info("Break Over", "Back to study!")
        self._begin_study()
      return
    self.left -= 1
    self._event = Clock.schedule_once(lambda dt: self._tick(), 1.0)

  def _fmt(self, s):
    m = s // 60
    ss = s % 60
    return f"{int(m):02d}:{int(ss):02d}"
