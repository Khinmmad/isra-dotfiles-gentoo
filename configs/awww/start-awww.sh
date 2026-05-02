#!/bin/bash
awww-daemon &
sleep 1
# Usa el primer wallpaper disponible en ~/Pictures/wallpapers/
WALLPAPER=$(ls "$HOME/Pictures/wallpapers/"*.png 2>/dev/null | head -1)
if [ -n "$WALLPAPER" ]; then
    awww img "$WALLPAPER" --transition-type grow --transition-duration 1
fi

