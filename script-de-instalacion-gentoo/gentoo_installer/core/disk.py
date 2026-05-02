#!/usr/bin/env python3
"""
Gentoo Installer — Core Disk Module
Particionado (parted/gdisk), formateo, mount
"""

import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("gentoo-installer")


@dataclass
class Disk:
    name: str
    size: str
    model: str
    path: str = ""
    removable: bool = False
    readonly: bool = False

    def __post_init__(self):
        if not self.path:
            self.path = f"/dev/{self.name}"


@dataclass
class Partition:
    number: int
    start: str
    end: str
    size: str
    fs: str
    mount: str
    path: str = ""
    bootable: bool = False
    flags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.path:
            self.path = f"/dev/{self.name}p{self.number}" if "nvme" in self.name or "mmc" in self.name else f"/dev/{self.name}{self.number}"


def list_disks() -> list[Disk]:
    """Detectar todos los discos disponibles usando lsblk"""
    disks = []
    try:
        result = subprocess.run(
            ["lsblk", "-d", "-n", "-o", "NAME,SIZE,MODEL,ROTA,RM,RO"],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                size = parts[1]
                model = " ".join(parts[2:-3]) if len(parts) > 5 else parts[2]
                is_removable = parts[-1] == "1" if parts else False
                is_readonly = parts[-1] == "1" if parts else False

                # Skip loop devices and ram
                if name.startswith(("loop", "ram", "sr")):
                    continue

                disk = Disk(name=name, size=size, model=model, removable=is_removable, readonly=is_readonly)
                disks.append(disk)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing disks: {e}")
    except FileNotFoundError:
        logger.error("lsblk not found")
    return disks


def detect_disks() -> list[Disk]:
    """Alias for list_disks"""
    return list_disks()


def get_disk_info(disk_name: str) -> Optional[Disk]:
    """Get info for a specific disk"""
    for disk in list_disks():
        if disk.name == disk_name:
            return disk
    return None


def list_partitions(disk_name: str) -> list[Partition]:
    """List existing partitions on a disk"""
    partitions = []
    try:
        result = subprocess.run(
            ["lsblk", f"/dev/{disk_name}", "-n", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT"],
            capture_output=True, text=True, check=True
        )
        for i, line in enumerate(result.stdout.strip().splitlines()):
            parts = line.split()
            if len(parts) >= 2 and parts[0] != disk_name:
                part = Partition(
                    number=i + 1,
                    start="",
                    end="",
                    size=parts[1] if len(parts) > 1 else "",
                    fs=parts[2] if len(parts) > 2 else "",
                    mount=parts[3] if len(parts) > 3 else "",
                    path=f"/dev/{parts[0]}"
                )
                partitions.append(part)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing partitions: {e}")
    return partitions


def wipe_disk(disk_path: str) -> bool:
    """Wipe disk signature and partition table"""
    logger.info(f"Wiping disk {disk_path}")
    try:
        subprocess.run(["wipefs", "-a", disk_path], check=True, capture_output=True)
        subprocess.run(["dd", "if=/dev/zero", f"of={disk_path}", "bs=1M", "count=10"],
                      check=True, capture_output=True)
        logger.info(f"Disk {disk_path} wiped")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error wiping disk: {e}")
        return False


def create_partitions_gpt(disk_name: str, scheme: list[dict]) -> bool:
    """
    Crear particiones usando parted (GPT)
    scheme: list of {"size": "512M", "fs": "fat32", "mount": "/boot/efi", "bootable": True}
    """
    disk_path = f"/dev/{disk_name}"
    logger.info(f"Creating GPT partitions on {disk_path}")

    try:
        # Create GPT label
        subprocess.run(["parted", "-s", disk_path, "mklabel", "gpt"], check=True)

        current_start = "0%"
        for i, part in enumerate(scheme):
            size = part.get("size", "100%")
            end = f"{current_start}+{size}" if size != "100%" and size != "free" else "100%"

            # Create partition
            fs_type = "fat32" if part.get("fs") == "fat32" else "ext4"
            if part.get("fs") == "swap":
                fs_type = "linux-swap"

            cmd = ["parted", "-s", disk_path, "mkpart", "primary", fs_type, current_start, end]
            subprocess.run(cmd, check=True)

            # Set boot flag
            if part.get("bootable"):
                if part.get("fs") == "fat32":
                    subprocess.run(["parted", "-s", disk_path, "set", str(i + 1), "esp", "on"], check=True)
                else:
                    subprocess.run(["parted", "-s", disk_path, "set", str(i + 1), "boot", "on"], check=True)

            current_start = end if size != "100%" and size != "free" else "100%"

        logger.info(f"GPT partitions created on {disk_path}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating GPT partitions: {e}")
        return False


def create_partitions_mbr(disk_name: str, scheme: list[dict]) -> bool:
    """
    Crear particiones usando parted (MBR)
    """
    disk_path = f"/dev/{disk_name}"
    logger.info(f"Creating MBR partitions on {disk_path}")

    try:
        # Create MBR label
        subprocess.run(["parted", "-s", disk_path, "mklabel", "msdos"], check=True)

        current_start = "1M"
        for i, part in enumerate(scheme):
            size = part.get("size", "100%")
            end = f"{current_start}+{size}" if size != "100%" and size != "free" else "100%"

            fs_type = "fat32" if part.get("fs") == "fat32" else "ext4"
            if part.get("fs") == "swap":
                fs_type = "linux-swap"

            cmd = ["parted", "-s", disk_path, "mkpart", "primary", fs_type, current_start, end]
            subprocess.run(cmd, check=True)

            if part.get("bootable"):
                subprocess.run(["parted", "-s", disk_path, "set", str(i + 1), "boot", "on"], check=True)

            current_start = end if size != "100%" and size != "free" else "100%"

        logger.info(f"MBR partitions created on {disk_path}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating MBR partitions: {e}")
        return False


def format_partition(partition_path: str, fs: str, label: str = "") -> bool:
    """Format a partition with the specified filesystem"""
    logger.info(f"Formatting {partition_path} as {fs}")

    try:
        if fs == "ext4":
            cmd = ["mkfs.ext4", "-F"]
            if label:
                cmd.extend(["-L", label])
            cmd.append(partition_path)
            subprocess.run(cmd, check=True)

        elif fs == "btrfs":
            cmd = ["mkfs.btrfs", "-f"]
            if label:
                cmd.extend(["-L", label])
            cmd.append(partition_path)
            subprocess.run(cmd, check=True)

        elif fs == "xfs":
            cmd = ["mkfs.xfs", "-f"]
            if label:
                cmd.extend(["-L", label])
            cmd.append(partition_path)
            subprocess.run(cmd, check=True)

        elif fs == "fat32":
            cmd = ["mkfs.fat", "-F", "32"]
            if label:
                cmd.extend(["-n", label])
            cmd.append(partition_path)
            subprocess.run(cmd, check=True)

        elif fs == "ext2":
            cmd = ["mkfs.ext2"]
            if label:
                cmd.extend(["-L", label])
            cmd.append(partition_path)
            subprocess.run(cmd, check=True)

        elif fs == "swap":
            subprocess.run(["mkswap", partition_path], check=True)

        else:
            logger.error(f"Unsupported filesystem: {fs}")
            return False

        logger.info(f"Partition {partition_path} formatted as {fs}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error formatting partition: {e}")
        return False


def mount_partition(partition_path: str, mount_point: Path, fs: str = "", options: str = "") -> bool:
    """Mount a partition to a mount point"""
    logger.info(f"Mounting {partition_path} to {mount_point}")

    try:
        mount_point.mkdir(parents=True, exist_ok=True)

        cmd = ["mount"]
        if options:
            cmd.extend(["-o", options])
        if fs:
            cmd.extend(["-t", fs])
        cmd.extend([partition_path, str(mount_point)])

        subprocess.run(cmd, check=True)
        logger.info(f"Mounted {partition_path} at {mount_point}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error mounting partition: {e}")
        return False


def umount_recursive(path: Path) -> bool:
    """Unmount a path and all its submounts"""
    try:
        subprocess.run(["umount", "-R", str(path)], check=True)
        logger.info(f"Unmounted {path} recursively")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error unmounting {path}: {e}")
        return False


def partition_disk(disk_name: str, scheme: list[dict], is_uefi: bool) -> list[str]:
    """
    Full disk partitioning workflow
    Returns list of partition paths
    """
    disk_path = f"/dev/{disk_name}"

    # Wipe existing
    if not wipe_disk(disk_path):
        raise RuntimeError(f"Failed to wipe disk {disk_path}")

    # Create partition table
    if is_uefi:
        if not create_partitions_gpt(disk_name, scheme):
            raise RuntimeError("Failed to create GPT partitions")
    else:
        if not create_partitions_mbr(disk_name, scheme):
            raise RuntimeError("Failed to create MBR partitions")

    # Wait for partitions to appear
    import time
    time.sleep(2)

    # Get partition paths
    partitions = []
    prefix = f"{disk_path}p" if "nvme" in disk_name or "mmc" in disk_name else f"{disk_path}"
    for i in range(1, len(scheme) + 1):
        part_path = f"{prefix}{i}"
        if Path(part_path).exists():
            partitions.append(part_path)

    return partitions


def format_and_mount_partitions(partitions: list[str], scheme: list[dict], root_mount: Path) -> dict[str, str]:
    """
    Format all partitions and mount them
    Returns mapping of mount_point -> partition_path
    """
    mounts = {}

    for i, (part_path, part_scheme) in enumerate(zip(partitions, scheme)):
        fs = part_scheme.get("fs", "ext4")
        mount = part_scheme.get("mount", "")

        # Format
        if not format_partition(part_path, fs):
            raise RuntimeError(f"Failed to format {part_path}")

        # Mount
        if mount == "swap":
            subprocess.run(["swapon", part_path], check=True)
            mounts["swap"] = part_path
        elif mount:
            mount_point = root_mount / mount.lstrip("/")
            if not mount_partition(part_path, mount_point, fs):
                raise RuntimeError(f"Failed to mount {part_path} to {mount_point}")
            mounts[mount] = part_path

    return mounts
