"""
signal_siphon.py — Signal Siphon Spire Builder (v6 High-Density Greeble Specification).

An asymmetric, needle-like communications & energy siphon spire featuring:
- Fluted stepped foundation plinth with crying obsidian dampeners
- Cantilevered telemetry pods projecting outward at intervals
- Suspended conduit cascades (deepslate tile walls, chains, hoppers)
- High-altitude lightning rod arrays and pearlescent froglight pulse nodes
"""

import math
import mcschematic
from .primitives import cuboid_filled, flat_plane, line_y, circle_xz, fluted_pillar_3x3, greeble_conduit_run

def build_signal_siphon(schem: mcschematic.MCSchematic, prompt: dict):
    dims = prompt.get("dimensions", {})
    w = max(18, dims.get("width", 22))
    h = max(28, dims.get("height", 45))
    l = max(18, dims.get("length", 22))

    cx = w // 2
    cz = l // 2

    # 1. Foundation Base Plinth (Y=0..3)
    # Heavy industrial plinth tapering inward
    flat_plane(schem, 1, 0, 1, w - 2, l - 2, "minecraft:crying_obsidian")
    flat_plane(schem, 2, 1, 2, w - 3, l - 3, "minecraft:polished_blackstone_bricks")
    flat_plane(schem, 3, 2, 3, w - 4, l - 4, "minecraft:polished_deepslate_bricks")

    # Corner power dampener pylons
    pylons = [(2, 2), (2, l - 3), (w - 3, 2), (w - 3, l - 3)]
    for px, pz in pylons:
        for py in range(1, 6):
            schem.setBlock((px, py, pz), "minecraft:purpur_pillar[axis=y]")
        schem.setBlock((px, 6, pz), "minecraft:pearlescent_froglight")
        schem.setBlock((px, 7, pz), "minecraft:copper_grate")

    # 2. Central Fluted Spire Core (Y=3..H-10)
    core_r = max(3, min(w, l) // 4)
    for y in range(3, h - 8):
        # Asymmetric structural taper
        curr_r = core_r if y < h // 2 else max(2, core_r - 1)
        circle_xz(schem, cx, y, cz, curr_r, "minecraft:polished_deepslate_bricks", filled=False)
        # Inner energy conduit core
        schem.setBlock((cx, y, cz), "minecraft:crying_obsidian")

        # Vertical fluting ribs along cardinal axes
        schem.setBlock((cx + curr_r, y, cz), "minecraft:purpur_pillar[axis=y]")
        schem.setBlock((cx - curr_r, y, cz), "minecraft:purpur_pillar[axis=y]")
        schem.setBlock((cx, y, cz + curr_r), "minecraft:purpur_pillar[axis=y]")
        schem.setBlock((cx, y, cz - curr_r), "minecraft:purpur_pillar[axis=y]")

    # 3. Cantilevered Telemetry Pods (Asymmetric Outcroppings)
    # Mid-level sensor outcropping to the East
    pod_y1 = h // 3
    for dx in range(curr_r, curr_r + 4):
        schem.setBlock((cx + dx, pod_y1, cz), "minecraft:dark_prismarine")
        schem.setBlock((cx + dx, pod_y1 - 1, cz), "minecraft:warped_fence")
    # Observation / Siphon glass chamber
    schem.setBlock((cx + curr_r + 3, pod_y1 + 1, cz), "minecraft:pearlescent_froglight")
    schem.setBlock((cx + curr_r + 3, pod_y1 + 2, cz), "minecraft:tinted_glass")
    schem.setBlock((cx + curr_r + 4, pod_y1 + 1, cz), "minecraft:lightning_rod[facing=east]")

    # Upper-level sensor outcropping to the West/North
    pod_y2 = (2 * h) // 3
    for dz in range(curr_r, curr_r + 4):
        schem.setBlock((cx - 1, pod_y2, cz - dz), "minecraft:dark_prismarine")
        schem.setBlock((cx - 1, pod_y2 - 1, cz - dz), "minecraft:deepslate_tile_wall")
    schem.setBlock((cx - 1, pod_y2 + 1, cz - curr_r - 3), "minecraft:sea_lantern")
    schem.setBlock((cx - 1, pod_y2 + 2, cz - curr_r - 3), "minecraft:hopper[facing=down]")

    # 4. Siphon Apex Needle (Y=H-8..H)
    needle_base_y = h - 8
    for ny in range(needle_base_y, h - 3):
        schem.setBlock((cx, ny, cz), "minecraft:chiseled_tuff")
        schem.setBlock((cx + 1, ny, cz), "minecraft:iron_bars")
        schem.setBlock((cx - 1, ny, cz), "minecraft:iron_bars")
        schem.setBlock((cx, ny, cz + 1), "minecraft:iron_bars")
        schem.setBlock((cx, ny, cz - 1), "minecraft:iron_bars")

    # High-altitude Antenna Spire
    schem.setBlock((cx, h - 3, cz), "minecraft:pearlescent_froglight")
    schem.setBlock((cx, h - 2, cz), "minecraft:end_rod")
    schem.setBlock((cx, h - 1, cz), "minecraft:chain")
    schem.setBlock((cx, h, cz), "minecraft:lightning_rod")

    # 5. Exterior Conduit Pass
    from .decoration import apply_greeble_pass
    apply_greeble_pass(schem, w, h, l, theme="void_tech")

    return schem
