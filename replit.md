# Study Saga - RPG Study Tracker

## Overview
Study Saga is a gamified study tracker built with Python and Kivy. It combines productivity with RPG elements to make studying more engaging and rewarding.

**Current State**: Successfully imported and configured for Replit environment. The application is running with a VNC interface for the GUI.

**Last Updated**: October 13, 2025

## Project Architecture

### Technology Stack
- **Language**: Python 3.11
- **GUI Framework**: Kivy 2.3.1
- **Notifications**: Plyer 2.1.0
- **Database**: SQLite (studysaga.db)
- **Display**: VNC (for GUI rendering in Replit)

### Project Structure
```
.
├── main.py                      # Main application entry point
├── studysaga/
│   ├── __init__.py
│   ├── db.py                    # Database layer with SQLite
│   └── services/
│       ├── gacha.py            # Gacha system for rewards
│       ├── notifications.py     # Desktop notifications
│       └── pomodoro.py         # Pomodoro timer controller
├── assets/
│   └── skins/                  # Character skin assets
├── studysaga.db                # SQLite database (created on first run)
├── requirements.txt            # Python dependencies
└── buildozer.spec             # Android build configuration
```

### Core Features
1. **Pomodoro Timer** - Customizable study/break sessions (default 25/5 minutes)
2. **Reward System** - Earn crystals & EXP for completed study sessions
3. **Gacha System** - Bronze/Silver/Gold rolls for skins & item boosts
4. **Inventory** - Equippable skins and items that boost rewards
5. **Progress Tracking** - Daily quests and weekly boss goals
6. **Database Persistence** - All progress saved in SQLite

### Database Schema
- `player` - Player stats (level, EXP, crystals, equipped items)
- `settings` - User preferences and timer configurations
- `items` - Available items with rarities and boost stats
- `inventory` - Player's owned items
- `sessions` - Study session history
- `weekly_state` - Weekly progress and rewards tracking

## Setup Notes

### Replit Configuration
- **Workflow**: VNC display for Kivy GUI application
- **Python Version**: 3.11
- **System Dependencies**: SDL2, OpenGL libraries for graphics rendering
- **Display Protocol**: VNC output for desktop application

### Environment Setup
The project was configured for Replit with:
1. Python 3.11 installation with pip
2. System packages for Kivy (SDL2, OpenGL, X11 libraries)
3. VNC workflow for GUI display
4. Missing `get_setting()` method added to DB class

### Recent Changes
- **2025-10-13**: Pixel-art redesign (Terraria-style)
  - Complete UI transformation with retro pixel-art aesthetic
  - Custom pixel-perfect character sprites (16px grid-based)
  - Dark purple/brown color palette with warm golden accents
  - PixelButton and PixelLabel custom widgets with layered borders
  - All icons redesigned: hero, trees, crystals, scrolls, tomes, capes, pouches
  - Fixed character sprite orientation and proportions
  
- **2025-10-13**: Initial import and Replit setup
  - Installed Python 3.11 and Kivy dependencies
  - Added system libraries for GUI rendering
  - Fixed missing `DB.get_setting()` method
  - Configured VNC workflow for desktop display
  - Created .gitignore for Python project

## Running the Application

The application runs automatically via the configured workflow. To manually start:
```bash
python main.py
```

The GUI will be displayed in the VNC viewer accessible through the Replit interface.

## Development Notes

### Key Components
- **GameIcon**: Custom vector icon widget for in-game graphics
- **PomodoroController**: Timer logic and session management
- **GachaMachine**: Random item distribution with weighted rarities
- **DB**: Complete database abstraction layer

### Window Configuration
- Default window size: 420x860 (mobile-style portrait)
- Multitouch disabled for mouse input
- Can be adjusted for desktop use

### Android Build
The project includes Buildozer configuration for Android deployment:
- Target API: 35
- Min API: 24
- Permissions: VIBRATE, WAKE_LOCK, POST_NOTIFICATIONS
- Architectures: arm64-v8a, armeabi-v7a

## User Preferences
None recorded yet.

## Future Enhancements
- Additional character skins
- More boost items and rarity tiers
- Sound effects and animations
- Cloud save/sync capabilities
- Social features (leaderboards, friend challenges)
