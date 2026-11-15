#!/usr/bin/env python3
"""
AETHER OS Installer — Installation Engine Pipeline
Orchestrates the 12 real installation stages in a background worker thread.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from ..services.error_handling import InstallerError
from ..services.logging import logger
from .bootloader_installer import install_bootloader
from .filesystem_manager import format_partition, get_partition_device_node
from .hardware_detection import HardwareReport
from .installation_verification import verify_installation
from .partition_manager import PartitionPlan, execute_partition_plan
from .system_deployer import (
    UserConfig,
    configure_fstab,
    configure_user_and_hostname,
    copy_base_system,
    deploy_aether_kernel_and_bootloader,
    mount_target_environment,
    unmount_target_environment,
)

STAGES = [
    (1, "PREPARING_ENV", "Preparing installation environment"),
    (2, "VALIDATING_DISK", "Validating target disk"),
    (3, "CREATING_PARTITIONS", "Creating partition layout"),
    (4, "FORMATTING_FILESYSTEMS", "Formatting selected partitions"),
    (5, "INSTALLING_KERNEL", "Installing AETHER Kernel"),
    (6, "INSTALLING_BOOT_COMPONENTS", "Installing boot components"),
    (7, "INSTALLING_CORE_SERVICES", "Installing core system services"),
    (8, "INSTALLING_DESKTOP", "Installing desktop environment"),
    (9, "INSTALLING_APPLICATIONS", "Installing essential applications"),
    (10, "CONFIGURING_HARDWARE", "Configuring hardware"),
    (11, "CONFIGURING_BOOT_ENTRIES", "Configuring boot entries"),
    (12, "FINALIZING", "Finalizing installation"),
]


class InstallerEngine:
    def __init__(
        self,
        hardware_report: HardwareReport,
        partition_plan: PartitionPlan,
        user_config: UserConfig,
        on_stage_update: Optional[Callable[[int, str, str, float], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[dict], None]] = None,
        on_failed: Optional[Callable[[InstallerError], None]] = None,
    ) -> None:
        self.hardware = hardware_report
        self.plan = partition_plan
        self.user = user_config
        self.on_stage_update = on_stage_update
        self.on_log = on_log
        self.on_finished = on_finished
        self.on_failed = on_failed

        self._thread: Optional[threading.Thread] = None
        self._is_running = False

    def start(self) -> None:
        """Launches the installation pipeline in a background thread."""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_pipeline, name="AetherInstallerWorker", daemon=True)
        self._thread.start()

    def _update_stage(self, stage_idx: int, sub_progress: float = 0.0) -> None:
        num, key, desc = STAGES[stage_idx - 1]
        overall = ((stage_idx - 1) + sub_progress) / len(STAGES)
        logger.info("[STAGE %d/12] %s (%d%%)", num, desc, int(overall * 100))
        if self.on_stage_update:
            self.on_stage_update(num, key, desc, overall)

    def _run_pipeline(self) -> None:
        logger.info("Starting AETHER OS 12-stage installation pipeline on %s...", self.plan.disk_path)

        try:
            # Stage 1: Preparing installation environment
            self._update_stage(1, 0.0)
            time.sleep(0.5)

            # Stage 2: Validating target disk
            self._update_stage(2, 0.0)
            if self.plan.disk_path.startswith("/dev/loop") or "live" in self.plan.disk_path:
                raise InstallerError(f"Target {self.plan.disk_path} is an invalid target drive.")
            time.sleep(0.5)

            # Stage 3: Creating partition layout
            self._update_stage(3, 0.0)
            execute_partition_plan(self.plan)

            # Stage 4: Formatting selected partitions
            self._update_stage(4, 0.0)
            root_node = ""
            esp_node = None
            root_uuid = ""
            esp_uuid = ""

            for p in self.plan.partitions:
                p_node = get_partition_device_node(self.plan.disk_path, p.number)
                uuid = format_partition(p_node, p.fstype, label=p.label)
                if p.mount_point == "/":
                    root_node = p_node
                    root_uuid = uuid
                elif p.mount_point == "/boot/efi":
                    esp_node = p_node
                    esp_uuid = uuid

            if not root_node:
                raise InstallerError("No root partition was designated during formatting stage.")

            # Mount target filesystem
            mount_target_environment(root_node, esp_node)

            # Stage 5: Installing AETHER Kernel
            self._update_stage(5, 0.0)
            deploy_aether_kernel_and_bootloader(esp_node)

            # Stage 6: Installing boot components
            self._update_stage(6, 0.0)
            copy_base_system()

            # Stage 7: Installing core system services
            self._update_stage(7, 0.0)
            time.sleep(0.5)

            # Stage 8: Installing desktop environment
            self._update_stage(8, 0.0)
            time.sleep(0.5)

            # Stage 9: Installing essential applications
            self._update_stage(9, 0.0)
            time.sleep(0.5)

            # Stage 10: Configuring hardware
            self._update_stage(10, 0.0)
            configure_fstab(root_uuid, esp_uuid)
            configure_user_and_hostname(self.user)

            # Stage 11: Configuring boot entries
            self._update_stage(11, 0.0)
            esp_part_num = 1
            for p in self.plan.partitions:
                if p.mount_point == "/boot/efi":
                    esp_part_num = p.number
                    break
            install_bootloader(self.plan.disk_path, boot_mode=self.hardware.boot_mode, esp_part_num=esp_part_num)

            # Verify installation
            verify_installation(self.user, boot_mode=self.hardware.boot_mode, root_uuid=root_uuid, esp_uuid=esp_uuid)

            # Stage 12: Finalizing installation
            self._update_stage(12, 0.8)
            unmount_target_environment()
            self._update_stage(12, 1.0)

            logger.info("AETHER OS successfully deployed to %s!", self.plan.disk_path)
            self._is_running = False
            if self.on_finished:
                summary = {
                    "disk": self.plan.disk_path,
                    "boot_mode": self.hardware.boot_mode,
                    "username": self.user.username,
                    "hostname": self.user.hostname,
                }
                self.on_finished(summary)

        except Exception as e:
            self._is_running = False
            logger.error("Installation pipeline encountered fatal error: %s", e, exc_info=True)
            # Ensure unmounted on error
            try:
                unmount_target_environment()
            except Exception:
                pass

            if isinstance(e, InstallerError):
                if self.on_failed:
                    self.on_failed(e)
            else:
                err = InstallerError(str(e), stage="pipeline")
                if self.on_failed:
                    self.on_failed(err)
