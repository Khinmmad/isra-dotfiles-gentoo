#!/usr/bin/env python3
"""
Gentoo Installer — Chroot Module
Setup chroot, execute commands in chroot, cleanup
"""

import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("gentoo-installer")


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


# Mount points needed for chroot
CHROOT_BINDS = [
    "/dev",
    "/dev/pts",
    "/proc",
    "/sys",
    "/run",
    "/tmp",
]


def setup_chroot(root: Path) -> bool:
    """
    Setup chroot environment
    Mount --bind /dev, /proc, /sys, /run
    Copy resolv.conf
    """
    root = Path(root)
    logger.info(f"Setting up chroot at {root}")

    try:
        # Copy resolv.conf for network
        if Path("/etc/resolv.conf").exists():
            subprocess.run(
                ["cp", "-L", "/etc/resolv.conf", str(root / "etc/resolv.conf")],
                check=True
            )

        # Bind mount required filesystems
        for mount in CHROOT_BINDS:
            src = Path(mount)
            dst = root / mount.relative("/")
            dst.mkdir(parents=True, exist_ok=True)

            if mount == "/dev":
                subprocess.run(["mount", "--rbind", str(src), str(dst)], check=True)
            elif mount == "/dev/pts":
                subprocess.run(["mount", "--rbind", str(src), str(dst)], check=True)
            else:
                subprocess.run(["mount", "--bind", str(src), str(dst)], check=True)

        logger.info(f"Chroot setup complete at {root}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting up chroot: {e}")
        # Attempt partial cleanup
        cleanup_chroot(root)
        return False


def chroot_run(root: Path, cmd: str, check: bool = True, timeout: Optional[int] = None, env: dict = None) -> ProcessResult:
    """
    Execute a command inside chroot
    Returns ProcessResult with returncode, stdout, stderr
    """
    root = Path(root)

    # Build environment
    chroot_env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "TERM": "xterm-256color",
        "HOME": "/root",
    }
    if env:
        chroot_env.update(env)

    env_args = []
    for key, value in chroot_env.items():
        env_args.extend([f"{key}={value}"])

    full_cmd = ["chroot", str(root), "env"] + env_args + ["/bin/bash", "-c", cmd]

    logger.info(f"Chroot exec: {cmd}")

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout
        )

        if result.stdout:
            logger.debug(f"stdout: {result.stdout[:200]}")
        if result.stderr:
            logger.debug(f"stderr: {result.stderr[:200]}")

        return ProcessResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {cmd}")
        return ProcessResult(returncode=-1, stdout="", stderr="Timeout")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed (rc={e.returncode}): {cmd}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout[:500]}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr[:500]}")
        return ProcessResult(
            returncode=e.returncode,
            stdout=e.stdout or "",
            stderr=e.stderr or ""
        )
    except FileNotFoundError:
        logger.error(f"chroot binary not found")
        return ProcessResult(returncode=-1, stdout="", stderr="chroot not found")


def cleanup_chroot(root: Path) -> bool:
    """
    Cleanup chroot environment
    Unmount all bind mounts
    """
    root = Path(root)
    logger.info(f"Cleaning up chroot at {root}")

    errors = []
    # Unmount in reverse order
    for mount in reversed(CHROOT_BINDS):
        dst = root / mount.relative("/")
        if dst.exists() or dst.is_mount():
            try:
                subprocess.run(["umount", "-l", str(dst)], check=True)
            except subprocess.CalledProcessError as e:
                errors.append(f"Failed to unmount {dst}: {e}")

    if errors:
        logger.warning(f"Some unmounts failed: {errors}")
        return False

    logger.info(f"Chroot cleanup complete")
    return True


def emerge_in_chroot(root: Path, packages: list[str], flags: str = "") -> ProcessResult:
    """Run emerge inside chroot"""
    cmd = f"emerge --ask=n --verbose {flags} {' '.join(packages)}"
    return chroot_run(root, cmd, timeout=None)


def eselect_in_chroot(root: Path, module: str, action: str) -> ProcessResult:
    """Run eselect inside chroot"""
    cmd = f"eselect {module} {action}"
    return chroot_run(root, cmd)
