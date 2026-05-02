#!/bin/bash
case $1 in
  title)
    playerctl metadata title 2>/dev/null || echo "No music"
    ;;
  artist)
    playerctl metadata artist 2>/dev/null || echo "Unknown"
    ;;
  status)
    playerctl status 2>/dev/null || echo "Stopped"
    ;;
  position)
    playerctl position 2>/dev/null || echo "0"
    ;;
  length)
    playerctl metadata mpris:length 2>/dev/null | awk '{printf "%d", $1/1000000}' || echo "0"
    ;;
  progress)
    pos=$(playerctl position 2>/dev/null || echo "0")
    len=$(playerctl metadata mpris:length 2>/dev/null | awk '{printf "%d", $1/1000000}' || echo "1")
    echo "$pos $len" | awk '{printf "%d", ($1/$2)*100}'
    ;;
  cover)
    url=$(playerctl metadata mpris:artUrl 2>/dev/null)
    if [[ $url == file://* ]]; then
      echo "${url#file://}"
    else
      echo "/tmp/cover.png"
      curl -s "$url" -o /tmp/cover.png 2>/dev/null
    fi
    ;;
  volume)
    pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+%' | head -1 | tr -d '%'
    ;;
esac