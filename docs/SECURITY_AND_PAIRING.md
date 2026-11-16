# LAN pairing and security

PC Controller is designed for trusted devices on the same private Wi-Fi network.

## Pairing flow

1. Start the Windows desktop agent.
2. Open the tray icon menu and choose **Pair a device**.
3. Scan the QR code or open the mobile connection page and enter the six-digit code.
4. The desktop agent issues a random bearer token to the paired device.
5. The token is stored as a SHA-256 digest in the desktop user's local application-data folder. The browser stores its token for this PC origin.
6. Use the local desktop settings page to revoke a paired device at any time.

The pairing code rotates on each desktop-agent start. Failed attempts are rate-limited.

## Permissions

The desktop permissions page is available locally at:

`http://127.0.0.1:9050/static/desktop.html`

Status, media, volume and brightness are enabled initially. App launching, desktop shortcuts, screen viewing, mouse/keyboard input, screen lock and power operations are disabled until explicitly enabled. App launching is separately allowlisted.

The API rejects remote requests without a paired token and checks the corresponding permission for every control route. The desktop's loopback UI remains available without pairing.

## Network notes

- Both devices must be connected to the same private Wi-Fi/LAN.
- Allow PC Controller through Windows Defender Firewall on **Private networks** only.
- UDP broadcast discovery uses port 9051; the HTTP API uses port 9050.
- Guest Wi-Fi isolation, VPNs, VLAN separation or router client isolation can prevent discovery.
- This initial LAN transport uses HTTP. Use only on a trusted private network; do not port-forward the API or expose it to the public internet. A TLS certificate/pinning flow is required before claiming transport encryption.

## Remote screen and input

Screen viewing and mouse/keyboard control are separate opt-in permissions. Screen capture returns a resized JPEG data URL. Click coordinates are clamped to the current desktop bounds, and keyboard input is restricted to a small allowlist.

## Data location

Pairing records and permissions are stored under:

`%LOCALAPPDATA%/PCController/`

Removing the application does not automatically remove this folder; users can delete it after uninstalling if they want to clear local pairing data.
