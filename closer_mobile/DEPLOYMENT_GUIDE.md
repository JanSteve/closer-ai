# CLOSER AI: Mobile App Store & Google Play Store Deployment Guide

**Application ID:** `ai.closer.telecaller`  
**Version:** `2.0.0`  
**Platform Target:** iOS (App Store / TestFlight) & Android (Google Play Store)

---

## 1. Quick Local Preview

You can run and test the complete production mobile app right now on your computer or mobile browser:

```bash
# Start the FastAPI Telephony Gateway with Mobile Web UI
python3 -m uvicorn closer.telephony.server:app --host 0.0.0.0 --port 8000
```

Open your browser at **`http://localhost:8000`** (or access from your iPhone/Android on the same Wi-Fi using your Mac's IP `http://<your-mac-ip>:8000`).

---

## 2. Compiling for iOS App Store (Xcode)

### Prerequisites
- macOS with Xcode installed (`xcode-select --install`)
- Apple Developer Account ($99/year for public App Store distribution, or free for local device testing)

### Build Steps
```bash
cd "closer_mobile"

# 1. Initialize native iOS project
npx @capacitor/cli add ios

# 2. Sync web assets & plugins
npx @capacitor/cli sync ios

# 3. Open in Xcode
npx @capacitor/cli open ios
```

### In Xcode:
1. Under **Signing & Capabilities**: Select your Apple Developer Team.
2. Verify Bundle Identifier: `ai.closer.telecaller`.
3. In `Info.plist`, verify microphone permission string:
   - `NSMicrophoneUsageDescription`: *"CLOSER AI requires real-time microphone access to enable high-ticket voice sales calls and instant human interruption."*
4. Select **Any iOS Device (arm64)** $\to$ **Product** $\to$ **Archive**.
5. Click **Distribute App** $\to$ **App Store Connect** $\to$ Submit to **TestFlight** or **App Store**.

---

## 3. Compiling for Google Play Store (Android Studio)

### Prerequisites
- Android Studio with Android SDK 34+
- Google Play Console Developer Account ($25 one-time fee)

### Build Steps
```bash
cd "closer_mobile"

# 1. Initialize native Android project
npx @capacitor/cli add android

# 2. Sync web assets & plugins
npx @capacitor/cli sync android

# 3. Open in Android Studio
npx @capacitor/cli open android
```

### In Android Studio:
1. Verify permissions in `AndroidManifest.xml`:
   ```xml
   <uses-permission android:name="android.permission.RECORD_AUDIO" />
   <uses-permission android:name="android.permission.INTERNET" />
   <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
   ```
2. Navigate to **Build** $\to$ **Generate Signed Bundle / APK**.
3. Choose **Android App Bundle (.aab)**.
4. Select or create your keystore.
5. Upload the resulting `.aab` file to **Google Play Console** under **Production** or **Internal Testing**.

---

## 4. Top Recommended GitHub Repos & Skills for Mobile Voice AI

For production-ready native integrations:

1. **[livekit-examples/agent-starter-flutter](https://github.com/livekit-examples/agent-starter-flutter)**:
   - LiveKit official cross-platform Flutter voice assistant with WebRTC and sub-300ms audio streaming.
2. **[extrawest/livekit_voice_assistant](https://github.com/extrawest/livekit_voice_assistant)**:
   - Production voice assistant combining Silero VAD, Groq/Ollama LLM, and Kokoro TTS on mobile.
3. **[keyur2maru/vad](https://github.com/keyur2maru/vad)** (`vad-flutter` on Pub.dev):
   - Flutter native FFI ONNX bindings for Silero VAD v5 running directly on iOS CoreML and Android NNAPI.
4. **[TheWidlarzGroup/react-native-voice-agent](https://github.com/TheWidlarzGroup/react-native-voice-agent)**:
   - React Native Expo audio pipeline with interruption and streaming audio buffers.
