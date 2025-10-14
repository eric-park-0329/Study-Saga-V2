Study Saga — Applied Patch (2025-10-14 18:27:05)
Changes:
1) Assets consolidated to ./assets; removed attached_assets/ fallback and duplicate paths.
2) sprite_renderer_ref.py rewritten to use absolute paths and only male/female bases.
3) main.py cleaned: absolute paths, ScreenManager + AnimatedBackground added, black text defaults.
4) auth.py now hashes passwords with bcrypt (fallback to 'plain:' if bcrypt unavailable) and issues long random tokens.
5) db.py: added bootstrap() and cleanup_expired_sessions() for schema/init and 30-day session expiry cleanup.
6) requirements/buildozer.spec synced: kivy, plyer, Pillow==10.4.0, bcrypt==4.2.0.
7) .gitignore strengthened; removed large UI ZIP packs from repo.
8) Minor KV defaults: Label/TextInput foreground set to black to read well on dark backgrounds.

How to run:
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  python main.py

Android build:
  edit buildozer.spec as needed; run buildozer android debug
