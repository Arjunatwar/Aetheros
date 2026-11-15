#!/usr/bin/env python3
"""
AETHER OS Installer — Error Handling Service
Structured exception hierarchy and recovery guidance for installation stages.
"""

from __future__ import annotations

from typing import Optional


class InstallerError(Exception):
    """Base exception for all installer-related failures."""

    def __init__(self, message: str, stage: str = "general", recovery_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.recovery_hint = recovery_hint or "Check the system logs for additional diagnostic details."

    def formatted_details(self) -> str:
        text = f"Stage: {self.stage}\nError: {self.message}"
        if self.recovery_hint:
            text += f"\n\nSuggested Action: {self.recovery_hint}"
        return text


class HardwareRequirementError(InstallerError):
    """Raised when critical hardware minimums are not satisfied."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage="requirements",
            recovery_hint=recovery_hint or "Verify your system meets the 64-bit x86_64, 2 GB RAM, and 20 GB disk requirements."
        )


class DiskOperationError(InstallerError):
    """Raised when disk discovery, validation, or partition manipulation fails."""

    def __init__(self, message: str, stage: str = "disk", recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage=stage,
            recovery_hint=recovery_hint or "Ensure the target storage disk is not locked, corrupted, or mounted read-only."
        )


class FilesystemFormatError(InstallerError):
    """Raised when formatting FAT32 or ext4 filesystems fails."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage="formatting",
            recovery_hint=recovery_hint or "Check disk health and verify partition boundaries before retrying."
        )


class DeploymentError(InstallerError):
    """Raised when copying system files or kernel fails."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage="deploy",
            recovery_hint=recovery_hint or "Ensure the live installation media is intact and has not been removed."
        )


class BootloaderError(InstallerError):
    """Raised when UEFI boot entry or bootloader installation fails."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage="bootloader",
            recovery_hint=recovery_hint or "Verify that UEFI mode is enabled and NVRAM variables are writable."
        )


class VerificationError(InstallerError):
    """Raised when post-installation sanity verification fails."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=message,
            stage="verification",
            recovery_hint=recovery_hint or "The installation could not be verified. Do not restart into the target drive yet."
        )
