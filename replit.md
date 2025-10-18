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
2. **Animated Home Screen** - Gender-based animated backgrounds (cozy study room scenes)
3. **Study Sessions** - Timer-based study tracking with crystal rewards (1 crystal/min)
4. **Gacha System** - Probability-based item rolls with 3 tiers:
   - Bronze (10💎): 90% bronze, 9% silver, 1% gold
   - Silver (30💎): 70% bronze, 25% silver, 5% gold
   - Gold (60💎): 50% bronze, 40% silver, 10% gold
5. **Inventory** - Item collection with search and filter by rarity
6. **Achievements** - 20 achievements with automatic progress tracking
7. **Settings** - Nickname, gender, dark mode, daily goal customization
8. **Weekly Stats** - Visual progress bars for the past 7 days

### Database Schema
- **users** - User accounts (email, password_hash, nickname, gender, crystals, dark_mode, daily_goal_minutes)
- **sessions** - Auth session tokens with expiration
- **study_sessions** - Study session history (duration, crystals_earned, timestamps)
- **items** - Item pool (name, type, rarity, boost_exp_pct, boost_crystal_pct, description)
- **inventory** - User-owned items (user_id, item_id, acquired_at, equipped)
- **achievements** - User achievements (name, description, progress, goal, completed, completed_at)

### Achievements System (21 Total)

**Beginner (3):**
- First Study - Complete your first study session
- Getting Started - Study for 30 minutes total
- First Roll - Perform your first gacha roll

**Study (4):**
- Study Novice - Study for 2 hours total
- Study Warrior - Study for 10 hours total
- Study Master - Study for 50 hours total
- Study Legend - Study for 100 hours total

**Crystal (4):**
- Pocket Change - Earn 100 crystals
- Crystal Collector - Earn 1000 crystals
- Crystal Hoarder - Earn 5000 crystals
- Crystal Tycoon - Earn 10000 crystals

**Gacha (3):**
- Gacha Beginner - Perform 10 gacha rolls
- Gacha Master - Perform 50 gacha rolls
- Gacha Addict - Perform 100 gacha rolls

**Weekly (2):**
- Weekly Hero - Complete 5 study sessions in a week
- Weekly Champion - Complete 10 study sessions in a week

**Collection (2):**
- Collector - Own 5 different items
- Hoarder - Own 15 items total

**Special (2):**
- Lucky Strike - Get a gold rarity item from gacha
- Marathon Runner - Complete a 60 minute study session

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
- **2025-10-18**: 대규모 기능 업데이트
  - EXP & 레벨 시스템 추가 (1분 = 1 EXP, 레벨업 시스템)
  - 아이템 활성화 시스템 (Bronze 10분, Silver 30분, Gold 60분)
  - Gacha chest 애니메이션 (rarity별 chest 이미지 표시)
  - Achievements 40개로 확장 (7개 카테고리)
  - Study 화면 UI 개선 (활성 아이템 표시)
  - Inventory 아이템 사용 기능 추가
  - 홈 화면에 레벨 및 EXP 진행도 표시

- **2025-10-18**: 홈 화면 레이아웃 개선
  - 버튼들을 양쪽 사이드로 배치 (왼쪽 3개, 오른쪽 2개)
  - 중앙의 책상 배경이 잘 보이도록 레이아웃 조정
  - 왼쪽: Study, Gacha, Achievements
  - 오른쪽: Inventory, Settings

- **2025-10-18**: UI 텍스트 최적화 및 Alignment 개선
  - Emoji 제거하고 일반 텍스트로 변경 (alignment 문제 해결)
  - 모든 텍스트가 깔끔하게 중앙 정렬
  - VNC 환경에서 완벽하게 렌더링
  - 브래킷 표기법으로 상태 표시 ([OK], [BRONZE], [SILVER], [GOLD])

- **2025-10-18**: Gacha 시스템 확률 기반 개편
  - Cosmetic 아이템 완전 제거 (cape, hair, hat)
  - 남은 아이템: 6개 (Bronze 2, Silver 2, Gold 2)
  - 확률 기반 가챠 구현:
    * Bronze (10💎): 90% bronze, 9% silver, 1% gold
    * Silver (30💎): 70% bronze, 25% silver, 5% gold
    * Gold (60💎): 50% bronze, 40% silver, 10% gold
  - Fashion Icon 업적 제거 (총 20개 업적)

- **2025-10-18**: 업적 시스템 확장 (5개 → 21개 → 20개)
  - 7개 카테고리: Beginner, Study, Crystal, Gacha, Weekly, Collection, Special
  - 자동 진행도 추적 시스템
  - Admin 계정 2000 크리스탈 설정

- **2025-10-18**: 배경 화면 재배치
  - 홈 화면: background_home.gif (4.0 MB) - 고정 배경, 모든 사용자 동일
  - Study 화면: background_male.gif / background_female.gif - 성별별 배경
  - Settings에서 성별 변경 시 Study 화면 배경 자동 변경

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
