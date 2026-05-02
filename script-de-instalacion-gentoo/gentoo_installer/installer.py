#!/usr/bin/env python3
"""
Gentoo Installer — Main Installer Class
Orchestrates the full installation process
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")


class Installer:
    """Main installer orchestrator"""

    def __init__(self, config: dict):
        self.config = config
        self.mount_root = Path(config.get("mount_root", "/mnt/gentoo"))
        self.errors = []
        self.warnings = []

    def run(self) -> bool:
        """Execute the full installation"""
        logger.info("Starting Gentoo installation")

        try:
            self._verify_environment()
            self._setup_disks()
            self._install_stage3()
            self._configure_portage()
            self._chroot_install()
            self._configure_locale_timezone()
            self._configure_network()
            self._setup_users()
            self._install_kernel()
            self._install_desktop()
            self._install_bootloader()
            self._finalize()

            logger.info("Installation completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Installation failed: {e}")
            self.errors.append(str(e))
            return False

    def _verify_environment(self) -> None:
        """Verify we're running in a live environment with required tools"""
        from .core import disk

        logger.info("Verifying environment...")

        # Check root privileges
        import os
        if os.geteuid() != 0:
            raise RuntimeError("This script must be run as root")

        # Check required commands
        required = ["mount", "mkfs.ext4", "wget", "tar", "chroot"]
        for cmd in required:
            if not disk.command_exists(cmd):
                raise RuntimeError(f"Required command not found: {cmd}")

        logger.info("Environment verified")

    def _setup_disks(self) -> None:
        """Partition and format disks"""
        from .core import disk

        logger.info("Setting up disks...")
        disk_config = self.config.get("partitions", [])

        if not disk_config:
            raise RuntimeError("No partition configuration provided")

        # Execute partitioning plan
        success = disk.execute_partition_plan(disk_config, self.mount_root)
        if not success:
            raise RuntimeError("Disk setup failed")

        logger.info("Disks configured")

    def _install_stage3(self) -> None:
        """Download and extract stage3"""
        from .core import stage3

        logger.info("Installing stage3...")
        profile = self.config.get("stage3_profile", "")
        mirror = self.config.get("mirror", "")

        if not profile:
            # Try to auto-detect
            stage3_url = stage3.detect_and_download(self.mount_root, mirror=mirror)
        else:
            stage3_url = stage3.download_stage3(self.mount_root, profile, mirror=mirror)

        if not stage3_url:
            raise RuntimeError("Stage3 download failed")

        logger.info("Stage3 installed")

    def _configure_portage(self) -> None:
        """Configure Portage"""
        from .core import portage

        logger.info("Configuring Portage...")

        # Configure make.conf
        make_conf = self.config.get("make_conf", {})
        if make_conf:
            portage.configure_make_conf(self.mount_root, make_conf)

        # Set profile
        profile = self.config.get("portage_profile", "")
        if profile:
            portage.set_profile(self.mount_root, profile)

        # Sync repository
        portage.sync(self.mount_root)

        logger.info("Portage configured")

    def _chroot_install(self) -> None:
        """Install base system in chroot"""
        from .core import portage, chroot

        logger.info("Installing base system...")

        # Install base packages
        base_packages = self.config.get("base_packages", [
            "sys-kernel/gentoo-sources",
            "sys-kernel/genkernel",
            "sys-boot/grub",
            "net-misc/dhcpcd",
            "sys-apps/mlocate",
            "app-admin/sysstat",
        ])

        for pkg in base_packages:
            if not portage.emerge(self.mount_root, [pkg]):
                self.warnings.append(f"Failed to install {pkg}")

        logger.info("Base system installed")

    def _configure_locale_timezone(self) -> None:
        """Configure locale and timezone"""
        from .core import timezone

        logger.info("Configuring locale and timezone...")

        tz = self.config.get("timezone", "UTC")
        locale = self.config.get("locale", "en_US.UTF-8")
        keymap = self.config.get("keymap", "us")
        utc = self.config.get("hwclock_utc", True)

        timezone.configure_timezone(self.mount_root, tz)
        timezone.configure_locale(self.mount_root, locale)
        timezone.configure_keymap(self.mount_root, keymap)
        timezone.configure_hwclock(self.mount_root, utc)

        logger.info("Locale and timezone configured")

    def _configure_network(self) -> None:
        """Configure network"""
        from .core import network

        logger.info("Configuring network...")
        network.setup_network(self.mount_root, self.config)
        logger.info("Network configured")

    def _setup_users(self) -> None:
        """Create users and configure sudo"""
        from .core import users

        logger.info("Setting up users...")

        # Set root password
        root_pass = self.config.get("root_password", "")
        if root_pass:
            users.set_root_password(self.mount_root, root_pass)

        # Create user accounts
        for user_config in self.config.get("users", []):
            username = user_config.get("username", "")
            password = user_config.get("password", "")
            groups = user_config.get("groups", ["wheel", "video", "audio"])
            shell = user_config.get("shell", "/bin/zsh")

            if username and password:
                users.create_user(self.mount_root, username, password, groups, shell)

        # Configure sudo
        users.configure_sudo(self.mount_root, nopasswd=True)

        logger.info("Users configured")

    def _install_kernel(self) -> None:
        """Install and compile kernel"""
        from .core import kernel

        logger.info("Installing kernel...")

        kernel_config = self.config.get("kernel", {})
        kernel_type = kernel_config.get("type", "gentoo-sources")
        kernel_method = kernel_config.get("method", "genkernel")
        kernel_params = kernel_config.get("params", [])

        if kernel_method == "genkernel":
            kernel.install_genkernel(self.mount_root, kernel_type, kernel_params)
        elif kernel_method == "manual":
            config_path = kernel_config.get("config_path", "")
            kernel.install_manual(self.mount_root, kernel_type, config_path, kernel_params)
        elif kernel_method == "binkernel":
            kernel.install_binkernel(self.mount_root, kernel_params)

        logger.info("Kernel installed")

    def _install_desktop(self) -> None:
        """Install desktop environment"""
        from .core import desktop

        logger.info("Installing desktop...")
        desktop_type = self.config.get("desktop", "none")
        init_system = self.config.get("init_system", "openrc")

        desktop.install_desktop(self.mount_root, desktop_type, init_system)

        logger.info("Desktop installed")

    def _install_bootloader(self) -> None:
        """Install bootloader"""
        from .core import bootloader

        logger.info("Installing bootloader...")

        bl_type = self.config.get("bootloader", "grub")
        disk_name = self.config.get("target_disk", "")
        efi = self.config.get("efi", True)

        if not disk_name:
            self.warnings.append("No target disk specified, skipping bootloader")
            return

        bootloader.setup_bootloader(self.mount_root, disk_name, bl_type, efi)

        # Set kernel parameters
        params = self.config.get("kernel", {}).get("params", [])
        if params:
            bootloader.configure_grub_params(self.mount_root, params)
            bootloader.generate_grub_cfg(self.mount_root)

        logger.info("Bootloader installed")

    def _finalize(self) -> None:
        """Final steps: fstab, cleanup, unmount"""
        from .core import fstab, disk

        logger.info("Finalizing installation...")

        # Generate fstab
        fstab.generate_fstab(self.mount_root)

        # Cleanup
        # (Portage cache cleanup, etc.)

        # Unmount
        disk.unmount_all(self.mount_root)

        logger.info("Installation finalized")
