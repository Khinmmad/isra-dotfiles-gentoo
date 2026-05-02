#!/usr/bin/env python3
"""Genera una textura CRT vintage: ruido ámbar + scanlines + viñeta + esquinas redondeadas."""
import struct, zlib, random, math

W, H = 1920, 1080
CORNER_R = 80          # radio de esquinas redondeadas
OUT = "/home/isra/.config/kitty/crt_bg.png"

def png_chunk(tag, data):
    c = tag + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

rng = random.Random(1337)
rows = []

# Pre-calcula tabla de ruido para velocidad
NOISE_TABLE = [rng.randint(-30, 30) for _ in range(W * H)]

for y in range(H):
    row = bytearray()
    row.append(0)  # filtro PNG: None

    cy = (y - H / 2) / (H / 2)          # coord normalizada vertical
    scanline = 0.72 if y % 2 == 0 else 1.0  # scanlines: líneas pares más oscuras

    for x in range(W):
        # ── Esquinas redondeadas: píxeles fuera del área = negro puro ──
        in_corner = False
        for (cx0, cy0) in [(CORNER_R, CORNER_R), (W-CORNER_R, CORNER_R),
                           (CORNER_R, H-CORNER_R), (W-CORNER_R, H-CORNER_R)]:
            dx, dy = x - cx0, y - cy0
            # cuadrante de la esquina
            qx = (x < CORNER_R and cx0 == CORNER_R) or (x >= W-CORNER_R and cx0 == W-CORNER_R)
            qy = (y < CORNER_R and cy0 == CORNER_R) or (y >= H-CORNER_R and cy0 == H-CORNER_R)
            if qx and qy and dx*dx + dy*dy > CORNER_R*CORNER_R:
                in_corner = True
                break

        if in_corner:
            row += b'\x00\x00\x00'
            continue

        # ── Viñeta radial (esquinas más oscuras) ──
        vx = (x - W / 2) / (W / 2)
        vignette = max(0.0, 1.0 - (vx*vx + cy*cy) * 0.75)
        vignette = vignette ** 0.6  # curva suave

        # ── Ruido de grano ──
        n = NOISE_TABLE[y * W + x]

        # ── Color base ámbar #0c0800 + ruido ──
        r = 12 + int(n * 1.4)
        g =  8 + int(n * 0.9)
        b =  0 + int(n * 0.2)

        # Aplica viñeta y scanline
        factor = vignette * scanline
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))

        row += bytes([r, g, b])

    rows.append(bytes(row))

raw = b"".join(rows)
compressed = zlib.compress(raw, 1)  # nivel 1 = rápido

sig  = b'\x89PNG\r\n\x1a\n'
ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
idat = png_chunk(b'IDAT', compressed)
iend = png_chunk(b'IEND', b'')

with open(OUT, 'wb') as f:
    f.write(sig + ihdr + idat + iend)

print(f"Generado: {OUT}  ({W}x{H})")
