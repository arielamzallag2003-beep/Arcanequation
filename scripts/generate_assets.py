from __future__ import annotations

import os
import struct
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


def write_bmp(path: Path, width: int, height: int, rgb_pixels: list[tuple[int, int, int]]) -> None:
    row_padding = (4 - (width * 3) % 4) % 4
    pixel_data = bytearray()

    for y in range(height - 1, -1, -1):
        for x in range(width):
            r, g, b = rgb_pixels[y * width + x]
            pixel_data.extend((b, g, r))
        pixel_data.extend(b"\x00" * row_padding)

    file_size = 54 + len(pixel_data)

    with path.open("wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(b"\x00\x00\x00\x00")
        f.write(struct.pack("<I", 54))

        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", width))
        f.write(struct.pack("<i", height))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", 24))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", len(pixel_data)))
        f.write(struct.pack("<I", 2835))
        f.write(struct.pack("<I", 2835))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", 0))

        f.write(pixel_data)


def make_player_sprite(size: int = 64) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    center = size / 2
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < size * 0.35:
                glow = max(0.0, 1.0 - dist / (size * 0.35))
                pixels.append((int(90 + 120 * glow), int(130 + 90 * glow), 255))
            else:
                pixels.append((18, 12, 40))
    return pixels


def make_enemy_sprite(size: int = 80) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    center = size / 2
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < size * 0.4:
                t = max(0.0, 1.0 - dist / (size * 0.4))
                pixels.append((255, int(30 + t * 90), int(110 + t * 120)))
            else:
                pixels.append((18, 12, 40))
    return pixels


def make_floor_texture(width: int = 320, height: int = 180) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    for y in range(height):
        for x in range(width):
            wave = int(8 * (1 + ((x * 0.17 + y * 0.09) % 3)))
            base = 18 + wave
            pixels.append((base, 14 + wave // 2, 40 + wave * 2))
    return pixels


def main() -> None:
    os.makedirs(ASSET_DIR, exist_ok=True)
    write_bmp(ASSET_DIR / "mage.bmp", 64, 64, make_player_sprite())
    write_bmp(ASSET_DIR / "void_lord.bmp", 80, 80, make_enemy_sprite())
    write_bmp(ASSET_DIR / "arcane_floor.bmp", 320, 180, make_floor_texture())


if __name__ == "__main__":
    main()
