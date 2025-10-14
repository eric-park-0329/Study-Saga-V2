[app]
title = Study Saga
package.name = studysaga
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,db
version = 0.1.0
requirements = kivy==2.3.1, plyer==2.1.0, pillow==10.4.0, bcrypt==4.2.0
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.ndk = 25b
android.enable_androidx = True
android.permissions = VIBRATE,WAKE_LOCK,POST_NOTIFICATIONS
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
