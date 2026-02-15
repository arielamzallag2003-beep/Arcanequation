from __future__ import annotations

import os
import struct
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


def write_bmp(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    pad = (4 - (width * 3) % 4) % 4
    px = bytearray()
    for y in range(height - 1, -1, -1):
        for x in range(width):
            r, g, b = pixels[y * width + x]
            px.extend((b, g, r))
        px.extend(b"\x00" * pad)

    with path.open("wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", 54 + len(px)))
        f.write(b"\x00\x00\x00\x00")
        f.write(struct.pack("<I", 54))
        f.write(struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(px), 2835, 2835, 0, 0))
        f.write(px)


def sprite(size: int, core: tuple[int, int, int], aura: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    out = []
    c = size / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            d = (dx * dx + dy * dy) ** 0.5
            if d < size * 0.35:
                t = 1 - d / (size * 0.35)
                out.append(tuple(min(255, int(core[i] + aura[i] * t)) for i in range(3)))
            else:
                out.append((12, 10, 30))
    return out


def floor_tex(w: int, h: int) -> list[tuple[int, int, int]]:
    out = []
    for y in range(h):
        for x in range(w):
            n = int(12 * (1 + math_sin(x * 0.1 + y * 0.05)))
            out.append((18 + n, 14 + n // 2, 44 + n * 2))
    return out


def math_sin(v: float) -> float:
    import math

    return math.sin(v)


def main() -> None:
    os.makedirs(ASSET_DIR, exist_ok=True)
    write_bmp(ASSET_DIR / "mage.bmp", 64, 64, sprite(64, (90, 140, 255), (100, 90, 40)))
    write_bmp(ASSET_DIR / "archmage.bmp", 82, 82, sprite(82, (255, 80, 180), (0, 110, 90)))
    write_bmp(ASSET_DIR / "arcane_floor.bmp", 320, 180, floor_tex(320, 180))


if __name__ == "__main__":
    main()
