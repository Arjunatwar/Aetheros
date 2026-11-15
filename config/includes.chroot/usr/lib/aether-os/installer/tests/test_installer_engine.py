#!/usr/bin/env python3
"""
Unit tests for AETHER OS Installer Engine Pipeline
"""

import unittest
from installer.core.hardware_detection import HardwareReport
from installer.core.installer_engine import InstallerEngine, STAGES
from installer.core.partition_manager import PartitionPlan, PlannedPartition
from installer.core.system_deployer import UserConfig


class TestInstallerEngine(unittest.TestCase):
    def test_stages_definition(self):
        self.assertEqual(len(STAGES), 12)
        stage_nums = [s[0] for s in STAGES]
        self.assertEqual(stage_nums, list(range(1, 13)))

        # Verify key stage names match specifications
        self.assertEqual(STAGES[0][1], "PREPARING_ENV")
        self.assertEqual(STAGES[4][1], "INSTALLING_KERNEL")
        self.assertEqual(STAGES[11][1], "FINALIZING")

    def test_engine_initialization(self):
        hw = HardwareReport(cpu_arch="x86_64", ram_total_mib=4096)
        plan = PartitionPlan(
            disk_path="/dev/sda",
            table_type="gpt",
            partitions=[
                PlannedPartition(1, "ESP", 1, 512, "vfat", "/boot/efi"),
                PlannedPartition(2, "ROOT", 513, 20000, "ext4", "/"),
            ]
        )
        user = UserConfig("alex", "Alex Mercer", "password123", "aether-pc", autologin=True)

        engine = InstallerEngine(hw, plan, user)
        self.assertFalse(engine._is_running)
        self.assertEqual(engine.plan.disk_path, "/dev/sda")
        self.assertEqual(engine.user.username, "alex")


if __name__ == "__main__":
    unittest.main()
