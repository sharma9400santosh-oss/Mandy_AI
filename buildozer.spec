[app]
title = Mandy
package.name = mandy
package.domain = com.santosh.mandy

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json

version = 0.2

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pyjnius

orientation = landscape
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/mandy_face.png

android.permissions = RECORD_AUDIO,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CALL_PHONE,READ_CONTACTS,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,REQUEST_INSTALL_PACKAGES,CAMERA

android.api = 34
android.minapi = 21
android.ndk = 25b
# 32-bit only, single architecture -- switched from arm64-v8a for
# compatibility with an older 32-bit head unit. Still single-arch (not
# combined with arm64-v8a) since combining architectures in one build
# has repeatedly caused native wheel cross-compilation failures.
# minapi = 21 (Android 5.0) is the lowest this NDK version (r25b) can
# target at all -- Google removed NDK support for anything older.
android.archs = armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
