# Mobile clients

The shared mobile web client is served by the Windows host at:

`http://<PC-LAN-IP>:9050/static/connect.html`

Connect the phone to the same private Wi-Fi, open the connection page, and enter the one-time code shown by the Windows tray agent. The paired browser then opens the existing responsive dashboard.

The API also emits a UDP discovery beacon on port 9051 so a future native Android client can discover hosts without asking the user to type an IP address.

## Native Android

A signed APK is not included in this foundation change. The next milestone is a native Android client that listens for the UDP beacon, lists discovered PCs, pairs using the displayed code, stores its token in Android Keystore, and presents the shared remote-control API in a native touch-first interface.

## iPhone and other devices

Use the mobile web client in Safari or another browser. A native iOS app is not required for the local-network control workflow.
