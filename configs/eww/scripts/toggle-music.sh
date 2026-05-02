#!/bin/bash
if eww active-windows | grep -q "music-widget"; then
  eww close music-widget
else
  eww open music-widget
fi