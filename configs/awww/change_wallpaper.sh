#!/bin/bash
WALLPAPER_DIR="$HOME/Pictures/wallpapers"
TRANSITION_TYPE="outer"
TRANSITION_POS="1,1"
TRANSITION_DURATION="2"
TRANSITION_FPS="60"

# Función para cambiar wallpaper
set_wallpaper() {
    awww img "$1" \
        --transition-type "$TRANSITION_TYPE" \
        --transition-pos "$TRANSITION_POS" \
        --transition-duration "$TRANSITION_DURATION" \
        --transition-fps "$TRANSITION_FPS" \
        --transition-angle 45
    echo "$1" > "$HOME/.cache/current_wallpaper"
}

# Modo selector con rofi
if [ "$1" == "--select" ]; then
    SELECTED=$(ls "$WALLPAPER_DIR"/*.png "$WALLPAPER_DIR"/*.jpg 2>/dev/null \
        | while read -r img; do
            name=$(basename "$img" | sed 's/\.[^.]*$//' | sed 's/wallhaven-//')
            echo -en "$name\0icon\x1f$img\n"
          done \
        | rofi -dmenu \
               -i \
               -p "🖼 Wallpaper" \
               -show-icons \
               -icon-theme "hicolor" \
               -theme ~/.config/rofi/launchers/type-6/style-1.rasi \
               -theme-str 'element-icon { size: 80px; }
                           listview { columns: 2; lines: 4; }
                           window { width: 900px; }')

    if [ -n "$SELECTED" ]; then
        # Reconstruir nombre completo
        FILE=$(ls "$WALLPAPER_DIR"/*.png "$WALLPAPER_DIR"/*.jpg 2>/dev/null \
            | grep "$(echo "$SELECTED" | sed 's/-/_/g')\|$SELECTED")
        [ -z "$FILE" ] && FILE=$(ls "$WALLPAPER_DIR"/*"$SELECTED"* 2>/dev/null | head -1)
        [ -n "$FILE" ] && set_wallpaper "$FILE"
    fi
    exit 0
fi

# Modo siguiente wallpaper (comportamiento original)
STATE_FILE="$HOME/.cache/current_wallpaper_index"
TOTAL=$(ls "$WALLPAPER_DIR"/*.png "$WALLPAPER_DIR"/*.jpg 2>/dev/null | wc -l)

[ "$TOTAL" -eq 0 ] && exit 1

INDEX=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
NEXT_INDEX=$(( (INDEX + 1) % TOTAL ))
FILE=$(ls "$WALLPAPER_DIR"/*.png "$WALLPAPER_DIR"/*.jpg | sed -n "$((NEXT_INDEX + 1))p")

set_wallpaper "$FILE"
echo "$NEXT_INDEX" > "$STATE_FILE"
