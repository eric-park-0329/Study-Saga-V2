# Study Saga - RPG Study Tracker

## Overview
Study Saga is a gamified study tracker built with Python and Kivy. It combines productivity with RPG elements to make studying more engaging and rewarding.

**Current State**: Fully functional with all core features implemented including study sessions, gacha system, inventory, settings, and achievements.

**Last Updated**: October 18, 2025

## Project Architecture

### Technology Stack
- **Language**: Python 3.11
- **GUI Framework**: Kivy 2.3.1
- **Database**: SQLite 3 (studysaga.sqlite3)
- **Display**: VNC (for GUI rendering in Replit)
- **Authentication**: Custom auth system with session tokens

### Project Structure
```
.
├── main.py                      # Main application with all screen logic
├── db.py                        # Database layer with SQLite
├── auth.py                      # Authentication system
├── auth.kv                      # Login/Register screen UI
├── home.kv                      # Home screen UI
├── study.kv                     # Study session screen UI
├── gacha.kv                     # Gacha roll screen UI
├── inventory.kv                 # Inventory screen UI
├── settings.kv                  # Settings screen UI
├── achievements.kv              # Achievements screen UI
├── studysaga.sqlite3            # SQLite database
└── attached_assets/
    ├── background_male.gif      # Animated background (male)
    ├── background_female.gif    # Animated background (female)
    └── assets/
        ├── base_male.png        # Male character sprite
        ├── base_female.png      # Female character sprite
        ├── cape_red.png         # Red cape cosmetic
        ├── hairstyle_short.png  # Short hair cosmetic
        └── hat_basic.png        # Basic hat cosmetic
```

### Core Features
1. **User Authentication** - Email-based login/register with gender selection
2. **Character Display** - Gender-based character sprites on home screen (male/female)
3. **Study Sessions** - Timer-based study tracking with crystal rewards (1 crystal/min)
4. **Gacha System** - Bronze (10), Silver (30), Gold (60) crystal rolls for items
5. **Inventory** - Item collection with search and filter by rarity
6. **Achievements** - 5 achievements with automatic progress tracking
7. **Settings** - Nickname, gender, dark mode, daily goal customization
8. **Weekly Stats** - Visual progress bars for the past 7 days

### Database Schema
- **users** - User accounts (email, password_hash, nickname, gender, crystals, dark_mode, daily_goal_minutes)
- **sessions** - Auth session tokens with expiration
- **study_sessions** - Study session history (duration, crystals_earned, timestamps)
- **items** - Item pool (name, type, rarity, boost_exp_pct, boost_crystal_pct, description)
- **inventory** - User-owned items (user_id, item_id, acquired_at, equipped)
- **achievements** - User achievements (name, description, progress, goal, completed, completed_at)

### Achievements System
1. **First Study** - Complete your first study session (0/1)
2. **Study Warrior** - Study for 10 hours total (0/600 minutes)
3. **Crystal Collector** - Earn 1000 crystals (0/1000)
4. **Gacha Master** - Perform 50 gacha rolls (0/50)
5. **Weekly Hero** - Complete 5 study sessions in a week (0/5)

## Setup Notes

### Replit Configuration
- **Workflow**: VNC display for Kivy GUI application
- **Python Version**: 3.11
- **System Dependencies**: SDL2, OpenGL libraries for graphics rendering
- **Display Protocol**: VNC output for desktop application
- **Database**: SQLite with automatic initialization

### Environment Setup
The project is configured for Replit with:
1. Python 3.11 with Kivy 2.3.1
2. System packages for Kivy (SDL2, OpenGL, X11 libraries)
3. VNC workflow for GUI display (configured to use `vnc` output type)
4. Automatic database initialization on first run

### Recent Changes
- **2025-10-18**: Animated background system
  - Added gender-based animated GIF backgrounds to home screen
  - Male background: Cozy study room with male character (3.87 MB)
  - Female background: Cozy study room with female character (4.01 MB)
  - Backgrounds auto-switch when gender changes in Settings
  - Animated rain through window and fireplace flames

- **2025-10-18**: Complete feature implementation
  - Implemented all core features (study, gacha, inventory, achievements, settings)
  - Expanded database with 5 new tables
  - Added comprehensive achievement tracking system
  - Implemented automatic progress updates
  - Added gender selection UI to auth screen
  - Added Back buttons to all sub-screens
  - Full CRUD operations for all features
  - Tested and verified all functionality

- **2025-10-13**: Pixel-art redesign (Terraria-style)
  - Complete UI transformation with retro pixel-art aesthetic
  - Custom pixel-perfect character sprites (16px grid-based)
  - Dark purple/brown color palette with warm golden accents
  - All icons redesigned: hero, trees, crystals, scrolls, tomes, capes, pouches
  
- **2025-10-13**: Initial import and Replit setup
  - Installed Python 3.11 and Kivy dependencies
  - Added system libraries for GUI rendering
  - Configured VNC workflow for desktop display

## Running the Application

The application runs automatically via the configured workflow. To manually start:
```bash
python main.py
```

The GUI will be displayed in the VNC viewer accessible through the Replit interface.

## Testing

### Test Accounts
You can create a new account using the Register button with any email and password. Gender selection is available during registration.

### Feature Testing
1. **Study Session**: Use the slider to set duration, click Start, wait for timer completion
2. **Gacha Rolls**: Click Bronze/Silver/Gold buttons (requires crystals)
3. **Inventory**: View collected items with filter by rarity
4. **Achievements**: Check progress after completing actions
5. **Settings**: Update nickname, gender, dark mode, daily goal

## Development Notes

### Key Components
- **StudySagaApp**: Main app class with all screen management
- **Theme**: Centralized color scheme for consistent UI
- **DB Module**: Complete database abstraction with helpers
- **Auth Module**: Session-based authentication

### Navigation Flow
```
Auth Screen (login/register)
    ↓
Home Screen
    ├─→ Study Screen (with timer & weekly stats)
    ├─→ Gacha Screen (roll for items)
    ├─→ Inventory Screen (view collected items)
    ├─→ Settings Screen (customize preferences)
    └─→ Achievements Screen (track progress)
```

### Window Configuration
- Default window size: 800x600 (desktop)
- VNC display via Replit workflow
- Dark theme with accent colors

## User Preferences
None recorded yet.

## Future Enhancements
- Sound effects and animations
- Item equip system with stat boosts
- Real-time achievement notifications
- Cloud save/sync capabilities
- Social features (leaderboards, friend challenges)
- More achievement types
- Daily quest system
