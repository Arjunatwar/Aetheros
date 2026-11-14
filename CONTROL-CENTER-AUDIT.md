# AETHER OS — Control Center Audit & Architecture

## 1. Executive Summary

The AETHER OS Control Center (`/usr/lib/aether-os/control-center.py`) is the primary quick-settings hub for the AETHER desktop environment. It implements the macOS/Aether purple-blue glass interface with fully functional, real-system Linux backends.

Unlike superficial desktop widgets that display static mockups, the AETHER Control Center communicates directly with real system daemons:
- **NetworkManager** (`nmcli` / D-Bus) for Wi-Fi and Ethernet
- **BlueZ** (`bluetoothctl` / D-Bus) for Bluetooth discovery, pairing, and battery status
- **PulseAudio / PipeWire** (`pactl`) for output/input sinks, sources, and master volume
- **Linux Backlight / XRandR** (`brightnessctl` & `xrandr`) for display brightness
- **Linux RFKill subsystem** (`rfkill`) for hardware and software radio isolation
- **AETHER Adaptive Visual Engine** for performance profile orchestration

---

## 2. Component Architecture

```
+--------------------------------------------------------------------------+
|                       AETHER Control Center Hub                          |
+--------------------------------------------------------------------------+
|  [Header] Control Center                                            [✕]  |
|                                                                          |
|  +-------------------------+  +-------------------------+                |
|  |  📶 Wi-Fi               |  |  ᛒ Bluetooth            |                |
|  |     Connected: "Home"  ›|  |     On / 2 Devices     ›|                |
|  +-------------------------+  +-------------------------+                |
|  |  🖧 Ethernet            |  |  ✈ Airplane Mode        |                |
|  |     Connected (eth0)    |  |     Off                 |                |
|  +-------------------------+  +-------------------------+                |
|                                                                          |
|  ☼ [=================== Display Brightness (85%) ===================]    |
|  🔊 [=================== Master Audio Volume (75%) ==================]    |
|                                                                          |
|  ▼ Audio Output & Input                                                  |
|     Output: [Built-in Analog Stereo / HDMI / VirtualBox Audio ▼]         |
|                                                                          |
|  [Display]         [Sound]            [Power]          [Appearance]      |
|                                                                          |
|  Performance Mode: [Balanced (Adaptive) ›]                               |
+--------------------------------------------------------------------------+
|                      Adaptive Visual Engine Card                         |
|  ✦ Adaptive Visual Engine                                             ●  |
|  [ Balanced Mode ]                                                       |
|  Auto-optimized for your hardware (4 GB RAM, 2 cores, VirtualBox)        |
+--------------------------------------------------------------------------+
```

### Expandable Submenu Flow
When clicking the **Wi-Fi** or **Bluetooth** tiles (indicated by `›`), the Control Center transitions seamlessly into dedicated management submenus via a GTK `Stack` with horizontal slide animations.

---

## 3. Wi-Fi Management Submenu

### Features & Capabilities
1. **Radio State Toggle**: Real-time switch toggling `nmcli radio wifi on|off`.
2. **Hardware Detection**: Queries `nmcli dev` for devices of type `wifi`. If no wireless adapter is detected (e.g. default VirtualBox NAT), it clearly explains the absence and guides the user rather than faking networks.
3. **Active Connection Display**: Displays active SSID, interface name, IP address, and signal strength. Provides direct **Disconnect** and **Forget Network** actions.
4. **Asynchronous Network Scanning**: Background thread triggers `nmcli dev wifi list --rescan yes`, parses SSIDs, signal levels (0–100%), security protocols (WPA3/WPA2/WPA/WEP/Open), and active status.
5. **Interactive Connection**:
   - For open/saved networks: connects immediately without prompting.
   - For secured networks: opens an interactive password dialog with password visibility toggle (👁).
   - Provides clear progress notifications and friendly error reporting (e.g. incorrect credentials, AP timeout).
6. **Hidden Networks**: Supports joining non-broadcasting SSIDs with security parameters.

---

## 4. Bluetooth Management Submenu

### Features & Capabilities
1. **Radio State Toggle**: Real-time switch toggling `bluetoothctl power on|off` and `rfkill unblock/block bluetooth`.
2. **Adapter Status**: Queries `bluetoothctl show` for adapter MAC, name, discovering state, and powered state. If missing in a VM, displays helpful passthrough guidance.
3. **Asynchronous Discovery**: Background scanning via `bluetoothctl scan on`, refreshing discovered devices at 1.5s intervals.
4. **Device Classification**: Automatic classification into Audio (headphones, speakers), Input (mice, keyboards, controllers), Phones, and Computers with context-aware symbolic icons.
5. **Pairing & Connection**: Handles `pair`, `trust`, `connect`, `disconnect`, and `remove` operations asynchronously.
6. **Battery Reporting**: Parses `Battery Percentage` from BlueZ device info and surfaces it in the UI.

---

## 5. Audio & Brightness Integration

### Audio Output / Input Chooser
- Direct integration with PulseAudio / PipeWire through `pactl list sinks` and `pactl list sources`.
- Dynamically populates available audio hardware (Built-in Audio, HDMI output, USB DACs, virtual sinks).
- Live volume scaling using `pactl set-sink-volume @DEFAULT_SINK@ <val>%`.

### Brightness Controller
- Primary: Hardware backlight control using `brightnessctl`.
- Fallback: Software brightness adjustment using `xrandr --output <display> --brightness <float>`. This ensures brightness adjustment works even inside virtual machines (VirtualBox, VMware, QEMU) where virtual display adapters lack physical PWM backlights.

---

## 6. Verification & Test Matrix

| Component | Target Interface | VM Target (VirtualBox) | Physical Hardware | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Wi-Fi Toggle** | `nmcli radio wifi` | Verified (reports state) | Verified | Pass |
| **Wi-Fi Absence** | `nmcli dev` detection | Verified (shows VM hint) | N/A (Adapter present) | Pass |
| **Wi-Fi Scanning** | `nmcli dev wifi list` | Verified (safe timeout) | Discovers SSIDs | Pass |
| **Wi-Fi Auth** | Password Dialog + Toggle | Verified UI & error trap | Connects to WPA2/3 | Pass |
| **Bluetooth Toggle** | `rfkill` + `bluetoothctl` | Verified (reports state) | Verified | Pass |
| **Bluetooth Absence** | `bluetoothctl show` | Verified (shows USB hint) | Adapter detected | Pass |
| **Volume Slider** | `pactl set-sink-volume` | Verified (alters audio) | Verified | Pass |
| **Audio Sinks** | `pactl list sinks` | Lists VirtualBox Audio | Lists physical devices | Pass |
| **Brightness Slider**| `xrandr` / `brightnessctl` | Verified (xrandr dimming) | Backlight dimmed | Pass |
| **Airplane Mode** | `rfkill block/unblock` | Verified | Verified | Pass |
