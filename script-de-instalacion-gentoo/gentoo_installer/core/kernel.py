#!/usr/bin/env python3
"""
Gentoo Installer — Kernel Module
genkernel, modules, firmware
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")


def install_genkernel(root: Path) -> bool:
    """Install genkernel"""
    from . import chroot, portage

    logger.info("Installing genkernel")
    result = chroot.chroot_run(root, "emerge --ask=n sys-kernel/gentoo-sources sys-kernel/genkernel")

    if result.ok:
        logger.info("genkernel installed")
        return True
    else:
        logger.error(f"Failed to install genkernel: {result.stderr[-300:]}")
        return False


def build_genkernel(root: Path, config: dict) -> bool:
    """
    Build kernel using genkernel
    Options: initramfs, firmware, etc.
    """
    from . import chroot

    logger.info("Building kernel with genkernel...")

    # Build genkernel command
    cmd_parts = ["genkernel", "--install"]

    # Always build initramfs
    cmd_parts.append("--install-initramfs")

    # Add firmware if requested
    if config.get("kernel_firmware", True):
        cmd_parts.append("--linux-firmware")

    # Add menuconfig if manual mode
    if config.get("kernel_manual", False):
        cmd_parts.append("--menuconfig")

    cmd = " ".join(cmd_parts)
    result = chroot.chroot_run(root, cmd, timeout=None)

    if result.ok:
        logger.info("Kernel built successfully with genkernel")
        return True
    else:
        logger.error(f"genkernel failed: {result.stderr[-500:]}")
        return False


def install_debian_sources(root: Path) -> bool:
    """Install debian-sources (pre-built kernel)"""
    from . import chroot

    logger.info("Installing debian-sources...")
    result = chroot.chroot_run(root, "emerge --ask=n sys-kernel/debian-sources")

    if result.ok:
        logger.info("debian-sources installed")
        return True
    else:
        logger.error(f"Failed to install debian-sources: {result.stderr[-300:]}")
        return False


def install_gentoo_kernel_bin(root: Path) -> bool:
    """Install gentoo-kernel-bin (binary kernel)"""
    from . import chroot

    logger.info("Installing gentoo-kernel-bin...")
    result = chroot.chroot_run(root, "emerge --ask=n sys-kernel/gentoo-kernel-bin")

    if result.ok:
        logger.info("gentoo-kernel-bin installed")
        return True
    else:
        logger.error(f"Failed to install gentoo-kernel-bin: {result.stderr[-300:]}")
        return False


def install_firmware(root: Path) -> bool:
    """Install linux-firmware"""
    from . import chroot

    logger.info("Installing linux-firmware...")
    result = chroot.chroot_run(root, "emerge --ask=n sys-kernel/linux-firmware")

    if result.ok:
        logger.info("linux-firmware installed")
        return True
    else:
        logger.error(f"Failed to install linux-firmware: {result.stderr[-300:]}")
        return False


def install_microcode(root: Path, cpu_vendor: str = "auto") -> bool:
    """Install CPU microcode"""
    from . import chroot

    if cpu_vendor == "auto":
        cpu_vendor = detect_cpu_vendor(root)

    pkg = "sys-firmware/intel-microcode" if cpu_vendor == "intel" else "sys-firmware/amd-ucode"
    logger.info(f"Installing {pkg}...")

    result = chroot.chroot_run(root, f"emerge --ask=n {pkg}")

    if result.ok:
        logger.info(f"{pkg} installed")
        return True
    else:
        logger.error(f"Failed to install microcode: {result.stderr[-300:]}")
        return False


def detect_cpu_vendor(root: Path) -> str:
    """Detect CPU vendor from /proc/cpuinfo"""
    try:
        cpuinfo_path = Path(root) / "proc/cpuinfo"
        with open(cpuinfo_path) as f:
            content = f.read().lower()
            if "intel" in content:
                return "intel"
            elif "amd" in content:
                return "amd"
    except:
        pass
    return "amd"  # Default to AMD (safer for Ryzen)


def setup_kernel_modules(root: Path, config: dict) -> bool:
    """Configure kernel modules to load at boot"""
    from . import chroot

    modules_dir = Path(root) / "etc/modules-load.d"
    modules_dir.mkdir(parents=True, exist_ok=True)

    modules = []

    # NVIDIA modules
    if "nvidia" in config.get("video_cards", ""):
        modules.extend(["nvidia", "nvidia_modeset", "nvidia_drm", "nvidia_uvm"])

    # Bluetooth modules
    if config.get("bluetooth"):
        modules.append("btusb")

    if modules:
        mod_file = modules_dir / "custom.conf"
        try:
            with open(mod_file, "w") as f:
                f.write("# Loaded by Gentoo Installer\n")
                for mod in modules:
                    f.write(f"{mod}\n")
            logger.info(f"Written modules config to {mod_file}")
            return True
        except IOError as e:
            logger.error(f"Error writing modules config: {e}")
            return False

    return True
