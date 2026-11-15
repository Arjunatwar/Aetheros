#!/usr/bin/env python3
"""
Unit tests for AETHER OS Disk Detection Subsystem
"""

import unittest
from installer.core.disk_detection import DiskInfo, PartitionInfo, enumerate_disks


class TestDiskDetection(unittest.TestCase):
    def test_disk_info_properties(self):
        disk = DiskInfo(
            name="nvme0n1",
            path="/dev/nvme0n1",
            model="Samsung SSD 980",
            size_bytes=500107862016,
            size_gib=465.8,
            is_rotational=False,
            transport="nvme",
            partition_table="gpt",
            is_live_media=False,
        )
        self.assertIn("Samsung SSD 980", disk.display_name)
        self.assertIn("465.8 GiB", disk.display_name)
        self.assertFalse(disk.is_live_media)

    def test_partition_esp_detection(self):
        p_esp = PartitionInfo(
            name="sda1",
            path="/dev/sda1",
            size_bytes=536870912,
            size_gib=0.5,
            fstype="vfat",
            label="EFI",
            is_esp=True,
        )
        self.assertTrue(p_esp.is_esp)
        self.assertEqual(p_esp.fstype, "vfat")

    def test_enumerate_disks_runs(self):
        disks = enumerate_disks()
        self.assertIsInstance(disks, list)


if __name__ == "__main__":
    unittest.main()
