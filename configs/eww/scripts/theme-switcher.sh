#!/bin/bash
case $1 in
  gtk-catppuccin)
    gsettings set org.gnome.desktop.interface gtk-theme "catppuccin-mocha-peach-standard"
    ;;
  gtk-tokyo)
    gsettings set org.gnome.desktop.interface gtk-theme "Tokyonight-Dark"
    ;;
  rofi-type6)
    sed -i 's|exec.*launcher.*\.sh|exec bash ~/.config/rofi/launchers/type-6/launcher.sh|' ~/.config/hypr/hyprland.conf
    ;;
  rofi-type7)
    sed -i 's|exec.*launcher.*\.sh|exec bash ~/.config/rofi/launchers/type-7/launcher.sh|' ~/.config/hypr/hyprland.conf
    ;;
  wallpaper)
    bash ~/.config/swww/change_wallpaper.sh --select
    ;;
esac