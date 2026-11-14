"""
quantum_foundry.py — Quantum Crafter Foundry Builder (v6 Industrial Macro Architecture).

A massive, tiered brutalist processing facility featuring:
- Reinforced stepped blast foundation with caution boundaries
- Recessed quantum core reactor (crying obsidian, sea lantern, glass)
- Dual elevated logistics rail decks with yellow safety lines
- External cooling manifolds, copper grates, and hopper exhaust flues
- Roof-mounted heavy HVAC ventilation batteries
"""

import mcschematic
from .primitives import cuboid_filled, cuboid_walls, flat_plane, line_x, line_z, stepped_buttress, coffered_ceiling_bay

def build_quantum_foundry(schem: mcschematic.MCSchematic, prompt: dict):
    dims = prompt.get("dimensions", {})
    w = max(24, dims.get("width", 28))
    h = max(20, dims.get("height", 26))
    l = max(26, dims.get("length", 32))

    # 1. Foundation & Sub-floor Blast Pad (Y=0..2)
    flat_plane(schem, 0, 0, 0, w - 1, l - 1, "minecraft:polished_blackstone")
    flat_plane(schem, 1, 1, 1, w - 2, l - 2, "minecraft:polished_deepslate")

    # Perimeter caution border
    for x in range(1, w - 1):
        schem.setBlock((x, 1, 1), "minecraft:yellow_concrete")
        schem.setBlock((x, 1, l - 2), "minecraft:yellow_concrete")
    for z in range(1, l - 1):
        schem.setBlock((1, 1, z), "minecraft:yellow_concrete")
        schem.setBlock((w - 2, 1, z), "minecraft:yellow_concrete")

    # 2. Main Industrial Hull Walls (Y=2..H-6)
    hull_top = h - 6
    cuboid_walls(schem, 2, 2, 2, w - 3, hull_top, l - 3, "minecraft:polished_deepslate_bricks")

    # Stepped Buttresses along East and West facades
    for z_pos in range(5, l - 5, 6):
        stepped_buttress(schem, 1, z_pos, 2, hull_top - 2, "west", "minecraft:polished_deepslate", "minecraft:deepslate_brick_stairs", "minecraft:deepslate_tile_wall")
        stepped_buttress(schem, w - 2, z_pos, 2, hull_top - 2, "east", "minecraft:polished_deepslate", "minecraft:deepslate_brick_stairs", "minecraft:deepslate_tile_wall")

    # 3. Recessed Central Quantum Core (Center floor)
    cx, cz = w // 2, l // 2
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            schem.setBlock((cx + dx, 1, cz + dz), "minecraft:crying_obsidian")
    schem.setBlock((cx, 2, cz), "minecraft:sea_lantern")
    schem.setBlock((cx, 3, cz), "minecraft:tinted_glass")
    schem.setBlock((cx, 4, cz), "minecraft:copper_grate")

    # 4. Elevated Transit Rail Decks (Y=3..4, along North & South interiors)
    for x in range(3, w - 3):
        # Southern track
        schem.setBlock((x, 3, 4), "minecraft:polished_andesite")
        schem.setBlock((x, 4, 4), "minecraft:powered_rail[powered=true]")
        # Northern track
        schem.setBlock((x, 3, l - 5), "minecraft:polished_andesite")
        schem.setBlock((x, 4, l - 5), "minecraft:powered_rail[powered=true]")

    # 5. Coffered Ceiling & Upper Girders (Y=hull_top)
    coffered_ceiling_bay(schem, 2, hull_top, 2, w - 3, l - 3, "minecraft:dark_prismarine", "minecraft:stone_brick_slab", "minecraft:pearlescent_froglight", grid_interval=4)

    # 6. Roof Tier & Mechanical Equipment (Y=hull_top+1..H)
    roof_y = hull_top + 1
    flat_plane(schem, 3, roof_y, 3, w - 4, l - 4, "minecraft:polished_deepslate")

    # Heavy HVAC Units
    for hx in [cx - 5, cx + 3]:
        for hz in [cz - 4, cz + 2]:
            for dx in range(2):
                for dz in range(2):
                    schem.setBlock((hx + dx, roof_y + 1, hz + dz), "minecraft:chiseled_deepslate")
                    schem.setBlock((hx + dx, roof_y + 2, hz + dz), "minecraft:iron_trapdoor[half=bottom]")
            schem.setBlock((hx, roof_y + 1, hz + 2), "minecraft:hopper[facing=down]")

    # Cooling Tower array (North edge of roof)
    for kx in range(5, w - 5, 5):
        schem.setBlock((kx, roof_y + 1, l - 5), "minecraft:chiseled_tuff")
        schem.setBlock((kx, roof_y + 2, l - 5), "minecraft:copper_grate")
        schem.setBlock((kx, roof_y + 3, l - 5), "minecraft:lightning_rod")

    # 7. Exterior Greeble Pass
    from .decoration import apply_greeble_pass
    apply_greeble_pass(schem, w, h, l, theme="industrial_singularity")

    return schem
