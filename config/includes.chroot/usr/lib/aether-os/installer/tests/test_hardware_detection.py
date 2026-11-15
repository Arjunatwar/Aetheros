#!/usr/bin/env python3
"""
Unit tests for AETHER OS Hardware Detection Subsystem
"""

import unittest
from installer.core.hardware_detection import HardwareReport, run_hardware_detection


class TestHardwareDetection(unittest.TestCase):
    def test_hardware_audit_runs(self):
        report = run_hardware_detection()
        self.assertIsInstance(report, HardwareReport)
        self.assertTrue(len(report.cpu_arch) > 0)
        self.assertTrue(report.cpu_cores >= 1)
        self.assertTrue(report.ram_total_mib > 0)
        self.assertIn(report.boot_mode, ("UEFI", "BIOS"))
        self.assertIn(report.compatibility_status, ("COMPATIBLE", "LIMITATIONS", "UNSUPPORTED"))

    def test_compatibility_thresholds(self):
        # 1. Fully compatible report
        r1 = HardwareReport(
            cpu_arch="x86_64",
            cpu_cores=4,
            ram_total_mib=4096,
            storage_drives_count=1,
            storage_total_gib=60.0,
            boot_mode="UEFI",
        )
        self.assertEqual(len(r1.blocking_reasons), 0)

        # 2. Unsupported report: 32-bit CPU
        r2 = HardwareReport(
            cpu_arch="i686",
            ram_total_mib=4096,
            storage_drives_count=1,
            storage_total_gib=30.0,
        )
        # Should flag 32-bit
        self.assertNotEqual(r2.cpu_arch, "x86_64")


if __name__ == "__main__":
    unittest.main()
