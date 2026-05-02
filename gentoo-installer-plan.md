# Gentoo Installer — Plan de Proyecto

## Visión
Installer interactivo tipo `archinstall` para Gentoo Linux con TUI, perfiles desktop, soporte OpenRC/systemd y distribución como ISO live.

---

## Lenguaje y Stack

| Componente | Tecnología |
|---|---|
| **Lenguaje principal** | Python 3.11+ |
| **TUI** | `simple-term-menu` (menús) + `rich` (progreso, tablas) |
| **Config de perfiles** | YAML (`pyyaml`) |
| **Logging** | Python `logging` + output a `/var/log/gentoo-installer.log` |
| **Empaquetado** | `pyproject.toml`, script ejecutable `gentoo-installer` |
| **Distribución** | ISO live basada en Gentoo con Python + deps preinstalados |

---

## Estructura del Proyecto

```
gentoo-installer/
├── pyproject.toml                          # Build config, deps, entry point
├── README.md                               # Doc principal
├── LICENSE                                 # GPL-3.0
│
├── gentoo_installer/
│   ├── __init__.py
│   ├── __main__.py                         # python -m gentoo_installer
│   └── main.py                             # Entry point, orchestration
│
│   ├── tui/                                # Capa de interfaz
│   │   ├── __init__.py
│   │   ├── app.py                          # TUI principal, loop de navegación
│   │   ├── menus.py                        # Definición de cada pantalla
│   │   ├── prompts.py                      # Inputs: texto, selects, confirm
│   │   ├── progress.py                     # Progress bars, step indicators
│   │   └── utils.py                        # Colores, clear, formatters
│
│   ├── core/                               # Lógica de instalación
│   │   ├── __init__.py
│   │   ├── disk.py                         # Particionado (parted/gdisk), formateo, mount
│   │   ├── stage3.py                       # Download stage3 tarball, extract
│   │   ├── chroot.py                       # Ejecutar cmds en /mnt/gentoo
│   │   ├── portage.py                      # make.conf, make.profile, emerge
│   │   ├── fstab.py                        # Generar /etc/fstab
│   │   ├── kernel.py                       # genkernel, modules, firmware
│   │   ├── bootloader.py                   # GRUB install/config (UEFI/BIOS)
│   │   ├── network.py                      | # Hostname, WiFi, netifrc/NetworkManager
│   │   ├── timezone.py                     | # Timezone, locale, hwclock
│   │   └── users.py                        # Root passwd, user creation, sudo
│
│   ├── profiles/                           # Perfiles desktop
│   │   ├── __init__.py
│   │   ├── base.yaml                       # Sistema mínimo
│   │   ├── hyprland.yaml                   # Hyprland + SDDM + pipewire + bluez
│   │   └── loader.py                       # Parser YAML + validación
│
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                     # Global settings, paths, defaults
│   │   └── validation.py                   # Validar inputs del usuario
│
│   └── utils/
│       ├── __init__.py
│       ├── run.py                          # subprocess wrapper + logging
│       ├── mirrors.py                      # Mirror selection (fastest)
│       └── hardware.py                     # Detect CPU, GPU, disk, UEFI/BIOS
│
├── scripts/
│   ├── build-iso.sh                        # Construir ISO live
│   └── test-chroot.sh                      # Helper para testing en chroot
│
└── tests/
    ├── conftest.py
    ├── test_disk.py
    ├── test_portage.py
    └── test_profiles.py
```

---

## Flujo de Instalación (pantallas TUI)

```
┌─────────────────────────────────┐
│   Gentoo Installer v0.1.0       │
├─────────────────────────────────┤
│  1. Keyboard Layout             │
│  2. Disk Configuration          │
│  3. Filesystem Selection        │
│  4. Mirror Selection            │
│  5. Profile Selection           │
│  6. Init System                 │
│  7. Kernel Options              │
│  8. Bootloader                  │
│  9. Network Configuration       │
│ 10. Timezone & Locale           │
│ 11. User Setup                  │
│ 12. Review & Install            │
│ 13. Exit                        │
└─────────────────────────────────┘
```

### Paso a paso

#### 1. Keyboard Layout
- Lista de keymaps (`localectl list-keymaps` o desde `/usr/share/keymaps`)
- Aplicar con `loadkeys`
- Preview de teclas especiales

#### 2. Disk Configuration
**Modo guiado:**
- Detectar todos los discos (`lsblk`, `blockdev`)
- Seleccionar disco target
- Opciones:
  - **Full disk** (borra todo, tabla GPT)
  - **Dual boot** (usa espacio libre existente)

**Esquema de particionado (UEFI):**
```
/dev/nvme0n1p1  EFI System       512MB   → /boot/efi (FAT32)
/dev/nvme0n1p2  Linux filesystem rest     → / (ext4/btrfs/xfs)
/dev/nvme0n1p3  Linux swap       RAM+2G  → swap
```

**Esquema de particionado (BIOS/MBR):**
```
/dev/sda1  Linux boot   1GB   → /boot (ext2)
/dev/sda2  Linux root   rest  → / (ext4/btrfs/xfs)
/dev/sda3  Linux swap   RAM+2G → swap
```

**Modo manual:**
- Usuario define particiones, tamaños, mount points
- Validación antes de proceder

#### 3. Filesystem
- ext4 (default, más estable)
- btrfs (compresión zstd, snapshots)
- xfs (alto rendimiento, good para HDDs grandes)

#### 4. Mirror Selection
- Fetch mirrors desde `https://www.gentoo.org/downloads/mirrors/`
- Test de velocidad (download small file)
- Opción manual (input URL)

#### 5. Profile Selection
- **Base system** — solo stage3 + sistema mínimo
- **Desktop** — X11, desktop environment genérico
- **Hyprland** — Wayland, Hyprland, SDDM, pipewire, bluez, firefox, kitty, wofi
- **Server** — sshd, fail2ban, sin GUI

Cada perfil define en YAML:
```yaml
name: "Hyprland Desktop"
description: "Wayland compositor + utilities"
packages:
  - "wayland"
  - "wayland-protocols"
  - "hyprland"
  - "sddm"
  - "pipewire"
  - "wireplumber"
  - "bluez"
  - "firefox"
  - "kitty"
  - "wofi"
services:
  - "dbus"
  - "elogind"      # OpenRC
  - "display-manager"
use_flags:
  "media-video/pipewire": "alsa wayland"
  "www-client/firefox": "wayland"
  "sys-auth/elogind": ""
post_install: |
  # Scripts post-emerge (ej: añadir usuario a grupos)
```

#### 6. Init System
- **OpenRC** — más simple, nativo Gentoo, tu setup actual
- **systemd** — estándar de facto, más deps
- El perfil YAML adapta servicios y paquetes según esta elección

#### 7. Kernel
- **genkernel** (recommended) — auto-detect, initramfs, fácil
- **Manual config** — usuario elige opciones avanzadas (expert mode)
- Opciones:
  - Incluir firmware (`linux-firmware`)
  - Módulos NVIDIA/AMD
  - Microcode CPU

#### 8. Bootloader
- **GRUB** — soporta UEFI + BIOS, multi-boot
- Detección automática de UEFI (`/sys/firmware/efi`)
- Configuración:
  - `GRUB_PLATFORMS="efi-64"` o `"pc"`
  - `os-prober` para detectar otros OSs
  - Kernel parameters (nvidia-drm.modeset, etc.)

#### 9. Network
- **Hostname** — input libre
- **WiFi** — detectar interfaces, escanear redes, input WPA passphrase
- **Ethernet** — DHCP por defecto
- Servicio según init:
  - OpenRC: `dhcpcd` o `netifrc`
  - systemd: `systemd-networkd` o `NetworkManager`

#### 10. Timezone & Locale
- Timezone: selector por región/ciudad
- Locale: `en_US.UTF-8`, `es_ES.UTF-8`, etc.
- `hwclock --systohc`

#### 11. User Setup
- Root password (x2 confirmación)
- Crear usuario normal:
  - Username
  - Password
  - Grupos: `wheel`, `video`, `audio`, `users`
- Configurar sudo (`visudo` con wheel NOPASSWD opcional)

#### 12. Review & Install
**Resumen final:**
```
Disk:       /dev/nvme0n1 (full erase)
EFI:        /dev/nvme0n1p1  512MB  FAT32
Root:       /dev/nvme0n1p2  476GB  ext4
Swap:       /dev/nvme0n1p3  34GB   swap
Profile:    Hyprland Desktop
Init:       OpenRC
Kernel:     genkernel (linux-firmware)
Bootloader: GRUB (UEFI)
Hostname:   gentoo
User:       isra (wheel, video)
```

- Confirmación explícita (⚠️ destruye datos en el disco)
- Progreso paso a paso con ETA
- Log en tiempo real

---

## Módulos Core — Detalle Técnico

### `core/disk.py`
```python
def detect_disks() -> list[Disk]
def create_partitions(disk: Disk, scheme: PartitionScheme) -> None
    # Usa parted (MBR) o gdisk (GPT)
def format_partition(partition: Partition, fs: Filesystem) -> None
def mount_root(root_part: Partition, mount_point: Path) -> None
def mount_efi(efi_part: Partition) -> Path
```

### `core/stage3.py`
```python
def fetch_stage3_list(mirror: str) -> list[Stage3Info]
    # Parsea HTML del mirror, extrae tarballs disponibles
def download_stage3(stage3: Stage3Info, dest: Path) -> Path
def extract_stage3(tarball: Path, root: Path) -> None
    # tar xpf --xattrs-include='*.*' --numeric-owner
```

### `core/chroot.py`
```python
def setup_chroot(root: Path) -> None
    # mount --bind /dev, /proc, /sys, /run
def chroot_run(root: Path, cmd: str, **kwargs) -> ProcessResult
def cleanup_chroot(root: Path) -> None
```

### `core/portage.py`
```python
def write_make_conf(root: Path, config: MakeConf) -> None
    # CFLAGS, CXXFLAGS, MAKEOPTS, USE, VIDEO_CARDS, GRUB_PLATFORMS
def set_profile(root: Path, profile: str) -> None
    # eselect profile set
def emerge(root: Path, packages: list[str], flags: dict) -> None
    # emerge --ask=n --verbose
```

### `core/bootloader.py`
```python
def install_grub(root: Path, disk: str, efi: bool) -> None
def configure_grub(root: Path, kernel_params: list[str]) -> None
def generate_grub_cfg(root: Path) -> None
```

### `core/users.py`
```python
def set_root_password(root: Path, password: str) -> None
def create_user(root: Path, username: str, groups: list[str]) -> None
def set_user_password(root: Path, username: str, password: str) -> None
def configure_sudo(root: Path, nopasswd: bool = True) -> None
```

---

## Perfil YAML — Esquema Completo

```yaml
name: "Hyprland"
description: "Wayland compositor with utilities"
min_ram: "8G"
requires: ["wayland"]

# Perfiles Portage base
base_profile: "default/linux/amd64/23.0/desktop"

# Paquetes a emergir
packages:
  global:
    - "wayland"
    - "wayland-protocols"
    - "hyprland"
    - "sddm"
    - "pipewire"
    - "wireplumber"
    - "rtkit"
    - "bluez"
    - "bluez-utils"
    - "firefox"
    - "kitty"
    - "wofi"
    - "waybar"
    - "hyprpaper"
    - "hyprlock"
    - "hypridle"

# USE flags por paquete
use_flags:
  "media-video/pipewire": "alsa wayland"
  "www-client/firefox": "wayland"
  "x11-base/xorg-server": "wayland"

# Servicios OpenRC
services_openrc:
  - "dbus"
  - "elogind"
  - "display-manager"

# Servicios systemd
services_systemd:
  - "dbus"
  - "display-manager"

# Grupos de usuario extra
user_groups:
  - "video"
  - "audio"

# Variables de entorno
env_vars:
  GBM_BACKEND: "nvidia-drm"
  __GLX_VENDOR_LIBRARY_NAME: "nvidia"
  WLR_NO_HARDWARE_CURSORS: "1"

# Scripts post-instalación
post_install: |
  # Añadir usuario al grupo video
  gpasswd -a $USERNAME video
  # Configurar Hyprland autostart si aplica
  mkdir -p /home/$USERNAME/.config/hypr
```

---

## ISO Build — `scripts/build-iso.sh`

### Opción A: Basada en Gentoo live oficial
```bash
# 1. Descargar Gentoo admin CD
# 2. Chroot
# 3. Instalar Python 3.11+
# 4. pip install simple-term-menu rich pyyaml
# 5. Instalar gentoo-installer
# 6. Configurar auto-start en /etc/profile.d/ o initramfs
# 7. Reconstruir ISO
```

### Opción B: Basada en SystemRescue o Arch ISO
```bash
# Usar ISO existente con Python
# Descargar stage3 + script gentoo-installer al boot
# Auto-lanzar si no hay argumentos
```

### Opción C (Recomendada para v1): Script descargable
```bash
# No ISO propia inicialmente
# El usuario bota con cualquier live con Python 3
# curl -sL https://... | bash  # o download + chmod +x
```

---

## Dependencias del Sistema (fuera de Python)

El live environment debe tener:
- `parted` / `gdisk` — particionado
- `e2fsprogs`, `btrfs-progs`, `xfsprogs` — formateo
- `tar`, `xz` — extract stage3
- `wget` / `curl` — downloads
- `grub` — bootloader
- `genkernel` — kernel
- `dialog` — si se usa como fallback TUI
- Python 3.11+ con:
  - `simple-term-menu`
  - `rich`
  - `pyyaml`

---

## Manejo de Errores y Logging

### Logging
```python
# Todo va a /var/log/gentoo-installer.log
# TUI muestra solo info relevante
# Errores críticos → pantalla roja con opción de retry/abort
```

### Recovery
- Si falla en mitad de la instalación:
  - Log indica exactamente qué paso falló
  - Opción de reintentar desde el paso fallido
  - Opción de abortar y limpiar mounts
- `umount -R /mnt/gentoo` al abortar

---

## Testing

### Unit tests
- `test_disk.py` — particionado, validación
- `test_portage.py` — make.conf generation, profile selection
- `test_profiles.py` — YAML parsing, validation

### Integration tests
- `test-chroot.sh` — ejecutar en VM con chroot
- QEMU test: boot ISO, instalar en disco virtual, verificar boot

### CI/CD (futuro)
- GitHub Actions: lint (ruff), typecheck (mypy), tests
- VM testing automatizado

---

## Roadmap

### Fase 1 — Core (semanas 1-2)
- [ ] Estructura del proyecto
- [ ] TUI base con navegación
- [ ] Disk partitioning (guided)
- [ ] Stage3 download & extract
- [ ] Chroot setup

### Fase 2 — Sistema base (semanas 3-4)
- [ ] make.conf generation
- [ ] Profile selection (Portage)
- [ ] emerge base system
- [ ] fstab generation
- [ ] Timezone, locale
- [ ] Kernel (genkernel)
- [ ] GRUB (UEFI + BIOS)
- [ ] Root password, user creation

### Fase 3 — Perfiles (semanas 5-6)
- [ ] Profile YAML parser
- [ ] Hyprland profile
- [ ] Desktop profile
- [ ] Service management (OpenRC + systemd)

### Fase 4 — ISO y distribución (semana 7)
- [ ] Build ISO script
- [ ] Testing en QEMU
- [ ] Documentación

### Fase 5 — Extras (semanas 8+)
- [ ] Manual partitioning
- [ ] Btrfs snapshots setup
- [ ] LUKS encryption
- [ ] LVM support
- [ ] Network bonding/bridging
- [ ] Más perfiles (KDE, GNOME, server)

---

## Notas de tu Setup Actual (referencia)

Tu sistema Gentoo funciona como perfil de referencia para Hyprland:
- OpenRC + elogind + dbus
- Kernel 6.18.25-gentoo sin initramfs (para v1 usar genkernel con initramfs)
- nvidia-drivers + mesa
- Hyprland 0.54.3 + SDDM + pipewire
- GRUB desde Arch (multi-boot)

Estas configs servirán como template para el perfil Hyprland del installer.
