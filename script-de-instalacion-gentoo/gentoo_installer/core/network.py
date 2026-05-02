#!/usr/bin/env python3
"""
Gentoo Installer — Network Module
Hostname, WiFi, netifrc/NetworkManager
"""

import subprocess
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gentoo-installer")


def detect_interfaces() -> list[dict]:
    """Detect available network interfaces"""
    interfaces = []
    try:
        result = subprocess.run(
            ["ip", "-o", "link", "show"],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().splitlines():
            match = re.match(r"(\d+):\s+(\S+?)(@\S+)?:\s+", line)
            if match:
                name = match.group(2)
                # Skip loopback
                if name == "lo":
                    continue
                # Determine type
                if name.startswith(("en", "eth")):
                    iface_type = "ethernet"
                elif name.startswith(("wl", "wlan")):
                    iface_type = "wifi"
                else:
                    iface_type = "unknown"

                interfaces.append({"name": name, "type": iface_type})
    except subprocess.CalledProcessError as e:
        logger.error(f"Error detecting interfaces: {e}")
    except FileNotFoundError:
        logger.warning("ip command not found")
    return interfaces


def scan_wifi(interface: str) -> list[dict]:
    """Scan for WiFi networks using iw"""
    networks = []
    try:
        result = subprocess.run(
            ["iw", "dev", interface, "scan"],
            capture_output=True, text=True, check=True
        )
        current = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("BSS"):
                if current.get("ssid"):
                    networks.append(current)
                current = {"ssid": "", "signal": ""}
            elif line.startswith("SSID:"):
                current["ssid"] = line.split(":", 1)[1].strip()
            elif line.startswith("signal:"):
                current["signal"] = line.split(":", 1)[1].strip()

        if current.get("ssid"):
            networks.append(current)

        # Remove duplicates, sort by signal
        seen = set()
        unique = []
        for net in networks:
            if net["ssid"] and net["ssid"] not in seen:
                seen.add(net["ssid"])
                unique.append(net)

        return unique

    except subprocess.CalledProcessError:
        logger.warning(f"Could not scan WiFi on {interface}")
        return []


def configure_hostname(root: Path, hostname: str) -> bool:
    """Set system hostname"""
    root = Path(root)

    try:
        # /etc/hostname
        hostname_file = root / "etc/hostname"
        with open(hostname_file, "w") as f:
            f.write(f"{hostname}\n")

        # /etc/hosts
        hosts_file = root / "etc/hosts"
        if hosts_file.exists():
            with open(hosts_file) as f:
                content = f.read()

            # Add hostname to 127.0.0.1 line
            new_lines = []
            for line in content.splitlines():
                if line.startswith("127.0.0.1"):
                    if hostname not in line:
                        line = f"127.0.0.1   localhost {hostname}"
                new_lines.append(line)

            with open(hosts_file, "w") as f:
                f.write("\n".join(new_lines) + "\n")

        logger.info(f"Hostname set to {hostname}")
        return True

    except IOError as e:
        logger.error(f"Error configuring hostname: {e}")
        return False


def configure_dhcp(root: Path, interface: str, init_system: str = "openrc") -> bool:
    """Configure DHCP for an interface"""
    from . import chroot, portage

    if init_system == "openrc":
        # Install dhcpcd
        portage.emerge(root, ["net-misc/dhcpcd"])

        # Enable dhcpcd service
        chroot.chroot_run(root, "rc-update add dhcpcd default")
        chroot.chroot_run(root, f"rc-service dhcpcd start", check=False)

    elif init_system == "systemd":
        # Use systemd-networkd
        chroot.chroot_run(root, "systemctl enable systemd-networkd")
        chroot.chroot_run(root, "systemctl enable systemd-resolved")

    logger.info(f"DHCP configured for {interface}")
    return True


def configure_wifi(root: Path, interface: str, ssid: str, password: str, init_system: str = "openrc") -> bool:
    """Configure WiFi connection"""
    from . import chroot, portage

    # Install wpa_supplicant
    portage.emerge(root, ["net-wireless/wpa_supplicant"])

    # Generate wpa_supplicant config
    wpa_conf = root / "etc/wpa_supplicant/wpa_supplicant.conf"
    wpa_conf.parent.mkdir(parents=True, exist_ok=True)

    # Generate PSK
    try:
        result = subprocess.run(
            ["wpa_passphrase", ssid, password],
            capture_output=True, text=True, check=True
        )
        wpa_config = result.stdout
    except:
        # Fallback manual config
        wpa_config = f"""network={{
    ssid="{ssid}"
    psk="{password}"
}}
"""

    try:
        with open(wpa_conf, "w") as f:
            f.write(wpa_config)

        if init_system == "openrc":
            # Copy wpa_supplicant conf for service
            chroot.chroot_run(root, f"rc-update add wpa_supplicant default")

        logger.info(f"WiFi configured: {ssid}")
        return True

    except IOError as e:
        logger.error(f"Error configuring WiFi: {e}")
        return False


def configure_networkmanager(root: Path, init_system: str = "openrc") -> bool:
    """Configure and enable NetworkManager"""
    from . import chroot, portage

    portage.emerge(root, ["net-misc/networkmanager"])

    if init_system == "openrc":
        chroot.chroot_run(root, "rc-update add NetworkManager default")
        chroot.chroot_run(root, "rc-service NetworkManager start", check=False)
    elif init_system == "systemd":
        chroot.chroot_run(root, "systemctl enable NetworkManager")

    logger.info("NetworkManager configured")
    return True


def setup_network(root: Path, config: dict) -> bool:
    """
    Complete network setup based on config
    """
    net_config = config.get("network", {})
    net_type = net_config.get("type", "dhcp")
    interface = net_config.get("iface", "")
    init_system = config.get("init_system", "openrc")

    if net_type == "none":
        logger.info("Skipping network configuration")
        return True

    if not interface:
        interfaces = detect_interfaces()
        if interfaces:
            interface = interfaces[0]["name"]
            logger.info(f"Using interface: {interface}")
        else:
            logger.warning("No network interface detected")
            return False

    # Set hostname
    configure_hostname(root, config.get("hostname", "gentoo"))

    if net_type == "dhcp":
        return configure_dhcp(root, interface, init_system)

    elif net_type == "wifi":
        ssid = net_config.get("wifi_ssid", "")
        password = net_config.get("wifi_pass", "")
        if ssid and password:
            return configure_wifi(root, interface, ssid, password, init_system)
        else:
            logger.error("WiFi SSID or password missing")
            return False

    elif net_type == "networkmanager":
        return configure_networkmanager(root, init_system)

    return False
