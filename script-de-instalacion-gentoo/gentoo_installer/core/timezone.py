#!/usr/bin/env python3
"""
Gentoo Installer — Timezone & Locale Module
Timezone, locale, hwclock
"""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("gentoo-installer")


def configure_locale(root: Path, locale: str) -> bool:
    """
    Configure system locale
    locale: e.g., "en_US.UTF-8"
    """
    root = Path(root)
    logger.info(f"Configuring locale: {locale}")

    try:
        # Generate locale
        locale_gen = root / "etc/locale.gen"
        with open(locale_gen, "w") as f:
            f.write(f"{locale} UTF-8\n")
            # Also generate common fallback
            if locale != "en_US.UTF-8":
                f.write("en_US.UTF-8 UTF-8\n")

        # Run locale-gen
        subprocess.run(
            ["chroot", str(root), "locale-gen"],
            check=True, capture_output=True
        )

        # Set default locale
        subprocess.run(
            ["chroot", str(root), "eselect", "locale", "set", "1"],
            check=False, capture_output=True
        )

        # Verify
        result = subprocess.run(
            ["chroot", str(root), "locale"],
            capture_output=True, text=True
        )
        logger.info(f"Locale configured: {result.stdout.strip()}")
        return True

    except Exception as e:
        logger.error(f"Error configuring locale: {e}")
        return False


def configure_timezone(root: Path, timezone: str) -> bool:
    """
    Configure system timezone
    timezone: e.g., "America/Mexico_City"
    """
    root = Path(root)
    tz_path = f"/usr/share/zoneinfo/{timezone}"

    logger.info(f"Configuring timezone: {timezone}")

    try:
        # Check if timezone file exists
        full_tz = root / tz_path.lstrip("/")
        if not full_tz.exists():
            logger.error(f"Timezone {timezone} not found")
            return False

        # Set timezone
        subprocess.run(
            ["chroot", str(root), "ln", "-sf", tz_path, "/etc/localtime"],
            check=True
        )

        # Also set via eselect if available
        subprocess.run(
            ["chroot", str(root), "eselect", "timezone", "set", timezone],
            check=False, capture_output=True
        )

        logger.info(f"Timezone set to {timezone}")
        return True

    except Exception as e:
        logger.error(f"Error configuring timezone: {e}")
        return False


def configure_keymap(root: Path, keymap: str) -> bool:
    """
    Configure console keymap
    keymap: e.g., "es", "us"
    """
    root = Path(root)
    keymap_file = root / "etc/conf.d/keymaps"

    logger.info(f"Configuring keymap: {keymap}")

    try:
        # Map short names to full keymap names
        keymap_map = {
            "es": "es",
            "en": "us",
            "fr": "fr",
            "de": "de",
            "pt": "br-abnt2",
            "it": "it",
            "ja": "jp",
            "zh": "us",
        }
        actual_keymap = keymap_map.get(keymap, keymap)

        # Write keymaps config
        keymap_file.parent.mkdir(parents=True, exist_ok=True)
        with open(keymap_file, "w") as f:
            f.write(f'keymap="{actual_keymap}"\n')
            f.write(f'set_windowkeys="YES"\n')

        logger.info(f"Keymap set to {actual_keymap}")
        return True

    except IOError as e:
        logger.error(f"Error configuring keymap: {e}")
        return False


def configure_hwclock(root: Path, utc: bool = True) -> bool:
    """
    Configure hardware clock
    utc: whether hardware clock is in UTC
    """
    root = Path(root)
    hwclock_file = root / "etc/conf.d/hwclock"

    logger.info(f"Configuring hwclock (UTC={utc})")

    try:
        hwclock_file.parent.mkdir(parents=True, exist_ok=True)
        clock_mode = "UTC" if utc else "local"

        with open(hwclock_file, "w") as f:
            f.write(f'clock="{clock_mode}"\n')

        # Set hardware clock
        subprocess.run(
            ["chroot", str(root), "hwclock", "--systohc"],
            check=False
        )

        logger.info(f"Hardware clock set to {clock_mode}")
        return True

    except Exception as e:
        logger.error(f"Error configuring hwclock: {e}")
        return False


def list_timezones() -> list[str]:
    """List available timezones"""
    tz_dir = Path("/usr/share/zoneinfo")
    timezones = []

    if tz_dir.exists():
        for region in sorted(tz_dir.iterdir()):
            if region.is_dir() and not region.name.startswith("."):
                for tz in sorted(region.iterdir()):
                    if tz.is_file():
                        timezones.append(f"{region.name}/{tz.name}")

    return timezones


def list_locales() -> list[str]:
    """List common locales"""
    return [
        "en_US.UTF-8",
        "en_GB.UTF-8",
        "es_ES.UTF-8",
        "es_MX.UTF-8",
        "es_AR.UTF-8",
        "fr_FR.UTF-8",
        "de_DE.UTF-8",
        "pt_BR.UTF-8",
        "it_IT.UTF-8",
        "ja_JP.UTF-8",
        "zh_CN.UTF-8",
        "ru_RU.UTF-8",
    ]
