# Android client

Native Android app module. It listens for PC Controller UDP beacons on port 9051, lists PCs discovered on the same Wi-Fi, pairs with the six-digit code, and opens the shared dashboard in an Android WebView.

The pairing token is encrypted at rest with an AES-GCM key held by Android Keystore.

## Build a debug APK

Requires JDK 17 and Android SDK platform 35.

```bash
cd android
gradle :app:assembleDebug
```

APK output: `android/app/build/outputs/apk/debug/app-debug.apk`.

The GitHub Actions workflow builds and uploads a debug APK artifact for pushes and pull requests that touch the Android project. This first native client wraps the shared mobile dashboard; a dedicated native touchpad and screen-streaming UI is a later iteration.
