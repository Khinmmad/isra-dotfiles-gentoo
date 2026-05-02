#!/usr/bin/env python3
"""
Gentoo Installer — Desktop Environment Module
Installs and configures DE/WMs: KDE, GNOME, XFCE, Hyprland, Qtile
"""

import logging
from pathlib import Path

logger = logging.getLogger("gentoo-installer")


def install_desktop(root: Path, desktop: str, init_system: str = "openrc") -> bool:
    """
    Install the selected desktop environment
    desktop: one of 'kde', 'gnome', 'xfce', 'hyprland', 'qtile', 'none'
    """
    from . import portage, chroot

    if desktop == "none":
        logger.info("No desktop environment selected")
        return True

    packages = []
    services = []

    logger.info(f"Installing desktop environment: {desktop}")

    if desktop == "kde":
        packages = ["kde-plasma/plasma-meta", "kde-apps/kde-apps-meta"]
        services = ["dbus", "sddm"]
        # Enable elogind for OpenRC
        if init_system == "openrc":
            packages.append("sys-auth/elogind")

    elif desktop == "gnome":
        packages = ["gnome-base/gnome", "gnome-base/gnome-light"]
        services = ["dbus", "gdm"]
        if init_system == "openrc":
            packages.append("sys-auth/elogind")

    elif desktop == "xfce":
        packages = ["xfce-base/xfce4-meta", "xfce-base/xfce4-session"]
        services = ["dbus", "slim"]
        if init_system == "openrc":
            packages.append("sys-auth/elogind")

    elif desktop == "hyprland":
        packages = [
            "dev-util/hyprland",  # Requires overlay or ~amd64
            "gui-apps/waybar",
            "gui-apps/wofi",
            "gui-apps/hyprlock",
            "gui-apps/hypridle",
        ]
        services = ["dbus"]
        if init_system == "openrc":
            packages.append("sys-auth/elogind")

    elif desktop == "qtile":
        packages = ["gui-wm/qtile", "x11-misc/slim"]
        services = ["dbus"]
        if init_system == "openrc":
            packages.append("sys-auth/elogind")

    else:
        logger.error(f"Unknown desktop: {desktop}")
        return False

    # Install packages
    for pkg in packages:
        if not portage.emerge(root, [pkg]):
            logger.warning(f"Failed to install {pkg}, continuing...")

    # Enable services
    if init_system == "openrc":
        for svc in services:
            if svc == "sddm":
                chroot.chroot_run(root, f"rc-update add display-manager default", check=False)
            elif svc == "gdm":
                chroot.chroot_run(root, f"rc-update add gdm default", check=False)
            elif svc == "slim":
                chroot.chroot_run(root, f"rc-update add slim default", check=False)
            else:
                chroot.chroot_run(root, f"rc-update add {svc} default", check=False)

    logger.info(f"Desktop environment {desktop} setup complete")
    return True
