#!/bin/bash
if eww active-windows | grep -q "volume-widget"; then
  eww close volume-widget
else
  eww open volume-widget
fi
