#!/bin/bash
case $1 in
  get)
    pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+%' | head -1 | tr -d '%'
    ;;
  set)
    pactl set-sink-volume @DEFAULT_SINK@ "$2%"
    ;;
  mute)
    pactl set-sink-mute @DEFAULT_SINK@ toggle
    ;;
  devices)
    pactl list sinks short | awk '{print $2}'
    ;;
esac

