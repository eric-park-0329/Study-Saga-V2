
import os, time, random
os.environ["KIVY_NO_ARGS"]="1"
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar

import db as DB
import auth as AUTH

Window.clearcolor = (0.12,0.13,0.16,1)

# Load KV files
Builder.load_file('auth.kv')
Builder.load_file('home.kv')
Builder.load_file('study.kv')
Builder.load_file('inventory.kv')
Builder.load_file('gacha.kv')
Builder.load_file('settings.kv')
Builder.load_file('achievements.kv')

class AuthScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

# Define other screens (will be styled by KV files)
class StudyScreen(Screen):
    pass

class InventoryScreen(Screen):
    pass

class GachaScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class AchievementsScreen(Screen):
    pass

# Theme object for KV files
class Theme:
    bg = (0.12, 0.13, 0.16, 1)
    card = (0.18, 0.19, 0.22, 1)
    text = (0.95, 0.95, 0.97, 1)
    muted = (0.65, 0.65, 0.67, 1)
    accent = (0.2, 0.6, 0.86, 1)
    accent_text = (1, 1, 1, 1)
    bronze = (0.8, 0.5, 0.2, 1)
    silver = (0.75, 0.75, 0.78, 1)
    gold = (1.0, 0.84, 0.0, 1)

class StudySagaApp(App):
    user=None
    profile={"nickname":"","gender":"female"}
    token=""
    crystals=100
    theme = Theme()
    
    # Study session state
    study_timer = None
    study_start_time = 0
    study_duration = 0
    study_elapsed = 0
    
    def build(self):
        DB.bootstrap()
        DB.init_items()
        
        self.sm = ScreenManager(transition=NoTransition())
        
        # Add all screens
        self.auth = AuthScreen(name="auth")
        self.home = HomeScreen(name="home")
        self.study_screen = StudyScreen(name="study")
        self.inventory_screen = InventoryScreen(name="inventory")
        self.gacha_screen = GachaScreen(name="gacha")
        self.settings_screen = SettingsScreen(name="settings")
        self.achievements_screen = AchievementsScreen(name="achievements")
        
        self.sm.add_widget(self.auth)
        self.sm.add_widget(self.home)
        self.sm.add_widget(self.study_screen)
        self.sm.add_widget(self.inventory_screen)
        self.sm.add_widget(self.gacha_screen)
        self.sm.add_widget(self.settings_screen)
        self.sm.add_widget(self.achievements_screen)
        
        self.sm.current = "auth"
        return self.sm

    def go(self, name): 
        if name in [s.name for s in self.sm.screens]:
            # Load data when entering certain screens
            if name == "home":
                self.refresh_home()
            elif name == "inventory":
                self.refresh_inventory()
            elif name == "gacha":
                self.refresh_gacha()
            elif name == "settings":
                self.load_settings()
            elif name == "achievements":
                self.refresh_achievements()
            elif name == "study":
                self.refresh_study()
            
            self.sm.current = name
        else:
            print(f"Screen '{name}' not found!")

    def set_msg(self, txt): 
        try:
            self.auth.ids.msg.text = txt
        except:
            pass

    def do_register(self, email, pw, gender='female'):
        ok, msg = AUTH.register(email.strip(), pw.strip(), (gender or 'female').strip())
        self.set_msg(msg)
        if ok:
            self.set_msg("Registration successful! Please login.")

    def do_login(self, email, pw):
        ok, msg, user = AUTH.login(email.strip(), pw.strip())
        self.set_msg(msg)
        if not ok: 
            return
        
        # Save profile and switch to Home
        self.user = user
        self.token = user["token"]
        self.crystals = user.get("crystals", 100)
        self.profile = {
            "id": user["id"],
            "email": user["email"],
            "nickname": user.get("nickname",""),
            "gender": user.get("gender","female")
        }
        
        # Initialize achievements if first login
        DB.init_achievements(user["id"])
        
        self.go("home")

    def refresh_home(self):
        """Refresh home screen data"""
        if not self.user:
            return
        
        # Update user data
        user = DB.get_user(self.profile["id"])
        if user:
            self.crystals = user["crystals"]
            self.profile["nickname"] = user.get("nickname", "")
            self.profile["gender"] = user.get("gender", "female")
            self.profile["exp"] = user.get("exp", 0)
            self.profile["level"] = user.get("level", 1)
        
        # Update today's goal progress
        sessions = DB.get_study_sessions(self.profile["id"], days=1)
        today_minutes = sum(s["duration_minutes"] for s in sessions)
        goal_minutes = user.get("daily_goal_minutes", 60)
        
        # Calculate EXP for next level
        exp_needed = 100 * self.profile["level"]
        
        try:
            self.home.ids.hello.text = f"Hi, {self.profile['nickname'] or 'User'}! | Lv.{self.profile['level']} | Crystals: {self.crystals}"
            self.home.ids.today_goal.text = f"Today: {today_minutes}/{goal_minutes} min | EXP: {self.profile['exp']}/{exp_needed}"
        except Exception as e:
            print(f"Error updating home screen: {e}")
            pass

    def refresh_study(self):
        """Refresh study screen with weekly data"""
        if not self.user:
            return
        
        try:
            # Set background based on gender
            gender = self.profile.get("gender", "female")
            if gender == "male":
                self.study_screen.ids.background_gif.source = "attached_assets/background_male.gif"
            else:
                self.study_screen.ids.background_gif.source = "attached_assets/background_female.gif"
            
            # Show active items
            DB.clean_expired_items(self.profile["id"])
            active_items = DB.get_active_items(self.profile["id"])
            if active_items:
                items_text = ", ".join([f"{item['name']}" for item in active_items])
                self.study_screen.ids.active_items.text = f"Active Boosts: {items_text}"
                
                # Calculate total effects
                total_exp = sum(item.get('boost_exp_pct', 0) for item in active_items)
                total_crystal = sum(item.get('boost_crystal_pct', 0) for item in active_items)
                self.study_screen.ids.active_effects.text = f"Effect: EXP +{total_exp}%, Crystal +{total_crystal}%"
            else:
                self.study_screen.ids.active_items.text = ""
                self.study_screen.ids.active_effects.text = ""
            
            # Get weekly sessions
            sessions = DB.get_study_sessions(self.profile["id"], days=7)
            
            # Group by day of week
            from datetime import datetime, timedelta
            today = datetime.now()
            week_data = {}
            for i in range(7):
                day = (today - timedelta(days=6-i)).date()
                week_data[day] = 0
            
            for s in sessions:
                day = datetime.fromtimestamp(s["start_time"]).date()
                if day in week_data:
                    week_data[day] += s["duration_minutes"]
            
            # Create week progress bars
            weekbars = self.study_screen.ids.weekbars
            weekbars.clear_widgets()
            
            for day in sorted(week_data.keys()):
                minutes = week_data[day]
                max_min = 120  # max display
                progress = min(1.0, minutes / max_min)
                
                bar = ProgressBar(max=1.0, value=progress)
                weekbars.add_widget(bar)
                
        except Exception as e:
            print(f"Error refreshing study: {e}")

    # Study functions
    def study_start(self, minutes):
        """Start a study session"""
        if self.study_timer:
            self.study_stop()
        
        self.study_duration = minutes
        self.study_elapsed = 0
        self.study_start_time = time.time()
        
        # Update UI
        try:
            self.study_screen.ids.status.text = f"Studying for {minutes} min..."
            self.study_screen.ids.pbar.value = 0
            # Update slider to match the preset
            self.study_screen.ids.minutes.value = minutes
        except:
            pass
        
        # Start timer (update every second)
        self.study_timer = Clock.schedule_interval(self._study_tick, 1.0)
        print(f"Study session started: {minutes} minutes")
    
    def _study_tick(self, dt):
        """Update study progress"""
        if not self.study_timer:
            return False
        
        self.study_elapsed = int(time.time() - self.study_start_time)
        remaining = max(0, self.study_duration * 60 - self.study_elapsed)
        
        # Update progress bar
        progress = min(1.0, self.study_elapsed / (self.study_duration * 60))
        
        try:
            self.study_screen.ids.pbar.value = progress
            mins_left = remaining // 60
            secs_left = remaining % 60
            self.study_screen.ids.status.text = f"Time remaining: {mins_left:02d}:{secs_left:02d}"
        except:
            pass
        
        # Check if completed
        if remaining <= 0:
            self._study_complete()
            return False
        
        return True
    
    def _study_complete(self):
        """Complete study session and award rewards"""
        if self.study_timer:
            self.study_timer.cancel()
            self.study_timer = None
        
        uid = self.profile["id"]
        
        # Get active items and calculate bonuses
        DB.clean_expired_items(uid)
        active_items = DB.get_active_items(uid)
        
        crystal_bonus = 0
        exp_bonus = 0
        for item in active_items:
            crystal_bonus += item.get("boost_crystal_pct", 0)
            exp_bonus += item.get("boost_exp_pct", 0)
        
        # Calculate rewards (1 crystal per minute + bonuses)
        base_crystals = self.study_duration
        bonus_crystals = int(base_crystals * crystal_bonus / 100)
        crystals_earned = base_crystals + bonus_crystals
        
        # Calculate EXP (1 EXP per minute + bonuses)
        base_exp = self.study_duration
        bonus_exp = int(base_exp * exp_bonus / 100)
        exp_earned = base_exp + bonus_exp
        
        # Save session
        DB.add_study_session(uid, self.study_duration, crystals_earned)
        
        # Update crystals and EXP
        self.crystals = DB.update_crystals(uid, crystals_earned)
        new_level = DB.update_exp(uid, exp_earned)
        
        # Update achievements
        DB.update_achievement(uid, "First Study", 1)
        DB.update_achievement(uid, "Quick Start", 1)
        
        total_study_minutes = DB.get_total_study_minutes(uid)
        DB.set_achievement_progress(uid, "Getting Started", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Rookie", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Novice", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Apprentice", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Warrior", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Expert", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Master", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Grandmaster", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Legend", total_study_minutes)
        DB.set_achievement_progress(uid, "Study Mythic", total_study_minutes)
        DB.set_achievement_progress(uid, "Study God", total_study_minutes)
        
        # Marathon achievements
        if self.study_duration >= 60:
            DB.update_achievement(uid, "Marathon Runner", 1)
        if self.study_duration >= 90:
            DB.update_achievement(uid, "Ultra Marathon", 1)
        
        # Crystal achievements
        total_crystals = DB.get_total_crystals_earned(uid)
        DB.set_achievement_progress(uid, "Pocket Change", total_crystals)
        DB.set_achievement_progress(uid, "Crystal Collector", total_crystals)
        DB.set_achievement_progress(uid, "Crystal Hoarder", total_crystals)
        DB.set_achievement_progress(uid, "Crystal Tycoon", total_crystals)
        DB.set_achievement_progress(uid, "Crystal Magnate", total_crystals)
        DB.set_achievement_progress(uid, "Crystal Emperor", total_crystals)
        
        # Level achievements
        DB.set_achievement_progress(uid, "Level 5", new_level)
        DB.set_achievement_progress(uid, "Level 10", new_level)
        DB.set_achievement_progress(uid, "Level 25", new_level)
        DB.set_achievement_progress(uid, "Level 50", new_level)
        DB.set_achievement_progress(uid, "Level 100", new_level)
        
        # Update UI
        bonus_text = ""
        if crystal_bonus > 0 or exp_bonus > 0:
            bonus_text = f" (Bonus: +{crystal_bonus}% crystals, +{exp_bonus}% EXP)"
        
        try:
            self.study_screen.ids.status.text = f"[OK] Completed! +{crystals_earned} crystals, +{exp_earned} EXP{bonus_text}"
            self.study_screen.ids.pbar.value = 1.0
        except:
            pass
        
        # Refresh weekly bars
        self.refresh_study()
        
        print(f"Study session completed! Earned {crystals_earned} crystals, {exp_earned} EXP")
    
    def study_stop(self):
        """Stop current study session"""
        if self.study_timer:
            self.study_timer.cancel()
            self.study_timer = None
        
        try:
            self.study_screen.ids.status.text = "Session stopped"
            self.study_screen.ids.pbar.value = 0
        except:
            pass
        
        print("Study session stopped")
    
    def pomodoro_start(self, work_min, break_min, cycles):
        """Start pomodoro timer (simplified - just starts work session)"""
        print(f"Pomodoro: {work_min}min work, {break_min}min break, {cycles} cycles")
        self.study_start(work_min)

    # Gacha functions
    def refresh_gacha(self):
        """Refresh gacha screen"""
        try:
            self.gacha_screen.ids.result.text = ""
            self.gacha_screen.ids.pity.text = f"Crystals: {self.crystals}"
        except:
            pass
        
    def do_gacha(self, tier):
        """Perform gacha roll with probability-based rarity selection"""
        costs = {"bronze": 10, "silver": 30, "gold": 60}
        cost = costs.get(tier, 10)
        
        if self.crystals < cost:
            try:
                self.gacha_screen.ids.result.text = "[!] Not enough crystals!"
            except:
                pass
            return
        
        # Deduct crystals
        self.crystals = DB.update_crystals(self.profile["id"], -cost)
        
        # Update Gacha achievements
        uid = self.profile["id"]
        DB.update_achievement(uid, "First Roll", 1)
        DB.update_achievement(uid, "Gacha Beginner", 1)
        DB.update_achievement(uid, "Gacha Enthusiast", 1)
        DB.update_achievement(uid, "Gacha Master", 1)
        DB.update_achievement(uid, "Gacha Addict", 1)
        DB.update_achievement(uid, "Gacha Legend", 1)
        
        # Probability-based rarity selection
        probabilities = {
            "bronze": {"bronze": 90, "silver": 9, "gold": 1},
            "silver": {"bronze": 70, "silver": 25, "gold": 5},
            "gold": {"bronze": 50, "silver": 40, "gold": 10}
        }
        
        # Get probability distribution for this tier
        prob = probabilities.get(tier, probabilities["bronze"])
        
        # Random roll (0-100)
        roll = random.randint(1, 100)
        
        # Determine rarity based on probability
        if roll <= prob["bronze"]:
            selected_rarity = "bronze"
        elif roll <= prob["bronze"] + prob["silver"]:
            selected_rarity = "silver"
        else:
            selected_rarity = "gold"
        
        # Get items of selected rarity
        items = DB.get_items(selected_rarity)
        if not items:
            items = DB.get_items()
        
        if items:
            # Random item from selected rarity
            item = random.choice(items)
            
            # Add to inventory
            DB.add_to_inventory(uid, item["id"])
            
            # Update First Item achievement
            DB.update_achievement(uid, "First Item", 1)
            
            # Update collection achievements
            inventory = DB.get_inventory(uid)
            total_items = len(inventory)
            unique_items = len(set(i['item_id'] for i in inventory))
            
            DB.set_achievement_progress(uid, "Collector", unique_items)
            DB.set_achievement_progress(uid, "Hoarder", total_items)
            DB.set_achievement_progress(uid, "Item Master", total_items)
            DB.set_achievement_progress(uid, "Treasure Hunter", unique_items)
            
            # Lucky Strike achievement (gold rarity)
            if item["rarity"] == "gold":
                DB.update_achievement(uid, "Lucky Strike", 1)
            
            # Show chest image first
            chest_images = {
                "bronze": "attached_assets/chest_green.png",
                "silver": "attached_assets/chest_blue.png",
                "gold": "attached_assets/chest_gold.png"
            }
            chest_img = chest_images.get(item["rarity"], "attached_assets/chest_green.png")
            
            # Show chest, then result after delay
            try:
                from kivy.uix.image import Image
                card_stage = self.gacha_screen.ids.card_stage
                card_stage.clear_widgets()
                
                # Clear previous result text
                self.gacha_screen.ids.result.text = ""
                self.gacha_screen.ids.pity.text = "Opening chest..."
                
                # Show chest image
                chest = Image(
                    source=chest_img,
                    allow_stretch=True,
                    keep_ratio=True,
                    size_hint=(1, 1),
                    pos_hint={"center_x": 0.5, "center_y": 0.5}
                )
                card_stage.add_widget(chest)
                
                # Show result after 1 second
                def show_result(dt):
                    card_stage.clear_widgets()
                    rarity_prefix = {"bronze": "[BRONZE]", "silver": "[SILVER]", "gold": "[GOLD]"}
                    prefix = rarity_prefix.get(item["rarity"], "[ITEM]")
                    self.gacha_screen.ids.result.text = f"{prefix} {item['name']}\n{item['description']}"
                    self.gacha_screen.ids.pity.text = f"Crystals: {self.crystals}"
                
                Clock.schedule_once(show_result, 1.0)
            except Exception as e:
                print(f"Error showing chest: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"Gacha roll ({tier}): Got {item['name']}")
        else:
            try:
                self.gacha_screen.ids.result.text = "No items available"
            except:
                pass

    # Inventory functions
    def refresh_inventory(self, search="", tier="all"):
        """Refresh inventory list"""
        try:
            from kivy.uix.button import Button
            grid = self.inventory_screen.ids.grid
            grid.clear_widgets()
            
            # Get inventory and active items
            items = DB.get_inventory(self.profile["id"])
            active_items = DB.get_active_items(self.profile["id"])
            active_item_ids = [ai["item_id"] for ai in active_items]
            
            # Filter
            if search:
                items = [i for i in items if search.lower() in i["name"].lower()]
            if tier != "all":
                items = [i for i in items if i["rarity"] == tier]
            
            # Display
            if not items:
                label = Label(text="No items found", color=self.theme.muted)
                grid.add_widget(label)
            else:
                for item in items:
                    # Create item row
                    row = BoxLayout(size_hint_y=None, height=60, spacing=10)
                    
                    # Rarity indicator
                    rarity_colors = {
                        "bronze": self.theme.bronze,
                        "silver": self.theme.silver,
                        "gold": self.theme.gold
                    }
                    color = rarity_colors.get(item["rarity"], self.theme.text)
                    
                    # Check if item is active
                    is_active = item["item_id"] in active_item_ids
                    status = " [ACTIVE]" if is_active else ""
                    
                    # Item info
                    info = f"{item['name']}{status}\n+{item['boost_exp_pct']}% EXP, +{item['boost_crystal_pct']}% Crystals"
                    label = Label(text=info, color=color, halign="left", valign="middle", size_hint_x=0.7)
                    label.text_size = (label.width, None)
                    label.bind(size=lambda lb, *_: setattr(lb, 'text_size', (lb.width, None)))
                    
                    # Use button
                    durations = {"bronze": "10min", "silver": "30min", "gold": "60min"}
                    duration_text = durations.get(item["rarity"], "10min")
                    
                    use_btn = Button(
                        text=f"Use ({duration_text})" if not is_active else "Active",
                        size_hint_x=0.3,
                        disabled=is_active,
                        background_color=self.theme.accent if not is_active else self.theme.card,
                        color=self.theme.accent_text
                    )
                    use_btn.bind(on_release=lambda btn, inv_id=item["id"]: self.use_item(inv_id))
                    
                    row.add_widget(label)
                    row.add_widget(use_btn)
                    grid.add_widget(row)
        except Exception as e:
            print(f"Error refreshing inventory: {e}")
    
    def use_item(self, inventory_id):
        """Use/activate an item"""
        uid = self.profile["id"]
        success, msg = DB.activate_item(uid, inventory_id)
        
        print(f"Use item result: {msg}")
        
        # Update Power User achievement
        if success:
            DB.update_achievement(uid, "Power User", 1)
        
        # Refresh inventory to show updated status
        self.refresh_inventory()

    # Settings functions
    def load_settings(self):
        """Load current settings into UI"""
        if not self.user:
            return
        
        user = DB.get_user(self.profile["id"])
        if not user:
            return
        
        try:
            self.settings_screen.ids.nick.text = user.get("nickname", "")
            
            # Gender
            if user.get("gender") == "male":
                self.settings_screen.ids.male.state = "down"
                self.settings_screen.ids.female.state = "normal"
            else:
                self.settings_screen.ids.male.state = "normal"
                self.settings_screen.ids.female.state = "down"
            
            # Dark mode
            self.settings_screen.ids.dark.active = bool(user.get("dark_mode", 0))
            
            # Goal
            self.settings_screen.ids.goal.value = user.get("daily_goal_minutes", 60)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self, nickname, male_state, female_state, dark_mode, goal):
        """Save settings"""
        if not self.user:
            return
        
        gender = "male" if male_state == "down" else "female"
        dark_int = 1 if dark_mode else 0
        
        DB.update_user_settings(self.profile["id"], nickname, gender, dark_int, goal)
        
        # Update local profile
        self.profile["nickname"] = nickname
        self.profile["gender"] = gender
        
        print("Settings saved!")
        self.go("home")

    # Achievements functions
    def refresh_achievements(self):
        """Refresh achievements list"""
        if not self.user:
            return
        
        try:
            grid = self.achievements_screen.ids.grid
            grid.clear_widgets()
            
            achievements = DB.get_achievements(self.profile["id"])
            
            if not achievements:
                label = Label(text="No achievements yet", color=self.theme.muted)
                grid.add_widget(label)
            else:
                for ach in achievements:
                    row = BoxLayout(orientation="vertical", size_hint_y=None, height=80, spacing=4)
                    
                    # Title (no status symbol - color indicates completion)
                    title = Label(
                        text=f"{ach['name']}", 
                        color=self.theme.text if ach["completed"] else self.theme.muted,
                        halign="left",
                        valign="top",
                        font_size="16sp"
                    )
                    title.text_size = (title.width, None)
                    title.bind(size=lambda lb, *_: setattr(lb, 'text_size', (lb.width, None)))
                    
                    # Progress
                    progress_pct = min(100, int(100 * ach["progress"] / ach["goal"])) if ach["goal"] > 0 else 0
                    desc = Label(
                        text=f"{ach['description']} ({ach['progress']}/{ach['goal']} - {progress_pct}%)",
                        color=self.theme.muted,
                        halign="left",
                        valign="top",
                        font_size="12sp"
                    )
                    desc.text_size = (desc.width, None)
                    desc.bind(size=lambda lb, *_: setattr(lb, 'text_size', (lb.width, None)))
                    
                    row.add_widget(title)
                    row.add_widget(desc)
                    grid.add_widget(row)
        except Exception as e:
            print(f"Error refreshing achievements: {e}")

if __name__=="__main__":
    StudySagaApp().run()
