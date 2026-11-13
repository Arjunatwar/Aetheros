# AETHER OS adaptive visual effects engine

**Phase:** 2.5 — implementation built into the 2026-11-12 development ISO; validation in progress.  
**Status:** automatic/manual controls work in the tested live session. Sustained-load behavior, installed-user persistence, accelerated physical GPUs, and the target host remain unverified.

## Design

`adaptive-effects.py` runs as one per-user XFCE autostart process. It reads local kernel and display state; it does not send telemetry or keep a privileged service. It polls every 10 seconds and writes current metrics/effect status under `~/.cache/aether-os/`. Per-user mode and effect overrides are stored in `~/.config/aether-os/visual-effects.json` using an atomic file replacement. The settings screen refreshes its display every five seconds.

### Inputs

| Signal | Source | Limit |
|---|---|---|
| Total, available and derived used RAM | `/proc/meminfo` (`MemTotal`, `MemAvailable`) | Kernel accounting, MiB rounded for the UI. |
| CPU utilization | Difference between successive `/proc/stat` counters | First sample is shown as sampling; aggregate across logical cores. |
| CPU core count | `os.cpu_count()` | Logical CPUs visible to the guest. |
| System load | `os.getloadavg()` | One-minute load, considered with core count. |
| GPU presence and utilization | DRM sysfs `cardN/device` PCI identifiers and `gpu_busy_percent`; `nvidia-smi` fallback | Many drivers, including this VirtualBox adapter, expose no utilization number. Missing is reported as unavailable. |
| Graphics acceleration and renderer | `glxinfo -B` direct-rendering status and renderer name | `llvmpipe`, `softpipe`, `swrast` and software rasterizers count as not accelerated. |
| Display refresh | Active `xrandr --current` mode | Refresh rate is not frame rate. |
| Rendered FPS | Not available from XFWM4 | The status stays `not exposed`; no estimate is substituted. |

The configured VirtualBox test used VMSVGA with 3D acceleration off. The guest identified VMware-compatible graphics but rendered through `llvmpipe`; GPU utilization and accelerated OpenGL were unavailable. Blur was disabled in this configuration.

## Profile recommendation

The current starting thresholds are deliberately conservative:

| Condition | Automatic recommendation |
|---|---|
| Less than 3.6 GiB visible RAM, or fewer than two visible CPU cores | Lightweight |
| 3.6–7.5 GiB RAM with no detected hardware-accelerated OpenGL | Lightweight |
| 3.6–7.5 GiB RAM with accelerated OpenGL | Balanced |
| 7.5–15.5 GiB RAM | Balanced |
| At least 15.5 GiB, accelerated OpenGL, and at least four CPU cores | Ultra |
| At least 15.5 GiB without both the GPU and CPU conditions | Balanced |

These are suggestions, not fixed claims of performance. The displayed recommendation combines the initial memory bands with graphics and core availability. For example, a 4 GiB VMSVGA guest without acceleration is recommended Lightweight.

## Runtime adaptation and hysteresis

- Low memory is available RAM below `max(512 MiB, 12% of total RAM)`.
- High CPU is an aggregate sample at or above 86%. It counts toward a downgrade only while one-minute load is at least 1.15 times the visible CPU-core count.
- Three consecutive high-load samples, low memory, or GPU utilization of at least 92% while CPU is high can step the automatic profile down by one level. A 60-second cooldown limits profile changes.
- Recovery requires no low-memory condition, CPU below 86%, load below 0.65 per core, and available RAM above `max(1,024 MiB, 28% of total)`, sustained for 12 polls (two minutes). After a 90-second cooldown the engine restores at most one profile level, then reevaluates.
- A manually selected Lightweight, Balanced, or Ultra mode pauses automatic profile switching. Selecting Automatic resumes it. Individual checkboxes save per-user overrides; “Use profile defaults” clears those overrides.

Pressure thresholds, hysteresis timing, and long-run responsiveness have not been stress-tested yet. Short-window behavior must not be described as validated until a controlled CPU/RAM load test is completed on the VM.

## Rendering strategy and fallbacks

| Effect | Lightweight | Balanced | Ultra | Current limitation/fallback |
|---|---|---|---|---|
| Blur | Off | Only with acceleration and at least 8 GiB | Only with acceleration | Requires accelerated OpenGL compositor; control is disabled without it. |
| Transparency | Off | On | On | Picom inactive opacity; profile uses XRender without blur. |
| Shadows | Off | On | On | Picom or XFWM fallback. |
| Dock animation | Off | Plank magnification | Plank stronger magnification | Magnification is supported; Plank launch bounce is not exposed by the packaged schema. |
| Window animation | Off | Fade | Fade | Picom fading, or the XFWM compositor fallback if Picom fails. |
| Desktop transitions | Off | Off | Off | Not supported by the selected XFWM4 session. |
| Notification animation | Off | Fade-out | Fade-out | Xfce notification daemon setting. |

The effect controller stops its owned Picom child before changing profiles and writes a small local config. It chooses GLX only when accelerated blur is enabled; otherwise it uses the XRender backend. If Picom cannot start, it falls back to XFWM's built-in compositor. It does not start an animation-rendering thread of its own. Manual modes cannot bypass renderer capability checks: blur stays off without acceleration and desktop transitions are always disabled.

## VirtualBox observations

Validation ISO: `dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso`, SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`.

Host: VirtualBox 7.2.22 on Windows 11 Home, Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This is not the specified 4th-generation Core i3 / 4 GiB host. Each guest had 2 vCPUs, VMSVGA, 128 MiB VRAM, 3D disabled and a disposable 30 GiB dynamic VDI. BIOS was used at 2 GiB; EFI at 3 and 4 GiB.

| Guest RAM | Visible total in UI | Used / available at capture | Automatic profile | Result |
|---:|---:|---:|---|---|
| 2 GiB | 1,974 MiB | 508 / 1,466 MiB | Lightweight | UI displayed VirtualBox software rendering; manual Balanced, Ultra, individual effect toggle, and return to Automatic were exercised. |
| 3 GiB | 2,961 MiB | 594 / 2,391 MiB | Lightweight | XFCE booted in EFI mode; blur and desktop-transition controls were unavailable. |
| 4 GiB | 3,903 MiB | 638 / 3,265 MiB | Lightweight | XFCE booted in EFI mode; no accelerated OpenGL path was detected. |

These are screenshots of a live settings window, with foreground apps open. They are not five-minute idle measurements and do not measure host paging. The separate Phase 2 ISO's five-minute 2 GiB sample (520 MiB used, including the terminal) is not a Phase 2.5 benchmark. No three-run median or target-host result exists yet.

Evidence and VM files: `dist/vb-validation-phase25/AETHER-P25-QA-20261112T101639Z/`; the 4 GiB settings capture is `performance-profile-4g.png`.

## Remaining validation

- Stress test sustained CPU, memory pressure, GPU-utilization availability and cooldown/recovery using safe user-space loads in a disposable VM.
- Recheck manual persistence after logging out/in on an installed user account.
- Measure five-minute idle memory after clean boots at 2 and 3 GiB, repeat each at least three times, and distinguish guest use from host paging.
- Test with a real accelerated Intel/AMD/NVIDIA device and compare compositor fallback behavior.
- Keep FPS, animated desktop transitions, Plank bounce, GPU utilization and blur explicitly unavailable unless the selected driver/tool exposes and passes them.
