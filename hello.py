from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
Window.clearcolor=(0.15,0.16,0.18,1)
class Hello(App):
    def build(self):
        return Label(text="Kivy Hello ✓", font_size="42sp")
if __name__=='__main__':
    Hello().run()
