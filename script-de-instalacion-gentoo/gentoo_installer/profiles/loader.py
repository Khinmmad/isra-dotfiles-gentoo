#!/usr/bin/env python3
"""
Gentoo Installer — Profile Loader
Load and validate YAML profiles
"""

import yaml
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")

DEFAULT_PROFILE = {
    "hostname": "gentoo",
    "init_system": "openrc",
    "timezone": "UTC",
    "locale": "en_US.UTF-8",
    "keymap": "us",
    "root_password": "",
    "users": [],
    "network": {
        "type": "dhcp",
        "iface": "",
    },
    "partitions": [],
    "bootloader": "grub",
    "kernel": {
        "type": "gentoo-sources",
        "config": "genkernel",
    },
    "desktop": "none",
    "drivers": "auto",
    "packages": [],
}


def load_profile(path: str) -> dict:
    """
    Load a YAML profile file
    Returns merged profile with defaults
    """
    profile_path = Path(path)

    if not profile_path.exists():
        logger.error(f"Profile not found: {path}")
        raise FileNotFoundError(f"Profile not found: {path}")

    try:
        with open(profile_path) as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty profile: {path}")
            return DEFAULT_PROFILE.copy()

        # Merge with defaults
        profile = merge_profiles(DEFAULT_PROFILE, data)
        logger.info(f"Profile loaded: {path}")
        return profile

    except yaml.YAMLError as e:
        logger.error(f"Error parsing profile: {e}")
        raise


def merge_profiles(default: dict, override: dict) -> dict:
    """Deep merge two profile dicts"""
    result = default.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_profiles(result[key], value)
        else:
            result[key] = value

    return result


def discover_profiles(profile_dir: str) -> list[dict]:
    """Discover all YAML profiles in a directory"""
    profiles = []
    p = Path(profile_dir)

    if not p.exists():
        return profiles

    for f in sorted(p.glob("*.yaml")):
        try:
            profile = load_profile(str(f))
            profile["_name"] = f.stem
            profile["_path"] = str(f)
            profiles.append(profile)
        except Exception as e:
            logger.warning(f"Skipping {f}: {e}")

    return profiles


def save_profile(path: str, profile: dict) -> bool:
    """Save current configuration as a YAML profile"""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "w") as f:
            yaml.dump(profile, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Profile saved: {path}")
        return True

    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        return False
