#!/usr/bin/env python3
"""
Gentoo Installer — Users Module
Root passwd, user creation, sudo
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")


def set_root_password(root: Path, password: str) -> bool:
    """
    Set root password
    Uses chpasswd for non-interactive password setting
    """
    from . import chroot

    logger.info("Setting root password")

    try:
        result = chroot.chroot_run(root, f'echo "root:{password}" | chpasswd')

        if result.ok:
            logger.info("Root password set")
            return True
        else:
            logger.error(f"Failed to set root password: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error setting root password: {e}")
        return False


def create_user(
    root: Path,
    username: str,
    password: str,
    groups: list[str],
    shell: str = "/bin/zsh"
) -> bool:
    """
    Create a new user
    groups: list of supplementary groups
    """
    from . import chroot

    logger.info(f"Creating user: {username}")

    # Ensure groups exist
    system_groups = ["wheel", "video", "audio", "users", "plugdev", "cdrom", "input", "kvm"]
    for group in groups:
        # Check if group exists
        result = chroot.chroot_run(root, f"getent group {group}", check=False)
        if not result.ok:
            # Create the group
            chroot.chroot_run(root, f"groupadd {group}", check=False)

    # Create user with primary group 'users' and supplementary groups
    groups_str = ",".join(groups)
    cmd = f"useradd -m -g users -G {groups_str} -s {shell} {username}"
    result = chroot.chroot_run(root, cmd)

    if not result.ok:
        logger.error(f"Failed to create user: {result.stderr}")
        return False

    # Set user password
    result = chroot.chroot_run(root, f'echo "{username}:{password}" | chpasswd')
    if not result.ok:
        logger.error(f"Failed to set user password: {result.stderr}")
        return False

    logger.info(f"User {username} created with groups: {groups}")
    return True


def set_user_password(root: Path, username: str, password: str) -> bool:
    """Set password for an existing user"""
    from . import chroot

    result = chroot.chroot_run(root, f'echo "{username}:{password}" | chpasswd')
    return result.ok


def add_user_to_group(root: Path, username: str, group: str) -> bool:
    """Add user to a group"""
    from . import chroot

    result = chroot.chroot_run(root, f"gpasswd -a {username} {group}")
    return result.ok


def configure_sudo(root: Path, nopasswd: bool = True, user: str = "") -> bool:
    """
    Configure sudo
    nopasswd: if True, user can sudo without password
    user: specific user, or empty for wheel group
    """
    from . import chroot

    logger.info("Configuring sudo...")

    # Install sudo if not present
    chroot.chroot_run(root, "emerge --ask=n sys-auth/sudo", check=False)

    # Configure sudoers
    sudoers_file = root / "etc/sudoers.d/wheel"

    try:
        if nopasswd:
            content = "%wheel ALL=(ALL:ALL) NOPASSWD:ALL\n"
        else:
            content = "%wheel ALL=(ALL:ALL) ALL\n"

        # Add specific user config if specified
        if user:
            if nopasswd:
                content += f"{user} ALL=(ALL:ALL) NOPASSWD:ALL\n"
            else:
                content += f"{user} ALL=(ALL:ALL) ALL\n"

        # Ensure sudoers.d directory exists
        sudoers_file.parent.mkdir(parents=True, exist_ok=True)

        # Write with proper permissions
        with open(sudoers_file, "w") as f:
            f.write(content)

        # Set permissions (0440 required for sudoers files)
        import os
        os.chmod(sudoers_file, 0o440)

        # Uncomment %wheel in sudoers if needed
        main_sudoers = root / "etc/sudoers"
        if main_sudoers.exists():
            try:
                with open(main_sudoers) as f:
                    content = f.read()

                # Uncomment the wheel line
                content = content.replace("# %wheel", "%wheel")

                with open(main_sudoers, "w") as f:
                    f.write(content)
            except IOError:
                pass

        logger.info("Sudo configured")
        return True

    except Exception as e:
        logger.error(f"Error configuring sudo: {e}")
        return False


def setup_root_user(root: Path) -> bool:
    """Ensure root user is properly configured"""
    from . import chroot

    # Set root shell to zsh
    result = chroot.chroot_run(root, "chsh -s /bin/zsh root", check=False)

    # Create .zshrc for root
    zshrc = root / "root/.zshrc"
    zshrc.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(zshrc, "w") as f:
            f.write("# Root .zshrc\n")
            f.write("export EDITOR=vim\n")
            f.write("alias ll='ls -la'\n")
        return True
    except IOError:
        return False
