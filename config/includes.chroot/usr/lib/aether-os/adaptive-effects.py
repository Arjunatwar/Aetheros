#!/usr/bin/python3
"""Low-overhead XFCE visual profile controller for AETHER OS."""

from __future__ import annotations

import fcntl
import json
import os
import re
import signal
import shutil
import subprocess
import threading
import time
from pathlib import Path


POLL_SECONDS = 10
RECOVERY_SAMPLES = 12
PROFILE_ORDER = ("lightweight", "balanced", "ultra")
EFFECT_KEYS = (
    "blur",
    "transparency",
    "shadows",
    "dock_animations",
    "window_animations",
    "desktop_transitions",
    "notification_animations",
)
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aether-os"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "aether-os"
PREFERENCES = CONFIG_DIR / "visual-effects.json"
STATUS_FILE = CACHE_DIR / "effects-status.json"
PID_FILE = CACHE_DIR / "effects.pid"
PICOM_CONFIG = CONFIG_DIR / "picom.conf"
WAKE = threading.Event()
RUNNING = True


def read_json(path: Path, fallback: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else fallback.copy()
    except (OSError, json.JSONDecodeError):
        return fallback.copy()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
        key, _, raw = line.partition(":")
        match = re.search(r"\d+", raw)
        if match:
            values[key] = int(match.group())
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    return {
        "total_kib": total,
        "available_kib": available,
        "used_kib": max(0, total - available),
    }


def read_cpu_times() -> tuple[int, int]:
    first = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0].split()
    counters = [int(item) for item in first[1:]]
    idle = counters[3] + (counters[4] if len(counters) > 4 else 0)
    return sum(counters), idle


def cpu_usage(previous: tuple[int, int] | None, current: tuple[int, int]) -> float | None:
    if previous is None:
        return None
    total_delta = current[0] - previous[0]
    idle_delta = current[1] - previous[1]
    if total_delta <= 0:
        return None
    return round(max(0.0, min(100.0, 100.0 * (total_delta - idle_delta) / total_delta)), 1)


def gpu_information() -> dict:
    models: list[str] = []
    busy_values: list[int] = []
    for device in sorted(Path("/sys/class/drm").glob("card[0-9]*/device")):
        try:
            vendor = (device / "vendor").read_text(encoding="ascii").strip().lower()
            pci_device = (device / "device").read_text(encoding="ascii").strip()
        except OSError:
            continue
        vendors = {
            "0x8086": "Intel graphics",
            "0x1002": "AMD graphics",
            "0x10de": "NVIDIA graphics",
            "0x15ad": "VMware-compatible graphics",
        }
        models.append(vendors.get(vendor, f"GPU {vendor}:{pci_device}"))
        try:
            busy = int((device / "gpu_busy_percent").read_text(encoding="ascii").strip())
            busy_values.append(max(0, min(100, busy)))
        except (OSError, ValueError):
            pass
    if not models and shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1, check=False,
            )
            for line in result.stdout.splitlines():
                model, _, raw_busy = line.partition(",")
                models.append(model.strip())
                if raw_busy.strip().isdigit():
                    busy_values.append(int(raw_busy.strip()))
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {"available": bool(models), "models": models, "utilization_percent": max(busy_values) if busy_values else None}


def graphics_information() -> dict:
    renderer = "unavailable"
    accelerated = False
    if shutil.which("glxinfo") and os.environ.get("DISPLAY"):
        try:
            result = subprocess.run(
                ["glxinfo", "-B"], capture_output=True, text=True, timeout=4, check=False,
            )
            output = result.stdout + result.stderr
            direct = re.search(r"direct rendering:\s*(Yes|No)", output, re.IGNORECASE)
            renderer_match = re.search(r"OpenGL renderer string:\s*(.+)", output, re.IGNORECASE)
            if renderer_match:
                renderer = renderer_match.group(1).strip()
            software = any(word in renderer.lower() for word in ("llvmpipe", "softpipe", "swrast", "software rasterizer"))
            accelerated = bool(direct and direct.group(1).lower() == "yes" and not software)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {"accelerated": accelerated, "renderer": renderer}


def display_refresh_rate() -> float | None:
    if not shutil.which("xrandr") or not os.environ.get("DISPLAY"):
        return None
    try:
        result = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=2, check=False)
        for line in result.stdout.splitlines():
            if "*" in line:
                match = re.search(r"([0-9]+(?:\.[0-9]+)?)\*", line)
                if match:
                    return float(match.group(1))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def collect_metrics(previous_cpu: tuple[int, int] | None, graphics: dict) -> tuple[dict, tuple[int, int]]:
    memory = read_meminfo()
    current_cpu = read_cpu_times()
    try:
        load = list(os.getloadavg())
    except OSError:
        load = []
    metrics = {
        "total_ram_mib": round(memory["total_kib"] / 1024),
        "available_ram_mib": round(memory["available_kib"] / 1024),
        "used_ram_mib": round(memory["used_kib"] / 1024),
        "cpu_percent": cpu_usage(previous_cpu, current_cpu),
        "cpu_cores": os.cpu_count() or 1,
        "system_load_1m": round(load[0], 2) if load else None,
        "gpu": gpu_information(),
        "graphics": graphics,
        "display_refresh_hz": display_refresh_rate(),
        # Xfwm4 does not expose rendered-frame counters. Do not substitute the
        # monitor refresh rate for measured application frame rate.
        "frame_rate_fps": None,
    }
    return metrics, current_cpu


def recommend_profile(metrics: dict) -> tuple[str, str]:
    total_gib = metrics["total_ram_mib"] / 1024.0
    cores = metrics["cpu_cores"]
    accelerated = metrics["graphics"]["accelerated"]
    if total_gib < 3.6 or cores < 2:
        return "lightweight", "The memory or CPU budget is in the low-end range."
    if total_gib < 7.5:
        if not accelerated:
            return "lightweight", "This 4–8 GiB system has no detected hardware-accelerated OpenGL path."
        return "balanced", "The system is in the 4–8 GiB range and graphics acceleration is available."
    if total_gib < 15.5:
        return "balanced", "The system is in the 8–16 GiB balanced range."
    if accelerated and cores >= 4:
        return "ultra", "Memory, CPU cores, and graphics acceleration meet the Ultra starting point."
    return "balanced", "Ultra is deferred because CPU cores or graphics acceleration are limited."


def xfconf_set(channel: str, prop: str, value: str, kind: str) -> bool:
    command = ["xfconf-query", "-c", channel, "-p", prop, "--set", value]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
        if result.returncode == 0:
            return True
        command = ["xfconf-query", "-c", channel, "-p", prop, "--create", "--type", kind, "--set", value]
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def gsettings_set(key: str, value: str) -> bool:
    schema = "net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/"
    try:
        result = subprocess.run(["gsettings", "set", schema, key, value], capture_output=True, text=True, timeout=2, check=False)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def defaults_for(profile: str, metrics: dict) -> dict[str, bool]:
    accelerated = metrics["graphics"]["accelerated"]
    if profile == "lightweight":
        return {
            "blur": False, "transparency": False, "shadows": False,
            "dock_animations": False, "window_animations": False,
            "desktop_transitions": False, "notification_animations": False,
        }
    if profile == "balanced":
        return {
            "blur": accelerated and metrics["total_ram_mib"] >= 8192,
            "transparency": True, "shadows": True,
            "dock_animations": True, "window_animations": True,
            "desktop_transitions": False, "notification_animations": True,
        }
    return {
        "blur": accelerated, "transparency": True, "shadows": True,
        "dock_animations": True, "window_animations": True,
        "desktop_transitions": False, "notification_animations": True,
    }


def resolved_effects(profile: str, preferences: dict, metrics: dict) -> dict[str, bool]:
    effects = defaults_for(profile, metrics)
    overrides = preferences.get("effects", {})
    for key in EFFECT_KEYS:
        value = overrides.get(key)
        if isinstance(value, bool):
            effects[key] = value
    effects["desktop_transitions"] = False
    if not metrics["graphics"]["accelerated"]:
        effects["blur"] = False
    return effects


def stop_compositor(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=1)


def write_picom_config(effects: dict[str, bool], blur: bool) -> str:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        'shadow = ' + ("true" if effects["shadows"] else "false") + ';',
        'shadow-radius = 10;',
        'shadow-opacity = 0.28;',
        'shadow-offset-x = -7;',
        'shadow-offset-y = -5;',
        'fading = ' + ("true" if effects["window_animations"] else "false") + ';',
        'fade-in-step = 0.08;',
        'fade-out-step = 0.08;',
        'inactive-opacity = ' + ("0.96" if effects["transparency"] else "1.0") + ';',
        'inactive-opacity-override = false;',
        'vsync = false;',
        'detect-client-opacity = true;',
        'corner-radius = 16;',
        'round-borders = 1;',
        'rounded-corners-exclude = [ "window_type = \'dock\'", "window_type = \'desktop\'" ];',
        'wintypes : { tooltip : { fade = false; shadow = false; }; };',
    ]
    if blur:
        lines.extend([
            'blur-method = "dual_kawase";',
            'blur-strength = 6;',
            'blur-background = true;',
        ])
    PICOM_CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "glx" if blur else "xrender"


def apply_profile(profile: str, preferences: dict, metrics: dict, current_child: subprocess.Popen | None) -> tuple[subprocess.Popen | None, dict, str]:
    effects = resolved_effects(profile, preferences, metrics)
    gsettings_set("zoom-enabled", "true" if effects["dock_animations"] else "false")
    gsettings_set("zoom-percent", str(165 if profile == "ultra" else 132))
    gsettings_set("icon-size", str(46 if profile == "ultra" else 42 if profile == "balanced" else 38))
    xfconf_set("xfce4-notifyd", "/do-fadeout", "true" if effects["notification_animations"] else "false", "bool")
    xfconf_set("xfwm4", "/general/show_frame_shadow", "false", "bool")
    xfconf_set("xfwm4", "/general/show_popup_shadow", "false", "bool")
    xfconf_set("xfwm4", "/general/show_dock_shadow", "false", "bool")

    requested_compositor = any(effects[key] for key in ("shadows", "transparency", "window_animations", "blur"))
    if not requested_compositor:
        stop_compositor(current_child)
        xfconf_set("xfwm4", "/general/use_compositing", "false", "bool")
        return None, effects, "Xfwm compositing and external effects are off."

    blur_enabled = effects["blur"] and metrics["graphics"]["accelerated"]
    backend = write_picom_config(effects, blur_enabled)
    stop_compositor(current_child)
    xfconf_set("xfwm4", "/general/use_compositing", "false", "bool")
    if shutil.which("picom"):
        try:
            child = subprocess.Popen(
                ["picom", "--config", str(PICOM_CONFIG), "--backend", backend],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(0.45)
            if child.poll() is None:
                reason = "AETHER is using the " + backend + " compositor."
                if effects["blur"] and not blur_enabled:
                    reason += " Blur is off because hardware acceleration is unavailable."
                return child, effects, reason
        except OSError:
            pass

    xfconf_set("xfwm4", "/general/use_compositing", "true", "bool")
    for prop in ("/general/show_frame_shadow", "/general/show_popup_shadow", "/general/show_dock_shadow"):
        xfconf_set("xfwm4", prop, "true" if effects["shadows"] else "false", "bool")
    reason = "Picom could not start; using XFWM's built-in compositor fallback."
    return None, effects, reason


def acquire_lock():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = CACHE_DIR / "effects.lock"
    handle = lock_path.open("w", encoding="ascii")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return None
    handle.write(str(os.getpid()))
    handle.flush()
    PID_FILE.write_text(str(os.getpid()), encoding="ascii")
    return handle


def main() -> int:
    global RUNNING
    lock_handle = acquire_lock()
    if lock_handle is None:
        return 0

    def stop(_signum, _frame):
        global RUNNING
        RUNNING = False
        WAKE.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGUSR1, lambda _signum, _frame: WAKE.set())
    child: subprocess.Popen | None = None
    previous_cpu = None
    graphics = graphics_information()
    base_metrics = {
        "total_ram_mib": round(read_meminfo()["total_kib"] / 1024),
        "cpu_cores": os.cpu_count() or 1,
        "graphics": graphics,
    }
    auto_profile, auto_reason = recommend_profile(base_metrics)
    high_load_samples = 0
    recovery_samples = 0
    last_profile_change = 0.0
    last_applied: tuple | None = None

    while RUNNING:
        WAKE.wait(POLL_SECONDS)
        WAKE.clear()
        try:
            metrics, previous_cpu = collect_metrics(previous_cpu, graphics)
        except (OSError, IndexError, ValueError):
            continue
        preferences = read_json(PREFERENCES, {"version": 1, "mode": "automatic", "effects": {}})
        mode = preferences.get("mode", "automatic")
        if mode not in ("automatic", *PROFILE_ORDER):
            mode = "automatic"

        now = time.monotonic()
        cores = max(1, metrics["cpu_cores"])
        available = metrics["available_ram_mib"]
        total = metrics["total_ram_mib"]
        low_memory = available < max(512, int(total * 0.12))
        high_cpu = metrics["cpu_percent"] is not None and metrics["cpu_percent"] >= 86
        load = metrics["system_load_1m"] or 0.0
        high_load_samples = high_load_samples + 1 if high_cpu and load >= cores * 1.15 else 0
        gpu_busy = metrics["gpu"]["utilization_percent"]
        gpu_pressure = gpu_busy is not None and gpu_busy >= 92 and high_cpu

        if mode == "automatic":
            if (low_memory or high_load_samples >= 3 or gpu_pressure) and now - last_profile_change >= 60:
                index = PROFILE_ORDER.index(auto_profile)
                if index > 0:
                    auto_profile = PROFILE_ORDER[index - 1]
                    auto_reason = "Effects were reduced after sustained memory, CPU, or GPU pressure."
                    last_profile_change = now
                recovery_samples = 0
            elif not low_memory and not high_cpu and load < cores * 0.65 and available > max(1024, int(total * 0.28)):
                recovery_samples += 1
                if recovery_samples >= RECOVERY_SAMPLES and now - last_profile_change >= 90:
                    recommended, reason = recommend_profile(metrics)
                    index = PROFILE_ORDER.index(auto_profile)
                    recommended_index = PROFILE_ORDER.index(recommended)
                    if index < recommended_index:
                        auto_profile = PROFILE_ORDER[index + 1]
                        auto_reason = "Resources stayed healthy; one visual step was restored after cooldown."
                        last_profile_change = now
                    recovery_samples = 0
            else:
                recovery_samples = 0
            selected_profile = auto_profile
            selection_reason = auto_reason
        else:
            selected_profile = mode
            selection_reason = "Manual profile selected; automatic profile changes are paused."

        desired_effects = resolved_effects(selected_profile, preferences, metrics)
        signature = (selected_profile, tuple(sorted(desired_effects.items())))
        effect_reason = "Profile unchanged."
        if signature != last_applied or (child is not None and child.poll() is not None):
            child, _effects, effect_reason = apply_profile(selected_profile, preferences, metrics, child)
            last_applied = signature

        status = {
            "timestamp": time.time(),
            "mode": mode,
            "selected_profile": selected_profile,
            "automatic_recommendation": recommend_profile(metrics)[0],
            "selection_reason": selection_reason,
            "effect_reason": effect_reason,
            "metrics": metrics,
            "effects": desired_effects,
            "effect_support": {
                "blur": metrics["graphics"]["accelerated"],
                "transparency": True,
                "shadows": True,
                "dock_animations": shutil.which("plank") is not None,
                "window_animations": shutil.which("picom") is not None,
                "desktop_transitions": False,
                "notification_animations": shutil.which("xfconf-query") is not None,
            },
            "effect_limits": {
                "blur": "Requires an accelerated OpenGL compositor.",
                "desktop_transitions": "XFWM4 does not provide animated virtual-desktop transitions.",
                "frame_rate_fps": "XFWM4 does not expose rendered-frame counters.",
                "dock_bounce": "Plank provides zoom/magnification; launch bounce is not exposed by its Debian settings schema.",
            },
        }
        try:
            write_json(STATUS_FILE, status)
        except OSError:
            pass
        if last_applied != signature:
            last_applied = signature

    stop_compositor(child)
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    lock_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
