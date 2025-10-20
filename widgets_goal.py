
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, Rectangle, Line

class GoalGauge(Widget):
    goal_minutes = NumericProperty(60.0)
    progress_minutes = NumericProperty(0.0)
    tick_interval = NumericProperty(10.0)
    reached_color = ListProperty([0.20, 0.86, 0.55, 0.95])
    base_color = ListProperty([0.85, 0.90, 1.00, 0.95])
    track_color = ListProperty([1.0, 1.0, 1.0, 0.35])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw,
                  goal_minutes=self._redraw, progress_minutes=self._redraw,
                  tick_interval=self._redraw)

    def _redraw(self, *a):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, max(2.0, self.height)
        if w <= 2 or h <= 2:
            return
        g = max(1.0, float(self.goal_minutes))
        p = max(0.0, float(self.progress_minutes))
        tick = max(1.0, float(self.tick_interval))
        mx = max(g, p)
        ticks_count = int((mx + tick - 1e-6) // tick) + 1
        max_minutes = max(tick, ticks_count * tick)
        track_h = max(2.0, h * 0.14)
        with self.canvas:
            # Track
            Color(*self.track_color); Rectangle(pos=(x, y + (h-track_h)/2.0), size=(w, track_h))
            # Fill
            frac = min(1.0, (p / max_minutes)) if max_minutes > 0 else 0.0
            Color(* (self.reached_color if p >= g else self.base_color) )
            Rectangle(pos=(x, y + (h-track_h)/2.0), size=(w*frac, track_h))
            # Goal marker
            Color(1,1,1,0.85)
            gx = x + (w * (g / max_minutes))
            Line(points=[gx, y, gx, y+h], width=1.0)
            # Ticks
            Color(1,1,1,0.65)
            for i in range(ticks_count + 1):
                tx = x + (w * ((i * tick) / max_minutes))
                tall = ((i * tick) % (tick * 3) == 0)
                th = h * (0.35 if tall else 0.24)
                Line(points=[tx, y + (h-th)/2.0, tx, y + (h+th)/2.0], width=1.0)
