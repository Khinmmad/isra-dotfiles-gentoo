# Gentoo Installer — Instalador Automático en Python

Instalador interactivo y automatizado para Gentoo Linux. Configuración completa desde particionado hasta escritorio, con soporte para perfiles YAML.

## Requisitos

- Python 3.11+
- Entorno live de Gentoo (o cualquier live Linux con herramientas base)
- Root (`sudo` o directo)
- Conexión a internet
- `simple-term-menu` (opcional, para menús TUI mejorados)

```bash
pip install simple-term-menu pyyaml
```

## Uso Rápido

### Modo Interactivo

```bash
# Como root desde un live environment
python3 main.py
```

Te guiará paso a paso:
1. Selección de disco
2. Particionado automático o manual
3. Descarga y extracción de stage3
4. Configuración de Portage
5. Instalación base en chroot
6. Kernel (genkernel / manual / binkernel)
7. Desktop Environment (KDE, GNOME, XFCE, Hyprland, Qtile)
8. Bootloader (GRUB, systemd-boot, rEFInd)
9. Usuarios, red, locale, timezone

### Desde Perfil YAML

```bash
python3 main.py --profile profiles/profile-desktop.yaml
```

## Estructura del Proyecto

```
script-de-instalacion-gentoo/
├── main.py                          # Entry point
├── profiles/
│   └── profile-desktop.yaml         # Perfil ejemplo (Hyprland + OpenRC)
├── gentoo_installer/
│   ├── installer.py                 # Orquestador principal
│   ├── core/
│   │   ├── disk.py                  # Particiones, formateo, montaje
│   │   ├── stage3.py                # Descarga y extracción stage3
│   │   ├── chroot.py                # Ejecución en chroot
│   │   ├── portage.py               # emerge, perfiles, make.conf
│   │   ├── fstab.py                 # Generación de fstab
│   │   ├── kernel.py                # genkernel / manual / binkernel
│   │   ├── bootloader.py            # GRUB / systemd-boot / rEFInd / Limine
│   │   ├── network.py               # DHCP, WiFi, NetworkManager
│   │   ├── timezone.py              # Locale, TZ, keymap, hwclock
│   │   ├── users.py                 # Creación de usuarios, sudo
│   │   └── desktop.py               # KDE, GNOME, XFCE, Hyprland, Qtile
│   ├── tui/
│   │   └── menus.py                 # Menús interactivos
│   ├── profiles/
│   │   └── loader.py                # Carga de perfiles YAML
│   └── utils/
│       └── validator.py             # Validación de inputs
├── tests/                           # Tests unitarios
└── scripts/                         # Scripts auxiliares (build ISO, test)
```

## Perfiles YAML

Los perfiles permiten instalación no interactiva. Ejemplo mínimo:

```yaml
hostname: "gentoo"
init_system: "openrc"
timezone: "America/Mexico_City"
locale: "es_MX.UTF-8"
keymap: "us"
target_disk: "nvme0n1"
efi: true
desktop: "hyprland"
kernel:
  type: "gentoo-sources"
  method: "genkernel"
  params: ["quiet", "splash", "nvidia-drm.modeset=1"]
users:
  - username: "isra"
    groups: ["wheel", "video", "audio"]
    shell: "/bin/zsh"
```

Ver `profiles/profile-desktop.yaml` para un ejemplo completo.

## Desktop Environments Soportados

| Desktop  | Paquete principal          | Display Manager |
|----------|----------------------------|-----------------|
| KDE      | kde-plasma/plasma-meta     | SDDM            |
| GNOME    | gnome-base/gnome           | GDM             |
| XFCE     | xfce-base/xfce4-meta       | SLiM            |
| Hyprland | dev-util/hyprland          | SDDM            |
| Qtile    | gui-wm/qtile               | SLiM            |

## Sistemas de Init

- **OpenRC** (default, recomendado)
- **systemd**

## Bootloaders

- **GRUB** (UEFI + BIOS)
- **systemd-boot** (UEFI)
- **rEFInd** (UEFI)
- **Limine** (manual config)

## Kernel

| Método       | Descripción                              |
|--------------|------------------------------------------|
| genkernel    | Automático, genera initramfs             |
| manual       | make menuconfig + compile (config custom) |
| binkernel    | gentoo-kernel-bin (precompilado)         |

## Tests

```bash
cd script-de-instalacion-gentoo
python3 -m pytest tests/ -v
```

## Sintaxis

```bash
python3 main.py --help
python3 main.py --verbose          # Debug output
python3 main.py --profile <path>   # Instalar desde perfil
python3 main.py                    # Modo interactivo
```

## Advertencias

⚠️ **Este script particiona y formatea discos. Úsalo con precaución.**
⚠️ **Requiere root. Si no estás seguro, revisa el código primero.**
⚠️ **No está probado en todas las configuraciones de hardware.**

## Licencia

MIT — mismo repo que los dotfiles (`isra-dotfiles-gentoo`).
