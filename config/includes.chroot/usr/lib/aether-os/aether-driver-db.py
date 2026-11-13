#!/usr/bin/python3
"""
AETHER OS — Hardware Driver Database
Maps PCI vendor/device IDs and class strings to Debian packages.
Used by the Driver Manager UI and the build-time auto-detect hook.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class DriverEntry:
    """One driver record — a hardware match → one or more Debian packages."""
    def __init__(
        self,
        name: str,
        description: str,
        packages: list[str],
        category: str,
        priority: int = 10,
        reboot_required: bool = False,
        kernel_module: str = "",
        post_install_cmd: str = "",
        pci_vendor_ids: list[str] | None = None,
        pci_device_ids: list[str] | None = None,
        pci_class_prefixes: list[str] | None = None,
        name_keywords: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.packages = packages
        self.category = category
        self.priority = priority
        self.reboot_required = reboot_required
        self.kernel_module = kernel_module
        self.post_install_cmd = post_install_cmd
        self.pci_vendor_ids = pci_vendor_ids or []
        self.pci_device_ids = pci_device_ids or []
        self.pci_class_prefixes = pci_class_prefixes or []
        self.name_keywords = name_keywords or []


# ---------------------------------------------------------------------------
# The database
# ---------------------------------------------------------------------------

DRIVER_DB: list[DriverEntry] = [

    # ── VirtualBox Guest Additions ──────────────────────────────────────────
    DriverEntry(
        name="VirtualBox Guest Additions",
        description="VMSVGA display, shared clipboard, shared folders, mouse integration for VirtualBox VMs",
        packages=["xserver-xorg-video-vmware"],
        category="Virtualization",
        priority=100,
        kernel_module="vboxguest",
        reboot_required=True,
        post_install_cmd="modprobe vboxguest vboxsf vboxvideo || true",
        pci_vendor_ids=["80ee"],           # Oracle/InnoTek
        name_keywords=["virtualbox", "vbox", "vmsvga"],
    ),

    # ── NVIDIA GPUs ─────────────────────────────────────────────────────────
    DriverEntry(
        name="NVIDIA Proprietary Driver",
        description="High-performance proprietary driver for NVIDIA GeForce/Quadro/RTX cards",
        packages=["nvidia-driver", "nvidia-driver-libs", "nvidia-settings"],
        category="GPU",
        priority=90,
        kernel_module="nvidia",
        reboot_required=True,
        post_install_cmd="update-initramfs -u || true",
        pci_vendor_ids=["10de"],
        pci_class_prefixes=["03"],
    ),
    DriverEntry(
        name="NVIDIA Open Kernel Module",
        description="NVIDIA open-source kernel module (Turing/Ampere/Ada — RTX 2000+)",
        packages=["nvidia-open-kernel-dkms", "nvidia-driver-libs"],
        category="GPU",
        priority=85,
        kernel_module="nvidia",
        reboot_required=True,
        pci_vendor_ids=["10de"],
        pci_class_prefixes=["03"],
        # Only suggested for newer device IDs — UI can refine further
    ),
    DriverEntry(
        name="Nouveau (NVIDIA open-source)",
        description="Open-source reverse-engineered NVIDIA driver — no CUDA, lower performance",
        packages=["xserver-xorg-video-nouveau"],
        category="GPU",
        priority=30,
        kernel_module="nouveau",
        pci_vendor_ids=["10de"],
        pci_class_prefixes=["03"],
    ),

    # ── AMD / ATI GPUs ──────────────────────────────────────────────────────
    DriverEntry(
        name="AMD AMDGPU (open-source)",
        description="Mainline kernel AMDGPU driver for Radeon RX 400+ and Vega/RDNA cards",
        packages=["firmware-amd-graphics", "xserver-xorg-video-amdgpu"],
        category="GPU",
        priority=80,
        kernel_module="amdgpu",
        pci_vendor_ids=["1002"],
        pci_class_prefixes=["03"],
    ),
    DriverEntry(
        name="AMD Radeon (legacy ATI)",
        description="Open-source radeon driver for older ATI/AMD cards (pre-GCN)",
        packages=["xserver-xorg-video-radeon", "firmware-amd-graphics"],
        category="GPU",
        priority=50,
        kernel_module="radeon",
        pci_vendor_ids=["1002"],
        pci_class_prefixes=["03"],
        name_keywords=["radeon hd", "radeon r", "rs", "rv"],
    ),

    # ── Intel Graphics ───────────────────────────────────────────────────────
    DriverEntry(
        name="Intel i915 Graphics",
        description="Mainline Intel GPU driver for HD/UHD/Iris/Arc graphics",
        packages=["firmware-intel-graphics", "xserver-xorg-video-intel", "intel-media-va-driver"],
        category="GPU",
        priority=80,
        kernel_module="i915",
        pci_vendor_ids=["8086"],
        pci_class_prefixes=["03"],
    ),

    # ── VMware / VMSVGA ──────────────────────────────────────────────────────
    DriverEntry(
        name="VMware SVGA Driver",
        description="X.Org driver for VMware SVGA / VMSVGA virtual GPU",
        packages=["xserver-xorg-video-vmware", "open-vm-tools-desktop"],
        category="GPU",
        priority=90,
        kernel_module="vmwgfx",
        pci_vendor_ids=["15ad"],           # VMware
        pci_class_prefixes=["03"],
    ),

    # ── QEMU / KVM virtio GPU ────────────────────────────────────────────────
    DriverEntry(
        name="virtio-gpu (KVM/QEMU)",
        description="Paravirtualised GPU driver for QEMU/KVM virtual machines",
        packages=["xserver-xorg-video-qxl", "spice-vdagent"],
        category="GPU",
        priority=85,
        kernel_module="virtio_gpu",
        pci_vendor_ids=["1af4", "1b36"],
        pci_class_prefixes=["03"],
        name_keywords=["virtio", "qxl"],
    ),

    # ── WiFi — Intel ─────────────────────────────────────────────────────────
    DriverEntry(
        name="Intel WiFi Firmware (iwlwifi)",
        description="Firmware blobs for Intel Wireless AC/AX/BE adapters",
        packages=["firmware-iwlwifi"],
        category="WiFi",
        priority=80,
        kernel_module="iwlwifi",
        pci_vendor_ids=["8086"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["wireless", "wi-fi", "centrino", "wifi", "ax200", "ax210",
                       "ac 7260", "ac 8260", "ac 9560", "ac 3160"],
    ),

    # ── WiFi — Realtek ───────────────────────────────────────────────────────
    DriverEntry(
        name="Realtek WiFi Firmware",
        description="Firmware for Realtek RTL8xxx USB and PCIe wireless adapters",
        packages=["firmware-realtek"],
        category="WiFi",
        priority=75,
        kernel_module="rtw88_pci",
        pci_vendor_ids=["10ec"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["realtek", "rtl8", "rtw"],
    ),

    # ── WiFi — Atheros / Qualcomm ────────────────────────────────────────────
    DriverEntry(
        name="Atheros / Qualcomm WiFi Firmware",
        description="Firmware for Atheros AR and Qualcomm QCA wireless adapters",
        packages=["firmware-atheros"],
        category="WiFi",
        priority=75,
        kernel_module="ath10k_pci",
        pci_vendor_ids=["168c", "17cb"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["atheros", "qualcomm", "qca", "ar91", "ar93"],
    ),

    # ── WiFi — Broadcom ──────────────────────────────────────────────────────
    DriverEntry(
        name="Broadcom WiFi Firmware (brcmfmac)",
        description="Open-source firmware for Broadcom BCM43xx WiFi chips",
        packages=["firmware-brcm80211"],
        category="WiFi",
        priority=70,
        kernel_module="brcmfmac",
        pci_vendor_ids=["14e4"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["broadcom", "bcm43"],
    ),
    DriverEntry(
        name="Broadcom wl (proprietary)",
        description="Broadcom proprietary STA driver — use only if brcmfmac fails",
        packages=["broadcom-sta-dkms"],
        category="WiFi",
        priority=40,
        kernel_module="wl",
        reboot_required=True,
        pci_vendor_ids=["14e4"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["broadcom", "bcm43"],
    ),

    # ── WiFi — MediaTek ──────────────────────────────────────────────────────
    DriverEntry(
        name="MediaTek WiFi Firmware",
        description="Firmware for MediaTek MT76xx and MT792x WiFi adapters",
        packages=["firmware-misc-nonfree"],
        category="WiFi",
        priority=70,
        kernel_module="mt76",
        pci_vendor_ids=["14c3"],
        pci_class_prefixes=["0280", "0282"],
        name_keywords=["mediatek", "mt76", "mt792"],
    ),

    # ── Audio ────────────────────────────────────────────────────────────────
    DriverEntry(
        name="Intel HDA Audio",
        description="Kernel driver for Intel High Definition Audio (snd_hda_intel)",
        packages=["alsa-firmware-loaders", "firmware-sof-signed"],
        category="Audio",
        priority=80,
        kernel_module="snd_hda_intel",
        pci_vendor_ids=["8086"],
        pci_class_prefixes=["0403"],
        name_keywords=["hda", "audio", "sound", "hdmi audio"],
    ),
    DriverEntry(
        name="AMD HDA Audio",
        description="Kernel driver for AMD High Definition Audio",
        packages=["alsa-firmware-loaders"],
        category="Audio",
        priority=75,
        kernel_module="snd_hda_codec_realtek",
        pci_vendor_ids=["1002", "1022"],
        pci_class_prefixes=["0403"],
    ),
    DriverEntry(
        name="Realtek HD Audio Codec",
        description="ALSA firmware and codecs for Realtek ALC-series audio chips",
        packages=["alsa-firmware-loaders", "firmware-realtek"],
        category="Audio",
        priority=75,
        kernel_module="snd_hda_codec_realtek",
        name_keywords=["realtek", "alc2", "alc8", "alc9"],
    ),

    # ── Ethernet — Realtek ───────────────────────────────────────────────────
    DriverEntry(
        name="Realtek Ethernet Firmware",
        description="Firmware for Realtek RTL8168/8111/8125 Gigabit/2.5G NICs",
        packages=["firmware-realtek"],
        category="Ethernet",
        priority=75,
        kernel_module="r8169",
        pci_vendor_ids=["10ec"],
        pci_class_prefixes=["0200"],
        name_keywords=["realtek", "rtl8168", "rtl8111", "rtl8125"],
    ),

    # ── Ethernet — Intel ────────────────────────────────────────────────────
    DriverEntry(
        name="Intel Ethernet (e1000e / igb / ice)",
        description="Drivers for Intel 1G/10G/25G Ethernet adapters",
        packages=["firmware-misc-nonfree"],
        category="Ethernet",
        priority=75,
        kernel_module="e1000e",
        pci_vendor_ids=["8086"],
        pci_class_prefixes=["0200"],
        name_keywords=["intel", "ethernet", "i219", "i225", "i350", "x550"],
    ),

    # ── Bluetooth ───────────────────────────────────────────────────────────
    DriverEntry(
        name="Intel Bluetooth Firmware",
        description="Firmware for Intel Bluetooth adapters (Bluetooth 4.0–5.4)",
        packages=["firmware-iwlwifi"],
        category="Bluetooth",
        priority=75,
        kernel_module="btintel",
        name_keywords=["intel", "bluetooth"],
    ),
    DriverEntry(
        name="Realtek Bluetooth Firmware",
        description="Firmware for Realtek USB Bluetooth adapters",
        packages=["firmware-realtek"],
        category="Bluetooth",
        priority=70,
        kernel_module="btrtl",
        name_keywords=["realtek", "bluetooth"],
    ),
    DriverEntry(
        name="Qualcomm Bluetooth Firmware",
        description="Firmware for Qualcomm Atheros Bluetooth adapters",
        packages=["firmware-atheros"],
        category="Bluetooth",
        priority=70,
        kernel_module="btqca",
        name_keywords=["qualcomm", "atheros", "bluetooth"],
    ),

    # ── Input ─────────────────────────────────────────────────────────────────
    DriverEntry(
        name="Synaptics Touchpad",
        description="X.Org libinput driver for Synaptics touchpads (included via libinput)",
        packages=["xserver-xorg-input-libinput"],
        category="Input",
        priority=70,
        kernel_module="i2c_hid",
        name_keywords=["synaptics", "touchpad", "trackpad"],
    ),
    DriverEntry(
        name="Wacom Tablet Driver",
        description="Kernel and X.Org drivers for Wacom drawing tablets",
        packages=["input-wacom-dkms", "xserver-xorg-input-wacom"],
        category="Input",
        priority=70,
        kernel_module="wacom",
        pci_vendor_ids=["056a"],           # Wacom
        name_keywords=["wacom"],
    ),

    # ── Printers ────────────────────────────────────────────────────────────
    DriverEntry(
        name="CUPS Print System",
        description="Common UNIX Printing System with drivers for most USB/network printers",
        packages=["cups", "cups-filters", "hplip", "printer-driver-gutenprint"],
        category="Printers",
        priority=60,
        kernel_module="usblp",
        post_install_cmd="systemctl enable --now cups || true",
        name_keywords=["printer", "print", "hp", "canon", "epson", "brother"],
    ),

    # ── Catch-all firmware ───────────────────────────────────────────────────
    DriverEntry(
        name="General Non-free Firmware",
        description="Miscellaneous firmware blobs for less-common hardware",
        packages=["firmware-misc-nonfree"],
        category="Other",
        priority=10,
    ),
]

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _hex(s: str) -> str:
    return s.strip().lower()


def find_drivers_for_device(
    pci_vendor: str = "",
    pci_device: str = "",
    pci_class: str = "",
    name: str = "",
) -> list[DriverEntry]:
    """Return all DriverEntry records that match the given PCI device."""
    vendor  = _hex(pci_vendor)
    device  = _hex(pci_device)
    cls     = _hex(pci_class)
    name_lc = name.lower()

    matches: list[DriverEntry] = []
    for entry in DRIVER_DB:
        matched = False
        # Vendor ID match
        if entry.pci_vendor_ids and vendor in [_hex(v) for v in entry.pci_vendor_ids]:
            matched = True
        # Class prefix match
        if entry.pci_class_prefixes:
            for pfx in entry.pci_class_prefixes:
                if cls.startswith(_hex(pfx)):
                    matched = True
                    break
        # Keyword match in device name
        if entry.name_keywords and not matched:
            for kw in entry.name_keywords:
                if kw.lower() in name_lc:
                    matched = True
                    break
        # Only check device IDs when vendor also matches
        if entry.pci_device_ids and device in [_hex(d) for d in entry.pci_device_ids]:
            matched = True

        if matched:
            matches.append(entry)

    matches.sort(key=lambda e: e.priority, reverse=True)
    return matches


def packages_for_devices(devices: list[dict]) -> set[str]:
    """Return the union of recommended packages for a list of lspci device dicts."""
    pkgs: set[str] = set()
    for dev in devices:
        entries = find_drivers_for_device(
            pci_vendor=dev.get("vendor_id", ""),
            pci_device=dev.get("device_id", ""),
            pci_class=dev.get("class_id", ""),
            name=dev.get("name", ""),
        )
        if entries:
            # Take only the highest-priority entry per category
            seen_cats: set[str] = set()
            for e in entries:
                if e.category not in seen_cats:
                    pkgs.update(e.packages)
                    seen_cats.add(e.category)
    return pkgs
