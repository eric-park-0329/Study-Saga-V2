# Study Saga (Python/Kivy)

A study-tracker RPG built in **Python** using **Kivy**. Rewards are based on study time:
- Pomodoro timer (default 25/5) with break/return alerts
- Crystals & EXP for completed study sessions
- Gacha (Bronze/Silver/Gold) → Skins & Item boosts
- Inventory with equippable skins/items that boost rewards
- Dungeon (auto farming while studying, crystals increase over time)
- Daily Quest & Weekly Boss Goal progress and clear

## Quick Start (Desktop)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Build for Android (via Buildozer)
1. Install buildozer and Android SDK/NDK per docs.
2. Edit `buildozer.spec` if needed (icons, version).
3. Run:
```bash
buildozer android debug
# or
buildozer android release
```
The APK will be in `bin/`.

### Android permissions
We request POST_NOTIFICATIONS and WAKE_LOCK. Background timer is handled by persistence + resume catch-up; full foreground-service implementation is stubbed (see `studysaga/services/notifications.py`).

## Notes
- Database: SQLite (`studysaga.db` created on first run)
- Default goals: daily 120 min, weekly 600 min. Change in Settings.
- Gacha costs: Bronze 10, Silver 30, Gold 60 (crystals).
- This is a starter app; polish/animations are minimal and can be extended.
