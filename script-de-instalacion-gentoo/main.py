#!/usr/bin/env python3
"""
Gentoo Installer — Entry Point
Interactive installer for Gentoo Linux
"""

import sys
import logging
import os
from pathlib import Path

# Ensure we can import from the package
sys.path.insert(0, str(Path(__file__).parent))

from gentoo_installer.core import disk
from gentoo_installer.tui import menus
from gentoo_installer.profiles import loader
from gentoo_installer.installer import Installer


def setup_logging(verbose: bool = False) -> None:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main_menu() -> str:
    """Show main menu"""
    options = [
        "Interactive Installation",
        "Install from Profile (YAML)",
        "Disk Partitioning Tool",
        "Save Current Config as Profile",
        "Exit",
    ]
    return menus.select_from_list("Gentoo Installer", options)


def interactive_install() -> dict:
    """Run interactive configuration"""
    config = {}

    menus.display_info(
        "Interactive Installation",
        ["Follow the prompts to configure your Gentoo system."],
    )

    # Hostname
    config["hostname"] = menus.input_with_default("Hostname", "gentoo")

    # Init system
    init = menus.select_from_list("Init System", ["openrc", "systemd"])
    config["init_system"] = init or "openrc"

    # Target disk
    disks = disk.list_disks()
    if disks:
        disk_choice = menus.select_from_list(
            "Target Disk",
            [f"{d['name']} ({d['size']})" for d in disks],
        )
        if disk_choice:
            selected = disk_choice.split()[0]
            config["target_disk"] = selected
            config["efi"] = menus.confirm("Use UEFI/EFI boot?", default=True)
    else:
        config["target_disk"] = menus.input_with_default("Target disk (e.g., /dev/nvme0n1)")

    # Timezone
    timezones = ["UTC", "America/Mexico_City", "America/New_York", "Europe/Madrid", "Asia/Tokyo"]
    config["timezone"] = menus.select_from_list("Timezone", timezones) or "UTC"

    # Locale
    locales = ["en_US.UTF-8", "es_MX.UTF-8", "es_ES.UTF-8", "en_GB.UTF-8"]
    config["locale"] = menus.select_from_list("Locale", locales) or "en_US.UTF-8"

    # Keymap
    keymaps = ["us", "es", "fr", "de", "br-abnt2"]
    config["keymap"] = menus.select_from_list("Keyboard Layout", keymaps) or "us"

    # Root password
    config["root_password"] = menus.input_secret("Root password: ")

    # User
    username = menus.input_with_default("Username", "")
    if username:
        password = menus.input_secret(f"Password for {username}: ")
        config["users"] = [{
            "username": username,
            "password": password,
            "groups": ["wheel", "video", "audio", "plugdev"],
            "shell": "/bin/zsh",
        }]

    # Desktop
    desktops = ["none", "kde", "gnome", "xfce", "hyprland", "qtile"]
    config["desktop"] = menus.select_from_list("Desktop Environment", desktops) or "none"

    # Kernel
    kernels = ["gentoo-sources", "linux-firmware", "binkernel"]
    config["kernel"] = {
        "type": menus.select_from_list("Kernel Source", kernels) or "gentoo-sources",
        "method": "genkernel",
        "params": ["quiet", "splash"],
    }

    # Bootloader
    config["bootloader"] = "grub"

    return config


def install_from_profile() -> dict:
    """Load installation from YAML profile"""
    profile_path = menus.input_with_default("Profile path", "/mnt/config/profile.yaml")
    try:
        return loader.load_profile(profile_path)
    except Exception as e:
        menus.display_error(f"Failed to load profile: {e}")
        return {}


def partitioning_tool() -> None:
    """Run interactive partitioning"""
    menus.display_info(
        "Disk Partitioning",
        ["This tool helps you plan your partition layout."],
    )

    disks = disk.list_disks()
    if not disks:
        menus.display_error("No disks found")
        return

    disk_choice = menus.select_from_list(
        "Select Disk",
        [f"{d['name']} ({d['size']})" for d in disks],
    )

    if disk_choice:
        selected = disk_choice.split()[0]
        menus.display_info(
            f"Disk: {selected}",
            [
                "Warning: This will erase the entire disk!",
                "Plan:",
                "  1. EFI System Partition (512MB)",
                "  2. Boot Partition (1GB)",
                "  3. Swap (RAM size)",
                "  4. Root Partition (Remaining)",
            ],
        )

        if menus.confirm("Proceed with partitioning?", default=False):
            success = disk.auto_partition(selected, Path("/mnt/gentoo"))
            if success:
                menus.display_success("Partitioning complete")
            else:
                menus.display_error("Partitioning failed")


def main() -> int:
    """Main entry point"""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    setup_logging(verbose)

    print("""
  ╔══════════════════════════════════════════╗
  ║          Gentoo Installer v1.0           ║
  ║     Automated Gentoo Linux Setup         ║
  ╚══════════════════════════════════════════╝
    """)

    while True:
        choice = main_menu()

        if choice == "Interactive Installation":
            config = interactive_install()
            if menus.confirm("Start installation with these settings?", default=False):
                installer = Installer(config)
                success = installer.run()
                if success:
                    menus.display_success("Installation completed successfully!")
                else:
                    menus.display_error("Installation failed. Check logs for details.")
                return 0 if success else 1

        elif choice == "Install from Profile (YAML)":
            config = install_from_profile()
            if config and menus.confirm("Start installation?", default=False):
                installer = Installer(config)
                success = installer.run()
                return 0 if success else 1

        elif choice == "Disk Partitioning Tool":
            partitioning_tool()

        elif choice == "Save Current Config as Profile":
            path = menus.input_with_default("Save profile to", "./profile.yaml")
            # Would need current config state here
            menus.display_info("Not implemented", ["Use YAML directly for now."])

        elif choice == "Exit" or choice is None:
            print("\nGoodbye!")
            return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
