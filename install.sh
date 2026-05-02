#!/usr/bin/env bash
# ============================================
# Dotfiles Install Script - isra@gentoo
# OpenRC + Hyprland + Quickshell
# ============================================

DOTFILES_DIR=$(dirname $(readlink -f $0))
CONFIG_DIR="$HOME/.config"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ============================================
# PAQUETES PORTAGE (oficiales + overlays)
# ============================================
PORTAGE_PKGS=(
    # Sistema Base & Utilities
    media-video/pipewire media-video/wireplumber media-sound/pavucontrol
    media-sound/pamixer sys-auth/polkit sys-power/upower sys-fs/udisks
    net-misc/networkmanager net-wireless/bluez sys-power/brightnessctl
    media-sound/playerctl sys-fs/udiskie app-misc/jq
    media-gfx/imagemagick x11-misc/xdg-user-dirs
    x11-misc/xdg-desktop-portal-hyprland x11-libs/gtk:4
    x11-libs/qtwayland dev-qt/qtwayland media-libs/libnotify

    # Window Manager & Display
    gui-wm/hyprland gui-apps/hyprlock gui-apps/hypridle
    gui-apps/hyprpaper gui-apps/hyprpicker x11-misc/dunst
    x11-misc/rofi gui-apps/grim gui-apps/slurp
    gui-apps/wl-clipboard gui-apps/satty app-misc/cliphist
    x11-misc/wl-clip-persist gui-apps/hyprsunset

    # Theming & Fonts
    x11-misc/nwg-look x11-misc/qt5ct x11-misc/qt6ct
    x11-themes/kvantum x11-themes/kvantum-qt5
    media-fonts/noto-emoji media-fonts/nerdfonts
    media-fonts/jetbrains-mono

    # Aplicaciones & Shell
    www-client/firefox x11-terms/kitty xfce-base/thunar
    xfce-extra/thunar-archive-plugin xfce-extra/thunar-media-tags-plugin
    xfce-extra/tumbler media-video/ffmpegthumbnailer app-arch/unzip
    app-editors/vim x11-misc/wofi gui-apps/nwg-displays
    app-shells/fzf app-shells/zsh app-shells/oh-my-zsh
    app-shells/zsh-syntax-highlighting app-shells/zsh-autosuggestions
    app-misc/fastfetch app-misc/lsd app-misc/tree
    app-shells/zoxide dev-util/spicetify-cli

    # File Manager deps
    app-misc/fd sys-apps/ripgrep app-arch/p7zip media-libs/poppler
)

# Overlays necesarios
OVERLAYS=(
    "hyproverlay https://codeberg.org/hyprland-overlay/hyprland-overlay"
    "guru https://github.com/gentoo-mirror/guru"
)

# Source builds (no disponibles en Portage)
SOURCE_PKGS=(
    "awww"
    "quickshell"
    "sddm-sugar-candy"
    "tokyonight-gtk-theme"
    "grub2-theme-fallout"
    "bibata-cursor-theme"
    "eww"
)

# ============================================
# FUNCIONES DE INSTALACIÓN
# ============================================

check_root() {
    if [ "$(id -u)" -eq 0 ]; then
        log_error "NO ejecutar como root. Usa sudo dentro del script."
        exit 1
    fi
}

check_deps() {
    log_section "Verificando dependencias"
    for cmd in sudo emerge git curl; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd no encontrado. Instálalo primero."
            exit 1
        fi
    done
    log_success "Dependencias verificadas"
}

setup_overlays() {
    log_section "Configurando overlays"

    if ! command -v eselect &>/dev/null; then
        log_info "Instalando eselect-repository..."
        sudo emerge -q app-eselect/eselect-repository
    fi

    for overlay in "${OVERLAYS[@]}"; do
        name=$(echo "$overlay" | awk '{print $1}')
        if eselect repository list 2>/dev/null | grep -q "$name"; then
            log_info "Overlay $name ya existe, actualizando..."
            sudo emaint sync -r "$name" 2>/dev/null
        else
            log_info "Añadiendo overlay $name..."
            sudo eselect repository add "$name" git "$(echo "$overlay" | awk '{print $2}')"
            sudo emaint sync -r "$name" 2>/dev/null
        fi
    done

    # Aceptar keywords para paquetes de overlay
    sudo mkdir -p /etc/portage/package.accept_keywords
    echo "gui-wm/hyprland ~amd64" | sudo tee -a /etc/portage/package.accept_keywords/overlays
    echo "gui-apps/quickshell ~amd64" | sudo tee -a /etc/portage/package.accept_keywords/overlays

    log_success "Overlays configurados"
}

install_portage() {
    log_section "Instalando paquetes de Portage"
    if ! sudo emerge -q --jobs=$(nproc) "${PORTAGE_PKGS[@]}"; then
        log_error "Error instalando paquetes. Revisa el log de emerge."
        return 1
    fi
    log_success "Paquetes de Portage instalados"
}

build_source() {
    log_section "Compilando paquetes desde source"

    # --- awww (wallpaper daemon) ---
    if ! command -v awww &>/dev/null; then
        log_info "Compilando awww..."
        if ! command -v cargo &>/dev/null; then
            log_info "Instalando Rust toolchain..."
            sudo emerge -q dev-lang/rust
        fi
        if [ ! -d "/tmp/awww" ]; then
            git clone https://github.com/IsaacMarovitz/awww.git /tmp/awww
        fi
        cd /tmp/awww && cargo build --release 2>/dev/null
        sudo cp target/release/awww /usr/local/bin/
        cd -
        log_success "awww instalado"
    else
        log_info "awww ya instalado"
    fi

    # --- quickshell ---
    if ! command -v qs &>/dev/null; then
        log_info "Compilando quickshell..."
        sudo emerge -q dev-qt/qtbase[gui widgets network] dev-qt/qtdeclarative dev-qt/qtwayland cmake
        if [ ! -d "/tmp/quickshell" ]; then
            git clone https://github.com/outfoxxed/quickshell.git /tmp/quickshell
        fi
        cd /tmp/quickshell
        cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
        cmake --build build -j$(nproc)
        sudo cmake --install build
        cd -
        log_success "quickshell instalado"
    else
        log_info "quickshell ya instalado"
    fi

    # --- eww (ElKowar's Wacky Widgets) ---
    if ! command -v eww &>/dev/null; then
        log_info "Instalando eww desde GURU..."
        if eselect repository list 2>/dev/null | grep -q "guru"; then
            sudo emerge -q gui-apps/eww 2>/dev/null || {
                log_warn "eww falló desde Portage, compilando desde source..."
                if [ ! -d "/tmp/eww" ]; then
                    git clone https://github.com/elkowar/eww.git /tmp/eww
                fi
                cd /tmp/eww && cargo build --release --no-default-features --features x11,wayland 2>/dev/null
                sudo cp target/release/eww /usr/local/bin/
                cd -
            }
        fi
        log_success "eww instalado"
    else
        log_info "eww ya instalado"
    fi

    # --- sddm-sugar-candy theme ---
    if [ ! -d "/usr/share/sddm/themes/sugar-candy" ]; then
        log_info "Instalando sddm-sugar-candy..."
        sudo mkdir -p /usr/share/sddm/themes
        git clone https://github.com/Kangie/sddm-sugar-candy.git /tmp/sddm-sugar-candy
        sudo cp -r /tmp/sddm-sugar-candy /usr/share/sddm/themes/sugar-candy
        log_success "sddm-sugar-candy instalado"
    else
        log_info "sddm-sugar-candy ya instalado"
    fi

    # --- tokyonight-gtk-theme ---
    if [ ! -d "/usr/share/themes/Tokyonight" ] && [ ! -d "$HOME/.themes/Tokyonight" ]; then
        log_info "Instalando tokyonight-gtk-theme..."
        git clone https://github.com/Fausto-Korpsvart/Tokyo-Night-GTK-Theme.git /tmp/tokyonight-gtk
        cd /tmp/tokyonight-gtk
        sudo mkdir -p /usr/share/themes
        sudo cp -r src/Tokyonight* /usr/share/themes/ 2>/dev/null || \
            cp -r src/Tokyonight* "$HOME/.themes/" 2>/dev/null
        cd -
        log_success "tokyonight-gtk-theme instalado"
    else
        log_info "tokyonight-gtk-theme ya instalado"
    fi

    # --- grub2-theme-fallout ---
    if [ ! -d "/usr/share/grub/themes/fallout" ]; then
        log_info "Instalando grub2-theme-fallout..."
        git clone https://github.com/shvchk/fallout-grub-theme.git /tmp/fallout-grub
        cd /tmp/fallout-grub
        sudo mkdir -p /usr/share/grub/themes/fallout
        sudo cp -r . /usr/share/grub/themes/fallout/
        cd -
        log_success "grub2-theme-fallout instalado"
    else
        log_info "grub2-theme-fallout ya instalado"
    fi

    # --- bibata-cursor-theme ---
    if ! ls /usr/share/icons/Bibata* &>/dev/null; then
        log_info "Instalando bibata-cursor-theme..."
        if sudo emerge -q x11-themes/bibata-cursor-theme 2>/dev/null; then
            log_success "bibata-cursor-theme instalado desde Portage"
        else
            git clone https://github.com/fu7imus5/Bibata-Cursors.git /tmp/bibata
            cd /tmp/bibata
            sudo mkdir -p /usr/share/icons
            sudo cp -r Bibata-Modern-Ice /usr/share/icons/
            cd -
            log_success "bibata-cursor-theme instalado desde source"
        fi
    else
        log_info "bibata-cursor-theme ya instalado"
    fi
}

install_ohmyzsh() {
    log_section "Personalizando Shell (ZSH)"
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi
    if [ ! -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]; then
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
            "$HOME/.oh-my-zsh/custom/themes/powerlevel10k"
    fi
    log_success "Oh My Zsh + Powerlevel10k instalados"
}

copy_configs() {
    log_section "Sincronizando configuraciones"

    BACKUP_DIR="$HOME/.config-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    cd "$DOTFILES_DIR/configs"
    for dir in *; do
        if [ -d "$dir" ] && [ "$dir" != "grub" ]; then
            if [ -d "$CONFIG_DIR/$dir" ]; then
                cp -r "$CONFIG_DIR/$dir" "$BACKUP_DIR/"
            fi
            mkdir -p "$CONFIG_DIR"
            cp -r "$dir" "$CONFIG_DIR/"
            log_success "Config sincronizada: $dir"
        fi
    done
    cd -

    # ZSH files (fuera de .config)
    [ -f "$DOTFILES_DIR/configs/.zshrc" ] && cp "$DOTFILES_DIR/configs/.zshrc" "$HOME/.zshrc"
    [ -f "$DOTFILES_DIR/configs/.p10k.zsh" ] && cp "$DOTFILES_DIR/configs/.p10k.zsh" "$HOME/.p10k.zsh"

    log_success "Configs sincronizadas (backup en $BACKUP_DIR)"
}

copy_wallpapers() {
    log_section "Sincronizando Wallpapers"
    mkdir -p "$HOME/Pictures/wallpapers"
    if [ -d "$DOTFILES_DIR/wallpapers" ]; then
        cp "$DOTFILES_DIR/wallpapers/"* "$HOME/Pictures/wallpapers/"
        log_success "Wallpapers copiados"
    fi
}

setup_sddm() {
    log_section "Configurando SDDM"
    sudo mkdir -p /usr/share/sddm/themes/sugar-candy/backgrounds
    SDDM_WALL="$(ls "$HOME/Pictures/wallpapers/"*.png 2>/dev/null | head -1)"
    if [ -n "$SDDM_WALL" ]; then
        sudo cp "$SDDM_WALL" /usr/share/sddm/themes/sugar-candy/backgrounds/
    fi
    sudo mkdir -p /etc/sddm.conf.d
    sudo bash -c 'cat > /etc/sddm.conf.d/hyprland.conf << EOF
[Theme]
Current=sugar-candy
DisplayServer=wayland
CompositorCommand=Hyprland
EOF'
    log_success "SDDM configurado para Hyprland"
}

setup_services() {
    log_section "Habilitando Servicios (OpenRC)"
    sudo rc-update add dbus default
    sudo rc-update add elogind default
    sudo rc-update add display-manager default
    sudo rc-update add bluetooth default
    sudo rc-update add NetworkManager default
    log_success "Servicios habilitados (dbus, elogind, display-manager, bluetooth, NetworkManager)"
}

setup_shell() {
    log_section "Configurando ZSH como shell por defecto"
    if [[ "$SHELL" != *"zsh"* ]]; then
        sudo chsh -s /usr/bin/zsh "$(whoami)"
        log_success "ZSH configurado como shell por defecto"
    else
        log_info "ZSH ya es el shell por defecto"
    fi
}

# ============================================
# LÓGICA PRINCIPAL (MAIN)
# ============================================

echo -e "${CYAN}"
cat << 'EOF'
   ____        _    __ _ _           
  |  _ \  ___ | |_ / _(_) | ___  ___ 
  | | | |/ _ \| __| |_| | |/ _ \/ __|
  | |_| | (_) | |_|  _| | |  __/\__ \
  |____/ \___/ \__|_| |_|_|\___||___/
                                     
  isra@gentoo - Quickshell + Hyprland
EOF
echo -e "${NC}"

echo -e "${YELLOW}Este script instalará el setup completo de dotfiles para Gentoo/OpenRC.${NC}"
read -p "¿Deseas continuar con la instalación? [s/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    log_error "Instalación cancelada."
    exit 1
fi

check_root
check_deps
setup_overlays
install_portage
build_source
install_ohmyzsh
copy_configs
copy_wallpapers
setup_sddm
setup_services
setup_shell

log_section "TODO LISTO"
log_success "Instalación completada con éxito."
log_warn "Por favor, reinicia para entrar en tu nuevo entorno."
log_info "La barra (Quickshell) se iniciará automáticamente al entrar en Hyprland."
log_info "Recuerda: GRUB se gestiona desde Arch en tu triple boot."
