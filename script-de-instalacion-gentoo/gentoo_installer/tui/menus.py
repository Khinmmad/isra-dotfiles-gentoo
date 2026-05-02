#!/usr/bin/env python3
"""
Gentoo Installer — TUI Module
Interactive text-based user interface
"""

import logging
import sys
from typing import Optional

logger = logging.getLogger("gentoo-installer")


def select_from_list(title: str, options: list[str], multiple: bool = False) -> Optional[list[str] | str]:
    """
    Select one or more items from a list
    Tries simple-term-menu first, falls back to basic input
    """
    # Try simple-term-menu
    try:
        from simple_term_menu import TerminalMenu

        menu = TerminalMenu(
            options,
            title=title,
            menu_cursor_style=("fg_green",),
            menu_cursor="> ",
            menu_highlight_style=("fg_yellow",),
            cycle_cursor=True,
            clear_screen=False,
            multi_select=multiple,
            multi_select_cursor_style=("fg_magenta",),
            multi_select_keys=(" ", "Enter"),
            multi_select_cursor=" [ ] ",
            multi_select_selected=" [x] ",
            show_multi_select_hint=multiple,
        )

        idx = menu.show()

        if idx is None:
            return None

        if multiple:
            return [options[i] for i in idx]
        else:
            return options[idx]

    except ImportError:
        # Fallback to basic input
        return _basic_menu(title, options, multiple)


def _basic_menu(title: str, options: list[str], multiple: bool = False) -> Optional[list[str] | str]:
    """Fallback basic menu using input"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")

    for i, opt in enumerate(options):
        print(f"  {i + 1}. {opt}")

    print(f"{'=' * 60}")

    try:
        choice = input("Selection (number): ").strip()

        if not choice:
            return None

        if multiple:
            # Allow comma-separated selections
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            return [options[i] for i in indices if 0 <= i < len(options)]
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            return None

    except (ValueError, KeyboardInterrupt):
        print("\nCancelled.")
        return None


def input_with_default(prompt: str, default: str = "") -> str:
    """Input with default value display"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        value = input(full_prompt).strip()
        return value if value else default
    except KeyboardInterrupt:
        print("\nCancelled.")
        return default


def input_secret(prompt: str) -> str:
    """Input secret (password)"""
    import getpass
    try:
        return getpass.getpass(prompt)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return ""


def confirm(message: str, default: bool = True) -> bool:
    """Yes/No confirmation"""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        choice = input(f"\n{message} {suffix}: ").strip().lower()
        if not choice:
            return default
        return choice in ("y", "yes")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return False


def show_progress(message: str, current: int, total: int, width: int = 40) -> None:
    """Display progress bar"""
    if total == 0:
        return
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    print(f"\r  {message}: [{bar}] {pct * 100:5.1f}%", end="", flush=True)
    if current == total:
        print()


def display_info(title: str, lines: list[str]) -> None:
    """Display informational block"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")
    for line in lines:
        print(f"  {line}")
    print(f"{'=' * 60}\n")


def display_error(message: str) -> None:
    """Display error message"""
    print(f"\n  ERROR: {message}\n")


def display_success(message: str) -> None:
    """Display success message"""
    print(f"\n  SUCCESS: {message}\n")


def display_warning(message: str) -> None:
    """Display warning message"""
    print(f"\n  WARNING: {message}\n")
