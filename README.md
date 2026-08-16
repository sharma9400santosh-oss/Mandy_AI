# Mandy

A voice-controlled car AI assistant, built in Python with Kivy. Mandy has
a face, listens to you, talks back with emotion-adjusted tone, and can
navigate, call people, play music, and show live vehicle gauges.

## What's new in v0.2

- **Fault-code (DTC) reading** (`obd_dtc.py`): the dashboard previously
  polled RPM/fuel/temp only. This adds real OBD-II Mode 03 stored-code
  reading over the same Bluetooth connection.
- **Warning-light rail** (`warning_rail.py`, dashboard screen): four
  tappable icons (oil/tire/battery/brake). Tapping one runs a live
  diagnostic and explains it in plain language via Mandy's existing
  Claude backend. Also auto-checks for stored codes every 90s while
  connected. Honest caveat: generic OBD codes can't be reliably
  attributed to one specific icon (tire pressure and brake fluid aren't
  even standard OBD PIDs), so a detected fault lights all four together
  as "something needs attention" rather than pretending to pinpoint one.
- **On-screen chat log** (`chat_panel.py`, dashboard screen): a
  visible, typed alternative to voice-only interaction, wired to the
  same `ConversationEngine` HomeScreen already uses.
- **Advanced mode** (`screens/advanced_mode_screen.py`, linked from
  Settings): raw key/value editor over the existing settings store, for
  config that doesn't have a dedicated field yet.

See `CHANGELOG_v0.2.md` for the full list of files touched and why.

## Features

| Feature | Status | Notes |
|---|---|---|
| Mandy's face + animated glow | Working | Uses your uploaded avatar image, glow color/pulse reflects her state |
| Voice input | Working | Native Android speech recognition, no API key |
| Wake word ("Hi Mandy" / "Hey Mandy") | Working | Toggle in Home screen; always-listening, uses more battery than tap-to-speak |
| Voice recognition (voiceprint) | Working, approximate | Only acts on commands that sound like your enrolled voice -- see limitation below |
| Talk-back voice output | Working | Android TTS, pitch/rate shift based on detected emotion |
| Navigation | Working | Hands off to Google Maps for real turn-by-turn |
| Phone calls | Working | Calls by contact name (looked up from your phone) or number |
| Spotify / YouTube / Radio | Working | Opens the real apps / streams |
| Speedometer | Working | Real GPS speed, works in any car |
| RPM gauge | Needs hardware | Real data, but only with a Bluetooth OBD-II adapter |
| Speed limit tracker | Working, needs internet | Looks up posted limits via OpenStreetMap, flags when you're over |
| Toll plaza alerts | Working, example data | Geofenced alerts + price; bundled database is a placeholder, see below |
| File explorer | Working | Browse and open files on your phone |
| Vehicle documents tracker | Working, manual entry | Insurance/PUC/Registration/DL expiry tracking -- see limitation below |
| RajmargYatra / mParivahan / insurer app launchers | Working | Opens the real apps; can't read their data |
| Icon-based app dashboard | Working | Media/Calls/Navigate/Docs/Files/Connect/Settings/Dashboard, generated icons |
| Connectivity screen (Wi-Fi/Bluetooth) | Working | Read-only status + connect to paired Bluetooth; Android reserves actually toggling Wi-Fi/BT to its own Settings app |
| Owner profile (name/phone) | Working | Informational only, stored on-device -- explicitly NOT a login/security feature |
| Update checker | Working | Checks your GitHub repo's public Releases, opens the page for manual install -- never auto-installs anything |
| Settings (name, wake phrase, voice style, AI key, insurer app) | Working | Persisted on-device |
| Open-ended conversation with real reasoning | Optional | Off by default; add an API key in Settings |
| Route options with live ETA comparisons | Not built | Would need Google Directions API (paid at scale) -- next phase candidate |

## Honest limitations (read before you expect more than this delivers)

- **Emotional voice**: Android's TTS engine has no real "sound sad" or
  "sound excited" control. What this app does is shift pitch and speaking
  rate based on detected emotion, which reads as *more expressive* than
  flat, but it is not actorly emotional speech. For that you'd eventually
  want a cloud TTS with emotion styles (ElevenLabs, Azure Neural voices) —
  there's a marked swap-in point in `tts_engine.py`.
- **RPM**: there is no way to get real engine RPM without a physical
  Bluetooth OBD-II adapter (~$10-15 ELM327 dongle) plugged into your
  car's OBD-II port. Regular car Bluetooth (the audio/hands-free kind)
  does not expose this data. Without the dongle, the RPM gauge has
  nothing to show.
- **Radio**: phones generally don't expose the FM radio chip without
  carrier-specific support, so this streams internet radio instead of
  broadcast FM. Swap in your own station URLs in `media_manager.py`.
- **Spotify/YouTube control**: these hand off to the real apps rather
  than reimplementing playback — the reliable way to do this without
  needing OAuth app registrations with Spotify/Google. Deeper in-app
  control (skip track without leaving Mandy) is a further phase.
- **Open-ended conversation**: without an API key in Settings, Mandy
  responds using a small set of built-in, honest responses — she will
  tell you she's not able to reason about something rather than fake it.
  Add a Claude API key in Settings and she'll use it for real.
- **Dashboard display (showing up on your car's built-in screen)**: not
  built yet — this currently runs on your phone's screen only. That
  needs Android Auto integration, a separate project phase.
- **Voiceprint ("recognize my voice")**: this compares pitch and speech
  rhythm between your enrolled voice and each command -- not a trained
  neural speaker-recognition model. It will reliably reject clearly
  different voices, but it is not bank-grade security and could in
  theory be fooled by a good impression. Enroll your voice in
  Settings → "Train Mandy on my voice."
- **Vehicle documents (Insurance/PUC/Registration/DL)**: entirely
  self-reported. There is no public API for a third-party app to check
  Vahan/Sarathi/mParivahan records, so this only tracks the dates you
  type in -- it cannot confirm your actual government records are
  correct or current.
- **RajmargYatra / mParivahan / insurer app**: these buttons only
  *launch* the real apps (or their Play Store page if not installed).
  None of them offer a public API, so Mandy can't pull data out of them
  or verify anything they show.
- **Toll alerts**: `assets/toll_database.json` ships with two clearly
  labeled EXAMPLE entries (fake prices, arbitrary coordinates) — not
  real, current toll data. Replace them with real toll plazas along
  your routes (name, lat/lon, radius, price per vehicle class) from
  NHAI's official FASTag toll list for this to be trustworthy. The
  detection engine itself (geofencing + cooldown) is fully real and
  tested.
- **Speed limit tracker**: uses OpenStreetMap's crowd-sourced `maxspeed`
  tags via the free Overpass API. Coverage is incomplete, especially
  off major highways — no warning shown doesn't mean you're within a
  legal limit, it may just mean the road isn't tagged. Needs internet.

## Project structure

```
Mandy/
├── main.py                    # App entry point, screen manager
├── screens/
│   ├── home_screen.py          # Mandy's face + voice interaction
│   ├── dashboard_screen.py     # Speedometer, RPM, toll alerts, speed limit
│   ├── media_screen.py         # Spotify / YouTube / Radio
│   ├── calls_screen.py         # Phone calling
│   ├── navigate_screen.py      # Manual destination entry
│   ├── documents_screen.py     # Vehicle number + document expiry tracker
│   ├── file_explorer_screen.py # Browse device storage
│   └── settings_screen.py      # Name, wake phrase, voice, AI key, insurer app
├── mandy_avatar.py             # Animated face widget
├── voice_engine.py             # Speech-to-text + raw audio capture
├── voiceprint_engine.py        # Lightweight speaker verification
├── wake_word_engine.py         # "Hi Mandy" / "Hey Mandy" always-listening
├── tts_engine.py                # Text-to-speech with emotion shift
├── conversation_engine.py       # Intent parsing + emotion detection
├── llm_client.py                 # Optional real AI backend (Claude API)
├── navigation.py                # Destination parsing + Maps launch
├── call_manager.py              # Phone calls + contact lookup
├── media_manager.py             # Spotify/YouTube/Radio launching
├── gps_speed.py                  # Real GPS speed + location tracking
├── obd_reader.py                 # Real RPM via OBD-II Bluetooth adapter
├── toll_engine.py                 # Toll plaza geofencing + price lookup
├── speed_limit_tracker.py         # Posted speed limit via OpenStreetMap
├── vehicle_documents.py            # Insurance/PUC/Registration/DL tracking
├── external_apps.py                # RajmargYatra/mParivahan/insurer launcher
├── bluetooth_manager.py          # General Bluetooth pairing/connection
├── widgets.py                    # Reusable circular gauge widget
├── settings_store.py             # Persistent on-device settings
├── buildozer.spec                # Android packaging config
├── requirements-desktop.txt      # For testing on your computer first
└── assets/
    ├── mandy_face.png            # Her face
    ├── icon.png                  # App icon
    └── toll_database.json        # EXAMPLE toll data -- replace with real data
```

## Step 1 — Test on your computer first (recommended)

```bash
pip install -r requirements-desktop.txt
python main.py
```

On desktop: GPS speed and RPM are simulated with fake fluctuating values
so you can see the gauges move without a phone or OBD adapter. Voice
uses your computer's mic; navigation opens in your browser; calls/Spotify/
YouTube just print what they *would* do, since there's no Android to
hand off to.

## Step 2 — Build the real Android APK

You have two options. **Option A needs no Linux machine at all** — recommended.

### Option A: Build in the cloud with GitHub Actions (no Linux needed)

This project already includes `.github/workflows/build-apk.yml`, which
builds a real APK automatically using GitHub's free cloud servers.

1. Create a free GitHub account if you don't have one: https://github.com/signup
2. Create a new repository (e.g. "Mandy"), and upload/push everything in
   this `Mandy/` folder to it. Easiest way if you're not familiar with
   git: on the repo's GitHub page, click **"Add file" → "Upload files"**,
   drag in the whole folder contents, and commit.
3. Go to the **Actions** tab on your repo. A workflow called "Build
   Mandy APK" will either already be running (it auto-runs on every
   push) or you can click **"Run workflow"** to start it manually.
4. Wait ~15-25 minutes (cloud build, first run is slower). When it's
   green/finished, click into the run, scroll to **Artifacts**, and
   download **mandy-apk** — that's your `.apk` file, zipped.
5. Unzip it, transfer the `.apk` to your phone (email, Drive, USB —
   any way), and install it (see Step 3 below).

No Linux machine, no local Android SDK download, nothing to install on
your own computer except a web browser.

The same workflow run also produces a second artifact,
**mandy-android-studio-project** — the actual generated Gradle/Android
project (Python bundled inside it), ready to open in Android Studio.

### Opening the project in Android Studio

1. Download and unzip **mandy-android-studio-project** from the
   Actions run (see steps above).
2. Open Android Studio → **File → Open** → select the unzipped
   `mandy-android-project` folder.
3. Let Gradle sync (first time can take a few minutes — it's a real
   Android project, just like any Java/Kotlin app).
4. Connect your phone (USB debugging on) or start an emulator, then hit
   the green **Run ▶** button like any other Android Studio project.
5. From here you also get Android Studio's normal tools for free:
   Logcat for debugging, generating a signed release build (Build →
   Generate Signed Bundle/APK) if you ever want to distribute it more
   widely, etc.

One thing to know: this generated project is Buildozer/python-for-android's
output, not something meant to be hand-edited long-term. If you change
Mandy's Python source (`main.py` and friends), re-run the GitHub Actions
build (or `buildozer android debug` locally) to regenerate this folder
with your changes — editing the generated Java/Gradle files directly
won't carry over.

### Option B: Build locally on Linux or WSL2

Must be done on Linux or WSL2 (Buildozer doesn't support Windows/macOS
directly).

```bash
# One-time setup
sudo apt update
sudo apt install -y python3-pip build-essential git python3 python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev

pip3 install --break-system-packages buildozer cython

cd Mandy
buildozer -v android debug
```

First build downloads the Android SDK/NDK automatically (30-60 min).
APK will be at:

```
bin/mandy-0.1-arm64-v8a-debug.apk
```

Install with `adb install bin/*.apk` (phone plugged in) or copy the file
to your phone and allow "install from unknown sources."

## Step 3 — First run on your phone

1. Grant microphone, Bluetooth, location, phone, and contacts permissions
   when prompted.
2. Go to Settings in the app: set your name, pick a wake phrase (not yet
   wired to always-listening — see Next phases), choose a voice
   personality label, and optionally add an AI API key for real
   conversation.
3. Pair your car's Bluetooth as usual, and if you have one, pair your
   OBD-II Bluetooth adapter too.
4. Mount your phone, open Mandy, tap "Talk to Mandy," and try:
   - *"Navigate to [destination]"*
   - *"Call [contact name]"*
   - *"Play [song] on Spotify"*
   - *"Open YouTube"*
   - *"Open radio"*
   - *"I'm exhausted today"* (she'll respond with a calmer, supportive tone)

## A note on security design choices

A few feature requests along the way (phone "registration," remote
"unlimited upgrades," auto-installing third-party APKs) could have been
built in a way that created real security problems -- specifically, an
unauthenticated public backend that could be tricked into pushing
software installs, and a "registration" screen that implied a security
check it didn't actually perform. Those versions were deliberately not
used. What's in this project instead:

- **Owner phone number**: stored locally, labeled clearly as
  informational only -- it is not a login and doesn't gate anything.
- **Update checking**: reads your GitHub repo's public Releases (a
  read-only, no-auth-needed source you control) and opens the release
  page for you to manually download and tap-install. Nothing is ever
  triggered remotely or installed without you choosing to.
- **AI backend**: your API key stays local to your device and talks
  directly to Anthropic's servers over TLS -- no self-hosted proxy
  server exposed to the public internet, so there's nothing for someone
  else to find and abuse.

## Making Mandy the home screen (instead of your phone's normal launcher)

You asked for "only Mandy on the main screen." There are two very
different things this could mean, with very different risk levels:

**Option A -- Mandy as a selectable Home app (what's documented here):**
Android lets multiple apps register as "Home" launchers; when you press
the device's Home button, Android asks which one to use (or lets you
set a default in Settings). To make Mandy one of the options:

1. After a successful `buildozer android debug` build, find the
   generated manifest template:
   `.buildozer/android/platform/build-armeabi-v7a/dists/mandy/templates/AndroidManifest.tmpl.xml`
2. Find the `<activity>` block for the main activity (search for
   `android.intent.action.MAIN`).
3. Add a second `<intent-filter>` alongside the existing one:
   ```xml
   <intent-filter>
       <action android:name="android.intent.action.MAIN" />
       <category android:name="android.intent.category.HOME" />
       <category android:name="android.intent.category.DEFAULT" />
   </intent-filter>
   ```
4. Rebuild (`buildozer android debug`). Install it, press Home on the
   device, and Android will offer Mandy as a Home app option.

Importantly: this does **not** lock you into Mandy. You (or anyone
with the device) can still switch back to the normal launcher anytime
via Settings -> Apps -> Default apps -> Home app, or by long-pressing
Home and picking a different one.

**Option B -- a true, un-exitable kiosk lock (NOT built here):**
Forcing the device to *only* ever show Mandy, with no way to switch
away without special access, needs Android's Device Owner / Lock Task
Mode APIs. This is a much bigger, riskier step: it typically has to be
set up before any Google account is added to the device, and a
misconfigured Device Owner app can be genuinely difficult to remove
without a full factory reset. Given how much we've already had to
debug in this build pipeline, I'd want to walk through this
deliberately and separately, with a plan for how to safely undo it, if
you decide you actually want it -- not bundle it into a routine update.

## Next phases (recommended order)


1. **Always-listening wake word** ("Mandy, I need you") instead of
   tap-to-speak — needs an offline wake-word engine (e.g. Porcupine)
   running as a background service.
2. **Cloud emotional TTS** (ElevenLabs/Azure) for genuinely expressive
   speech instead of pitch/rate approximation.
3. **Android Auto integration** so Mandy shows up on your car's own
   screen, not just your phone.
4. **Deeper Spotify control** via the Spotify Web API (needs your own
   app registration with Spotify) for in-app playback control.

Tell me which one you want next and I'll build it in.
