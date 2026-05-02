#!/usr/bin/env python3
"""
Gentoo Installer — Stage3 Module
Download stage3 tarball, extract
"""

import subprocess
import logging
import re
from pathlib import Path
from typing import Optional
from urllib.request import urlopen
from html.parser import HTMLParser

logger = logging.getLogger("gentoo-installer")


class Stage3Info:
    """Info about a stage3 tarball"""
    def __init__(self, name: str, url: str, size: str = ""):
        self.name = name
        self.url = url
        self.size = size

    def __repr__(self):
        return f"Stage3Info({self.name})"


class LinkParser(HTMLParser):
    """Parse HTML to find stage3 tarball links"""
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_link = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.current_link = value

    def handle_data(self, data):
        if "stage3" in data.lower() and "tar." in self.current_link:
            if not self.current_link.startswith(".."):
                self.links.append((self.current_link.strip(), data.strip()))


def fetch_stage3_list(mirror: str) -> list[Stage3Info]:
    """Fetch list of available stage3 tarballs from mirror"""
    if not mirror.endswith("/"):
        mirror += "/"
    
    url = f"{mirror}releases/amd64/autobuilds/"
    logger.info(f"Fetching stage3 list from {url}")

    try:
        response = urlopen(url, timeout=15)
        html = response.read().decode("utf-8", errors="ignore")

        parser = LinkParser()
        parser.feed(html)

        stage3_list = []
        seen = set()
        for link, text in parser.links:
            if "stage3-amd64" in link and link.endswith(".tar.xz"):
                # Filter out .CONTENTS, .DIGESTS, etc
                if ".CONTENTS" not in link and ".DIGESTS" not in link and "SYSTEMD" not in link.upper():
                    if link not in seen:
                        seen.add(link)
                        stage3_list.append(Stage3Info(
                            name=link,
                            url=f"{url}{link}"
                        ))

        return stage3_list

    except Exception as e:
        logger.error(f"Error fetching stage3 list: {e}")
        return []


def select_stage3(mirror: str, preferred: str = "desktop-openrc") -> Optional[Stage3Info]:
    """Select best stage3 tarball"""
    stage3_list = fetch_stage3_list(mirror)

    if not stage3_list:
        logger.error("No stage3 tarballs found")
        return None

    # Try to find preferred type
    for s3 in stage3_list:
        if preferred in s3.name:
            logger.info(f"Selected stage3: {s3.name}")
            return s3

    # Fallback to first available
    logger.info(f"Fallback stage3: {stage3_list[0].name}")
    return stage3_list[0]


def download_stage3(stage3: Stage3Info, dest: Path) -> Path:
    """Download stage3 tarball"""
    output = dest / stage3.name
    logger.info(f"Downloading {stage3.url} to {output}")

    try:
        # Use wget for resume support
        subprocess.run(
            ["wget", "-c", "-O", str(output), stage3.url],
            check=True
        )
        logger.info(f"Downloaded {stage3.name} ({output.stat().st_size / (1024**3):.2f} GB)")
        return output

    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading stage3: {e}")
        raise RuntimeError(f"Failed to download {stage3.name}")
    except FileNotFoundError:
        # Fallback to curl
        try:
            subprocess.run(
                ["curl", "-L", "-o", str(output), stage3.url],
                check=True
            )
            return output
        except Exception as e:
            logger.error(f"Error downloading with curl: {e}")
            raise RuntimeError(f"Failed to download {stage3.name}")


def extract_stage3(tarball: Path, root: Path) -> bool:
    """
    Extract stage3 tarball to root
    Uses tar xpf --xattrs-include='*.*' --numeric-owner
    """
    logger.info(f"Extracting {tarball} to {root}")

    try:
        root.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "tar", "xpf", str(tarball),
                "--xattrs-include='*.*'",
                "--numeric-owner",
                "-C", str(root)
            ],
            check=True
        )

        logger.info(f"Extracted {tarball} to {root}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting stage3: {e}")
        return False


def download_and_extract(mirror: str, dest: Path, root: Path, preferred: str = "desktop-openrc") -> bool:
    """Full download + extract workflow"""
    stage3 = select_stage3(mirror, preferred)
    if not stage3:
        return False

    tarball = download_stage3(stage3, dest)
    return extract_stage3(tarball, root)
