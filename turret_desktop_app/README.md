# ESP32-S3 Turret Desktop Controller

A Windows GUI using Python/PySide6 for the existing ESP32-S3 turret TCP firmware. No firmware changes are required to test connectivity, STATUS, ENABLE or DISABLE.

## Quick start
1. Install Python 3.10 or newer from https://www.python.org/downloads/ (enable **Add Python to PATH**).
2. Extract this folder and double-click `launch_windows.bat` (first run installs PySide6).
3. Verify the ESP32-S3 is powered, connected to Wi-Fi, and its Serial Monitor displays `TCP Server listening on port 5000`.
4. Enter the actual ESP32 IP address (defaults to `192.168.0.118` from the last bench test) and port 5000, then click **Connect**.
5. Click **Refresh status**; optionally **Enable drivers** and **Disable drivers**.
6. The PAN/TILT and MOVE controls intentionally send commands to the existing firmware, which currently replies `NOT_IMPLEMENTED` and **does not move motors**.

## Existing protocol
ESP32 TCP server (`WiFiServer`) listens on port 5000, UTF-8 lines terminated by newline. Upon connection it sends `CONNECTED`.

| Client sends | Current ESP32 response |
|---|---|
| `STATUS\n` | `STATUS`, `WIFI=...`, `MOTORS=...`, `PAN=NOT_IMPLEMENTED`, `TILT=NOT_IMPLEMENTED`, `END_STATUS` |
| `ENABLE\n` | `OK ENABLED` |
| `DISABLE\n` | `OK DISABLED` |
| `PAN 10\n` | `NOT_IMPLEMENTED PAN` |
| `TILT -10\n` | `NOT_IMPLEMENTED TILT` |
| `MOVE 10 -5\n` | `NOT_IMPLEMENTED MOVE` |
| `STOP\n` | `NOT_IMPLEMENTED STOP` |

## Hardware mapped by ESP32 firmware
- Motor 1 / pan: STEP GPIO4, DIR GPIO6, ENABLE GPIO2
- Motor 2 / tilt: STEP GPIO17, DIR GPIO18, ENABLE GPIO16
- A4988 ENABLE LOW = outputs active, HIGH = outputs off
- A4988 RESET and SLEEP both pulled to 3.3 V; common ground

## Safety notes
- The current firmware has **no implemented motion, STOP mechanism, physical feedback or homing**. The desktop STOP button only sends the placeholder command and **is not an emergency stop**.
- Disabling an A4988 removes holding torque: support the tilt axis to prevent it dropping.
- Wi-Fi/TCP disconnect does not automatically disable the motors with the present firmware. An independent physical power cut-off/stop is needed for mechanical safety.
- TCP port 5000 is **unauthenticated and unencrypted** in the current firmware. Use a trusted private LAN, not an exposed public network.
- The address is allocated by the router and may change; consult the Arduino Serial Monitor for the latest address.
