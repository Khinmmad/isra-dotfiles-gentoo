#!/bin/bash
if eww active-windows | grep -q "sidebar-widget"; then
  eww close sidebar-widget
else
  eww open sidebar-widget
fi