# 🎬 AutoClip AI – Mobile & Cloud Architecture

AutoClip AI is an automated video clipping system designed for Twitch streams and long VODs, producing 9:16 vertical short-form highlights (for TikTok, YouTube Shorts, and Instagram Reels) powered by multi-signal peak detection and Whisper AI.

---

## 📁 Project Structure

```
Auto-Clipping/
├── backend/                  # FastAPI AI Auto-Clipping Engine
│   ├── app/
│   │   ├── main.py           # REST API & WebSocket Server
│   │   ├── models.py         # Pydantic schemas (Jobs, Clips, Requests)
│   │   └── services/
│   │       ├── clipper_service.py # Audio RMS peak detection, yt-dlp & FFmpeg 9:16 crop
│   │       └── job_manager.py     # Async job queue & real-time progress broadcast
│   ├── run_server.py         # One-click backend startup script
│   └── data/                 # Generated audio WAVs, clips, and thumbnails
│
├── web_mobile/               # Zero-Install Mobile PWA Interface (Run directly on Android phone)
│   ├── index.html            # TikTok-style fullscreen vertical video feed
│   └── manifest.json         # PWA definition (Install to Home Screen)
│
├── android/                  # Native Android App (Kotlin + Jetpack Compose)
│   ├── app/
│   │   ├── build.gradle.kts  # Dependencies (Media3 ExoPlayer, Retrofit, Coil)
│   │   └── src/main/java/com/autoclip/ai/
│   │       ├── MainActivity.kt           # Main Compose UI & Share Intents
│   │       ├── data/api/AutoClipApi.kt   # Retrofit client for FastAPI
│   │       └── ui/player/VerticalClipPlayer.kt # Auto-looping 9:16 ExoPlayer
│   └── build.gradle.kts
│
└── .github/workflows/
    └── build-apk.yml         # Cloud APK Compiler (No Android Studio required!)
```

---

## 🚀 Quickstart: Running Without Android Studio

You do not need Android Studio installed on your computer to use or develop this app. Here are your two zero-friction options:

### Option 1: Mobile Web App / PWA (Instant Test on Your Phone Right Now)

1. **Start the Backend Server on your PC:**
   ```bash
   python backend/run_server.py
   ```
2. **Find your PC's local IP address:**
   - In PowerShell, run: `ipconfig` (look for `IPv4 Address`, e.g., `192.168.1.15`).
3. **Open on your Android Phone:**
   - Open Chrome on your Android phone connected to the same Wi-Fi.
   - Go to: `http://192.168.1.15:8000`
   - You get the full mobile UI: paste a Twitch/YouTube URL, watch real-time progress, swipe through 9:16 vertical clips, and share directly to TikTok/Instagram!
   - Tap **"Add to Home screen"** in Chrome to install it as an app icon on your phone!

---

### Option 2: Build the Native Android APK via GitHub Actions (Cloud Compiler)

Because Android Studio is not installed locally, you can let GitHub compile the APK for free in the cloud:

1. **Push this project to a GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial AutoClip release"
   git remote add origin https://github.com/YOUR_USERNAME/auto-clip.git
   git push -u origin main
   ```
2. **Download your compiled APK:**
   - Go to the **Actions** tab on your GitHub repository.
   - The workflow `Build Android APK` will automatically run.
   - Once finished (about 2–3 minutes), click on the run and download **`AutoClip-Debug-APK`**.
   - Send the `.apk` to your Android phone (or download directly on your phone) and install it!
