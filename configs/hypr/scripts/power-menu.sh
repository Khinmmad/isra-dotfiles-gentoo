#!/bin/bash

option=$(printf "⏻ Shutdown\n↻ Reboot\n🔒 Lock\n🌙 Suspend\n🚪 Logout" | wofi --dmenu)

case "$option" in
    "⏻ Shutdown")
        poweroff
        ;;
    "↻ Reboot")
        reboot
        ;;
    "🔒 Lock")
        hyprlock
        ;;
    "🌙 Suspend")
        systemctl suspend 2>/dev/null || pm-suspend || echo mem | sudo tee /sys/power/state
        ;;
    "🚪 Logout")
        hyprctl dispatch exit
        ;;
esac
