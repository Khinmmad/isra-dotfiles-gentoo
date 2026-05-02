#!/usr/bin/env python3
"""
Gentoo Installer — Validation Module
Input validation helpers
"""

import re
from pathlib import Path
from typing import Optional


def validate_hostname(hostname: str) -> bool:
    """Validate hostname format"""
    if not hostname or len(hostname) > 63:
        return False
    return bool(re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", hostname))


def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or len(username) > 32:
        return False
    return bool(re.match(r"^[a-z_][a-z0-9_-]*$", username))


def validate_password(password: str) -> bool:
    """Validate password (min length 6)"""
    return len(password) >= 6


def validate_mount_point(mount: str) -> bool:
    """Validate mount point path"""
    return mount.startswith("/") and not mount.endswith("/")


def validate_partition_device(device: str) -> bool:
    """Validate block device path"""
    return bool(re.match(r"^/dev/(sd[a-z]|nvme[0-9]+n[0-9]+|vd[a-z]|mmcblk[0-9]+)(p[0-9]+)?$", device))


def validate_email(email: str) -> bool:
    """Basic email validation"""
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))


def validate_integer(value: str, min_val: int = 0, max_val: int = 999999) -> Optional[int]:
    """Validate and return integer"""
    try:
        i = int(value)
        if min_val <= i <= max_val:
            return i
    except ValueError:
        pass
    return None
