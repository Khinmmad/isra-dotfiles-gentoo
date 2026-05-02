#!/usr/bin/env python3
"""
Gentoo Installer — Bootloader Module
GRUB install/config (UEFI/BIOS)
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")


def is_uefi() -> bool:
    """Detect if system boots in UEFI mode"""
    return Path("/sys/firmware/efi").exists()


def install_grub(root: Path, disk: str, efi: bool) -> bool:
    """
    Install GRUB bootloader
    disk: disk name (e.g., nvme0n1 or sda)
    efi: whether to install in UEFI mode
    """
    from . import chroot, portage

    disk_path = f"/dev/{disk}"

    # Install grub package
    platform = "efi-64" if efi else "pc"
    logger.info(f"Installing GRUB ({platform})...")

    # Add GRUB_PLATFORMS to make.conf temporarily
    result = chroot.chroot_run(root, f"emerge --ask=n sys-boot/grub os-prober")

    if not result.ok:
        logger.error(f"Failed to emerge GRUB: {result.stderr[-300:]}")
        return False

    # Install GRUB to disk
    if efi:
        # UEFI installation
        efi_mount = Path(root) / "boot/efi"

        # Ensure EFI partition is mounted
        if not efi_mount.exists() or not efi_mount.is_mount():
            efi_mount.mkdir(parents=True, exist_ok=True)
            # Find EFI partition
            result = chroot.chroot_run(root, f"mount -t vfat {disk_path}1 /boot/efi", check=False)

        cmd = f"grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=Gentoo --recheck"
    else:
        # BIOS installation
        cmd = f"grub-install --target=i386-pc {disk_path}"

    logger.info(f"Running: {cmd}")
    result = chroot.chroot_run(root, cmd)

    if not result.ok:
        logger.error(f"GRUB installation failed: {result.stderr[-300:]}")
        return False

    logger.info("GRUB installed successfully")
    return True


def configure_grub_params(root: Path, params: list[str]) -> bool:
    """Add kernel parameters to GRUB_CMDLINE_LINUX_DEFAULT"""
    root = Path(root)
    default_grub = root / "etc/default/grub"

    if not default_grub.exists():
        logger.error("/etc/default/grub not found")
        return False

    try:
        # Read current content
        with open(default_grub) as f:
            content = f.read()

        # Build new GRUB_CMDLINE_LINUX_DEFAULT
        existing_params = ""
        for line in content.splitlines():
            if line.startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                # Extract existing params
                start = line.find('"') + 1
                end = line.rfind('"')
                if start > 0 and end > start:
                    existing_params = line[start:end]

        # Combine with new params
        new_params = f"{existing_params} {' '.join(params)}".strip()

        # Replace or add the line
        new_lines = []
        found = False
        for line in content.splitlines():
            if line.startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                new_lines.append(f'GRUB_CMDLINE_LINUX_DEFAULT="{new_params}"')
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f'GRUB_CMDLINE_LINUX_DEFAULT="{new_params}"')

        with open(default_grub, "w") as f:
            f.write("\n".join(new_lines) + "\n")

        logger.info(f"GRUB params updated: {new_params}")
        return True

    except IOError as e:
        logger.error(f"Error configuring GRUB params: {e}")
        return False


def generate_grub_cfg(root: Path) -> bool:
    """Generate GRUB configuration"""
    from . import chroot

    logger.info("Generating GRUB config...")

    # Enable os-prober
    default_grub = root / "etc/default/grub"
    if default_grub.exists():
        try:
            with open(default_grub) as f:
                content = f.read()

            if "GRUB_DISABLE_OS_PROBER" not in content:
                content += "\nGRUB_DISABLE_OS_PROBER=false\n"
                with open(default_grub, "w") as f:
                    f.write(content)
        except IOError:
            pass

    # Generate config
    result = chroot.chroot_run(root, "grub-mkconfig -o /boot/grub/grub.cfg")

    if result.ok:
        logger.info("GRUB config generated")
        return True
    else:
        logger.error(f"GRUB config generation failed: {result.stderr[-300:]}")
        return False


def setup_bootloader(root: Path, disk: str, bootloader_type: str = "grub", efi: bool = True) -> bool:
    """
    Complete bootloader setup
    """
    if bootloader_type == "grub":
        if not install_grub(root, disk, efi):
            return False
        return generate_grub_cfg(root)

    elif bootloader_type == "systemd-boot":
        return install_systemd_boot(root)

    elif bootloader_type == "refind":
        return install_refind(root)

    elif bootloader_type == "limine":
        return install_limine(root)

    elif bootloader_type == "none":
        logger.info("Skipping bootloader installation")
        return True

    else:
        logger.error(f"Unknown bootloader type: {bootloader_type}")
        return False


def install_systemd_boot(root: Path) -> bool:
    """Install systemd-boot (UEFI only)"""
    from . import chroot

    logger.info("Installing systemd-boot...")
    result = chroot.chroot_run(root, "bootctl install")

    if result.ok:
        logger.info("systemd-boot installed")
        return True
    else:
        logger.error(f"systemd-boot installation failed: {result.stderr[-300:]}")
        return False


def install_refind(root: Path) -> bool:
    """Install rEFInd"""
    from . import chroot, portage

    logger.info("Installing rEFInd...")
    portage.emerge(root, ["sys-boot/refind"])
    result = chroot.chroot_run(root, "refind-install")

    if result.ok:
        logger.info("rEFInd installed")
        return True
    else:
        logger.error(f"rEFInd installation failed: {result.stderr[-300:]}")
        return False


def install_limine(root: Path) -> bool:
    """Install Limine"""
    from . import chroot, portage

    logger.info("Installing Limine...")
    result = portage.emerge(root, ["sys-boot/limine"])

    if result:
        logger.info("Limine installed (manual config required)")
        return True
    return False
