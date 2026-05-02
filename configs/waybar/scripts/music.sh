#!/bin/bash
player_status=$(playerctl status 2>/dev/null)

if [ "$player_status" = "Playing" ]; then
    artist=$(playerctl metadata artist 2>/dev/null | head -c 20)
    title=$(playerctl metadata title 2>/dev/null | head -c 25)
    echo "󰝚 $artist - $title"
elif [ "$player_status" = "Paused" ]; then
    artist=$(playerctl metadata artist 2>/dev/null | head -c 20)
    title=$(playerctl metadata title 2>/dev/null | head -c 25)
    echo "󰏤 $artist - $title"
else
    echo "󰝛 No music"
fi