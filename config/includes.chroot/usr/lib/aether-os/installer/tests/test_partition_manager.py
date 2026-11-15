#!/usr/bin/env python3
"""
Unit tests for AETHER OS Partition Manager Subsystem
"""

import unittest
from installer.core.disk_detection import DiskInfo
from installer.core.partition_manager import (
    create_erase_disk_plan,
    validate_manual_plan,
    PartitionPlan,
    PlannedPartition,
)
from installer.services.error_handling import DiskOperationError


class TestPartitionManager(unittest.TestCase):
    def setUp(self):
        self.mock_disk = DiskInfo(
            name="sda",
            path="/dev/sda",
            model="VBOX HARDDISK",
            size_bytes=32212254720,  # 30 GiB
            size_gib=30.0,
            is_rotational=False,
            transport="sata",
            partition_table="gpt",
            is_live_media=False,
        )

    def test_create_erase_disk_plan(self):
        plan = create_erase_disk_plan(self.mock_disk, boot_mode="UEFI")
        self.assertEqual(plan.disk_path, "/dev/sda")
        self.assertEqual(plan.table_type, "gpt")
        self.assertTrue(plan.is_destructive_wipe)
        self.assertEqual(len(plan.partitions), 2)

        # First partition should be ESP (512 MiB)
        p1 = plan.partitions[0]
        self.assertEqual(p1.number, 1)
        self.assertEqual(p1.size_mib, 512)
        self.assertEqual(p1.mount_point, "/boot/efi")
        self.assertEqual(p1.fstype, "vfat")
        self.assertIn("esp", p1.flags)

        # Second partition should be Root
        p2 = plan.partitions[1]
        self.assertEqual(p2.number, 2)
        self.assertTrue(p2.size_mib > 25000)
        self.assertEqual(p2.mount_point, "/")
        self.assertEqual(p2.fstype, "ext4")

    def test_refuse_erase_live_media(self):
        live_disk = DiskInfo(
            name="sdb",
            path="/dev/sdb",
            model="SanDisk Ultra USB",
            size_bytes=16000000000,
            size_gib=15.0,
            is_rotational=False,
            transport="usb",
            partition_table="gpt",
            is_live_media=True,
        )
        with self.assertRaises(DiskOperationError):
            create_erase_disk_plan(live_disk)

    def test_validate_manual_plan(self):
        # Valid plan
        valid_plan = PartitionPlan(
            disk_path="/dev/sda",
            table_type="gpt",
            partitions=[
                PlannedPartition(1, "ESP", 1, 512, "vfat", "/boot/efi", ["esp"]),
                PlannedPartition(2, "ROOT", 513, 25000, "ext4", "/"),
            ]
        )
        errors = validate_manual_plan(valid_plan, boot_mode="UEFI")
        self.assertEqual(len(errors), 0)

        # Invalid plan: missing root
        no_root = PartitionPlan(
            disk_path="/dev/sda",
            table_type="gpt",
            partitions=[
                PlannedPartition(1, "ESP", 1, 512, "vfat", "/boot/efi", ["esp"]),
            ]
        )
        errors = validate_manual_plan(no_root, boot_mode="UEFI")
        self.assertTrue(any("root partition" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
