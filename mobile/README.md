# Mobile clients

## Android application

The native Android project is in `android/`. It listens for PC Controller UDP beacons on port 9051, lists discovered Windows PCs, pairs using the one-time six-digit code, and opens the shared remote dashboard. Pairing tokens are encrypted with an AES-GCM key held by Android Keystore.

A debug APK is built by the `Android APK` GitHub Actions workflow. The workflow uploads the APK as an artifact; it is not yet a signed Play Store release.

## iPhone and other devices

The shared mobile web client is served by the Windows host at:

`http://<PC-LAN-IP>:9050/static/connect.html`

Connect the phone and PC to the same private Wi-Fi. Scan the pairing QR code from the Windows tray menu or open the connection page and enter the one-time code. Safari and other modern browsers can then use the responsive dashboard.

## Shared API

Both clients use the same Windows FastAPI service. The desktop permissions page controls which actions each paired device can perform. See [../docs/SECURITY_AND_PAIRING.md](../docs/SECURITY_AND_PAIRING.md).
