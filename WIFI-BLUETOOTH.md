# AETHER OS — Wi-Fi & Bluetooth Architecture Specification

## 1. Overview

AETHER OS incorporates native, real-system networking and peripheral subsystems through modular Python backends:
- `/usr/lib/aether-os/aether_network.py` (`NetworkManagerBackend`)
- `/usr/lib/aether-os/aether_bluetooth.py` (`BluetoothBackend`)

These backends are shared across the **AETHER Control Center** (`control-center.py`), the **AETHER Settings Hub** (`aether-settings.py`), and desktop status widgets.

---

## 2. Wi-Fi Architecture (`aether_network.py`)

### System Integration
```
[ AETHER Control Center / Settings ]
                  │
                  ▼  (async Python threads)
    [ NetworkManagerBackend ]
                  │
                  ▼  (subprocess / D-Bus)
       [ NetworkManager / nmcli ]
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
 [ wpa_supplicant ]     [ Linux Kernel / nl80211 ]
       │                     │
       ▼                     ▼
 [ Wi-Fi Hardware ]    [ 802.11 Access Points ]
```

### Core Operations

#### 1. Hardware Presence & Radio Query
```python
info = net_backend.get_wifi_adapter_info()
# Returns:
# {
#   "has_adapter": bool,
#   "device": "wlan0",
#   "state": "disconnected"|"connected"|"unavailable",
#   "enabled": True|False,
#   "error_hint": str
# }
```
When running in VirtualBox or QEMU without USB Wi-Fi passthrough, `has_adapter` evaluates to `False`. The backend detects the hypervisor via `systemd-detect-virt` and provides clear instructions:
> *"No Wi-Fi adapter detected in this virtual machine. VMs use virtual Ethernet by default. To test Wi-Fi, attach a USB Wi-Fi dongle."*

#### 2. Asynchronous Network Discovery
Scanning is executed off the main thread:
```bash
nmcli -t -f SSID,BSSID,SIGNAL,SECURITY,IN-USE dev wifi list --rescan yes
```
- Colon-escaped SSIDs are normalized.
- Empty and hidden SSIDs are handled safely.
- Multi-BSSID networks (mesh/roaming) are deduplicated, preserving the entry with the strongest signal or the currently connected BSSID.
- Results are sorted: active connection first, followed by descending signal strength.

#### 3. Security Classification
The raw security string is classified into standard categories:
- **WPA3**: Modern SAE / WPA3-Personal
- **WPA2**: WPA2-PSK (AES / TKIP)
- **WPA**: Legacy WPA
- **WEP**: Legacy WEP
- **Open**: Unsecured public network

#### 4. Authentication and Connection
Connecting to a network is non-blocking:
```python
net_backend.connect_wifi(ssid, password=pw, hidden=is_hidden, callback=on_result)
```
- If the network was previously saved in `/etc/NetworkManager/system-connections/`, credentials are auto-supplied by NetworkManager.
- If credentials fail, specific error messages are captured:
  - `"Secrets were required"` -> *"Incorrect Wi-Fi password. Please check your credentials."*
  - `"No network with SSID"` -> *"Network was not found or is out of range."*
  - `"Connection activation timed out"` -> *"Connection timed out. Access point did not respond."*

---

## 3. Bluetooth Architecture (`aether_bluetooth.py`)

### System Integration
```
[ AETHER Control Center / Settings ]
                  │
                  ▼  (async Python threads)
       [ BluetoothBackend ]
                  │
                  ▼  (subprocess / D-Bus)
       [ BlueZ / bluetoothctl ]
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
 [ rfkill subsystem ]   [ Linux Bluetooth Subsystem ]
       │                     │
       ▼                     ▼
 [ HCI Controller ]     [ Nearby BLE & Classic Devices ]
```

### Core Operations

#### 1. Controller Detection & Status
```python
bt_info = bt_backend.get_adapter_info()
# Returns:
# {
#   "has_adapter": bool,
#   "name": "aether-0",
#   "mac": "XX:XX:XX:XX:XX:XX",
#   "powered": bool,
#   "discovering": bool,
#   "error_hint": str
# }
```

#### 2. Device Classification Engine
The backend inspects Device Alias, Icon, and Class of Device (CoD) from `bluetoothctl info <MAC>` and categorizes devices:
| Category | Matching Patterns | Symbolic Icon |
| :--- | :--- | :--- |
| **Audio (Headphones)** | `headphone`, `headset`, `earbuds`, `airpods`, `buds`, `wh-`, `wf-` | `audio-headphones-symbolic` |
| **Audio (Speakers)** | `speaker`, `soundbar`, `boombox` | `audio-speakers-symbolic` |
| **Input (Keyboards)** | `keyboard`, `keychron` | `input-keyboard-symbolic` |
| **Input (Mice)** | `mouse`, `trackpad`, `touchpad`, `mx master` | `input-mouse-symbolic` |
| **Input (Gamepads)** | `controller`, `gamepad`, `joystick`, `xbox`, `dualsense` | `input-gaming-symbolic` |
| **Phones** | `phone`, `iphone`, `pixel`, `galaxy`, `android` | `phone-symbolic` |
| **Computers** | `laptop`, `desktop`, `macbook`, `pc` | `computer-symbolic` |

#### 3. Battery Reporting
Parses the BlueZ `Battery Percentage` field (e.g. `Battery Percentage: 0x5a (90)`) to report peripheral battery health directly in the device card.

---

## 4. Hardware vs Virtualized Behavior

| Environment | Wi-Fi Behavior | Bluetooth Behavior | Ethernet Behavior |
| :--- | :--- | :--- | :--- |
| **VirtualBox VM (NAT)** | Displays VM notice; no fake APs shown | Displays VM notice; no fake devices shown | `enp0s3` connected via virtual host NAT |
| **VirtualBox VM (USB Passthrough)**| Real Wi-Fi scanning, connection, WPA2/3 | Real BT discovery, pairing, audio connect | Fully functional |
| **Physical Intel/AMD Laptop** | Full iwlwifi/ath9k/rtw88 hardware scan | Intel/Broadcom BT controller discovery | Physical RJ-45 / USB-C Ethernet |
| **Live ISO Environment** | Works out-of-the-box via live user polkit | Works out-of-the-box via bluez daemon | Auto-DHCP active |
