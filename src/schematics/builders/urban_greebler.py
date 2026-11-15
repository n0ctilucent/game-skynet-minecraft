#!/usr/bin/env python3
"""
urban_greebler.py — Street-level infrastructure, human-scale clutter,
and rooftop/facade greebling generator for the Void-Tech / Emerald Mirror district.
"""

import random
from typing import List, Tuple, Dict, Optional

# Unified 12-block district palette ensuring chunk palette <= 64
DISTRICT_PALETTE = {
    "promenade": [
        "minecraft:andesite",
        "minecraft:stone_bricks",
        "minecraft:cobblestone",
        "minecraft:packed_mud",
        "minecraft:mud_bricks"
    ],
    "unplowed_snow": "minecraft:snow[layers=1]",
    "curb": "minecraft:deepslate_brick_wall",
    "fence": "minecraft:spruce_fence",
    "chain_x": "minecraft:chain[axis=x]",
    "chain_z": "minecraft:chain[axis=z]",
    "chain_y": "minecraft:chain[axis=y]",
    "wall_post": "minecraft:polished_deepslate_wall",
    "warm_lamp": "minecraft:lantern[hanging=true]",
    "cyber_lamp": "minecraft:soul_lantern[hanging=true]",
    "lightning_rod": "minecraft:lightning_rod",
    "copper_vent": "minecraft:oxidized_copper",
    "copper_slab": "minecraft:weathered_cut_copper_slab",
    "smoke_core": "minecraft:campfire[lit=true]",
    "pier_deck": "minecraft:campfire[lit=false]",
    "pier_log": "minecraft:oak_log[axis=y]",
    "pier_slab": "minecraft:spruce_slab[type=top]",
    "bench": "minecraft:spruce_stairs",
    "planter": "minecraft:composter",
    "azalea": "minecraft:flowering_azalea_leaves",
    "berry": "minecraft:sweet_berry_bush[age=3]",
    "hvac_body": "minecraft:iron_block",
    "hvac_vent": "minecraft:iron_trapdoor[half=bottom]",
    "solar": "minecraft:daylight_detector",
    "mast": "minecraft:iron_bars"
}


def build_promenade(x1: int, z1: int, x2: int, z2: int, y: int = 63, width: int = 3, seed: int = 42) -> List[str]:
    """
    Generate 3-to-5-block wide weathered promenade between coordinates.
    Edges receive snow layers (unplowed curbs), core receives randomized masonry.
    """
    commands = []
    rnd = random.Random(seed)
    
    dx = 1 if x2 >= x1 else -1
    dz = 1 if z2 >= z1 else -1
    half_w = width // 2

    # Traverse path
    if abs(x2 - x1) >= abs(z2 - z1):
        # East-West dominant
        for x in range(x1, x2 + dx, dx):
            # Interpolate z
            t = (x - x1) / (x2 - x1) if x2 != x1 else 0
            cz = int(z1 + t * (z2 - z1))
            for offset in range(-half_w, half_w + 1):
                pz = cz + offset
                is_edge = (abs(offset) == half_w)
                block = rnd.choice(DISTRICT_PALETTE["promenade"])
                commands.append(f"setblock {x} {y} {pz} {block}")
                # Clear air above
                commands.append(f"setblock {x} {y + 1} {pz} minecraft:air keep")
                # Unplowed snow on outer curb
                if is_edge and rnd.random() < 0.6:
                    commands.append(f"setblock {x} {y + 1} {pz} {DISTRICT_PALETTE['unplowed_snow']}")
    else:
        # North-South dominant
        for z in range(z1, z2 + dz, dz):
            t = (z - z1) / (z2 - z1) if z2 != z1 else 0
            cx = int(x1 + t * (x2 - x1))
            for offset in range(-half_w, half_w + 1):
                px = cx + offset
                is_edge = (abs(offset) == half_w)
                block = rnd.choice(DISTRICT_PALETTE["promenade"])
                commands.append(f"setblock {px} {y} {z} {block}")
                commands.append(f"setblock {px} {y + 1} {z} minecraft:air keep")
                if is_edge and rnd.random() < 0.6:
                    commands.append(f"setblock {px} {y + 1} {z} {DISTRICT_PALETTE['unplowed_snow']}")

    return commands


def build_lamp_post(x: int, y: int, z: int, style: str = "warm", height: int = 4) -> List[str]:
    """
    Generate 4-block-tall street lamp with hanging luminaire.
    style='warm' -> residential lantern; style='cyber' -> soul lantern / end rod.
    """
    commands = []
    # Pillar
    for dy in range(1, height):
        commands.append(f"setblock {x} {y + dy} {z} {DISTRICT_PALETTE['wall_post']}")
    
    # Arm & luminaire
    top_y = y + height
    commands.append(f"setblock {x} {top_y} {z} {DISTRICT_PALETTE['wall_post']}")
    commands.append(f"setblock {x} {top_y + 1} {z} {DISTRICT_PALETTE['lightning_rod']}")
    
    # Hanging lantern to south or east
    lamp_block = DISTRICT_PALETTE["cyber_lamp"] if style == "cyber" else DISTRICT_PALETTE["warm_lamp"]
    commands.append(f"setblock {x} {top_y} {z + 1} {DISTRICT_PALETTE['fence']}")
    commands.append(f"setblock {x} {top_y - 1} {z + 1} {lamp_block}")

    return commands


def build_guardrail(x1: int, z1: int, x2: int, z2: int, y: int = 64) -> List[str]:
    """
    Line waterfront drop-offs with deepslate brick wall posts linked by chains.
    """
    commands = []
    dx = 1 if x2 >= x1 else -1
    dz = 1 if z2 >= z1 else -1

    if x1 != x2:
        for x in range(x1, x2 + dx, dx):
            if (x - x1) % 3 == 0:
                commands.append(f"setblock {x} {y} {z1} {DISTRICT_PALETTE['curb']}")
            else:
                commands.append(f"setblock {x} {y} {z1} {DISTRICT_PALETTE['chain_x']}")
    elif z1 != z2:
        for z in range(z1, z2 + dz, dz):
            if (z - z1) % 3 == 0:
                commands.append(f"setblock {x1} {y} {z} {DISTRICT_PALETTE['curb']}")
            else:
                commands.append(f"setblock {x1} {y} {z} {DISTRICT_PALETTE['chain_z']}")

    return commands


def build_market_stall(x: int, y: int, z: int, facing: str = "south", theme: str = "red_white") -> List[str]:
    """
    Construct 3x2 open-air market stall with awning and stacked cargo.
    """
    commands = []
    # 4 fence corners (Y+1 to Y+2)
    corners = [(0, 0), (2, 0), (0, 1), (2, 1)]
    for cx, cz in corners:
        commands.append(f"setblock {x + cx} {y + 1} {z + cz} {DISTRICT_PALETTE['fence']}")
        commands.append(f"setblock {x + cx} {y + 2} {z + cz} {DISTRICT_PALETTE['fence']}")

    # Awning at Y+3
    wool_a = "minecraft:red_wool" if theme == "red_white" else "minecraft:cyan_wool"
    wool_b = "minecraft:white_wool" if theme == "red_white" else "minecraft:gray_wool"
    for cx in range(3):
        for cz in range(2):
            wblk = wool_a if (cx + cz) % 2 == 0 else wool_b
            commands.append(f"setblock {x + cx} {y + 3} {z + cz} {wblk}")

    # Counter & Cargo at ground
    commands.append(f"setblock {x + 1} {y + 1} {z} minecraft:barrel[facing=up]")
    commands.append(f"setblock {x + 1} {y + 1} {z + 1} minecraft:chest[facing={facing}]")
    commands.append(f"setblock {x + 3} {y + 1} {z} minecraft:hay_block")
    commands.append(f"setblock {x + 3} {y + 1} {z + 1} minecraft:scaffolding")

    return commands


def build_gathering_nook(x: int, y: int, z: int) -> List[str]:
    """
    Construct benches facing a cobblestone-ringed central campfire.
    """
    commands = []
    # Central fire pit
    commands.append(f"setblock {x} {y} {z} {DISTRICT_PALETTE['smoke_core']}")
    # Stool slabs ring
    for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        commands.append(f"setblock {x + dx} {y} {z + dz} minecraft:cobblestone_slab[type=bottom]")

    # North bench
    commands.append(f"setblock {x - 1} {y} {z - 2} {DISTRICT_PALETTE['bench']}[half=bottom,facing=south]")
    commands.append(f"setblock {x} {y} {z - 2} {DISTRICT_PALETTE['bench']}[half=bottom,facing=south]")
    commands.append(f"setblock {x + 1} {y} {z - 2} {DISTRICT_PALETTE['bench']}[half=bottom,facing=south]")

    # Armrests
    commands.append(f"setblock {x - 2} {y} {z - 2} minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]")
    commands.append(f"setblock {x + 2} {y} {z - 2} minecraft:spruce_trapdoor[facing=west,half=bottom,open=true]")

    return commands


def build_pier(x: int, y_water: int, z: int, length: int = 6, width: int = 3, axis: str = "z") -> List[str]:
    """
    Extend a 3-block-wide dock over water on oak_log pilings with unlit campfire planks.
    """
    commands = []
    half_w = width // 2
    deck_y = y_water + 1

    for step in range(length):
        if axis == "z":
            cz = z + step
            # Pilings every 3 blocks
            is_piling_row = (step % 3 == 0)
            for offset in range(-half_w, half_w + 1):
                cx = x + offset
                if is_piling_row and (abs(offset) == half_w):
                    # Pilings down 3 blocks
                    for dy in range(4):
                        commands.append(f"setblock {cx} {deck_y - dy} {cz} {DISTRICT_PALETTE['pier_log']}")
                # Decking
                commands.append(f"setblock {cx} {deck_y} {cz} {DISTRICT_PALETTE['pier_deck']}")
            
            # Bollards at end
            if step == length - 1:
                commands.append(f"setblock {x - half_w} {deck_y + 1} {cz} {DISTRICT_PALETTE['fence']}")
                commands.append(f"setblock {x + half_w} {deck_y + 1} {cz} {DISTRICT_PALETTE['fence']}")
                commands.append(f"setblock {x - half_w} {deck_y + 2} {cz} {DISTRICT_PALETTE['warm_lamp']}")
                commands.append(f"setblock {x + half_w} {deck_y + 2} {cz} {DISTRICT_PALETTE['warm_lamp']}")

    return commands


def build_chimney_vent(x: int, y_roof: int, z: int, height: int = 4) -> List[str]:
    """
    Construct functional brick/cobblestone chimney with rising smoke campfire.
    """
    commands = []
    for dy in range(height):
        commands.append(f"setblock {x} {y_roof + dy} {z} minecraft:bricks")
    
    top_y = y_roof + height
    # Campfire generates live smoke particles
    commands.append(f"setblock {x} {top_y} {z} {DISTRICT_PALETTE['smoke_core']}")
    commands.append(f"setblock {x} {top_y + 1} {z} minecraft:stone_brick_stairs[half=bottom,facing=north]")
    commands.append(f"setblock {x} {top_y} {z + 1} minecraft:spruce_trapdoor[half=bottom,open=false]")
    commands.append(f"setblock {x} {top_y} {z - 1} minecraft:spruce_trapdoor[half=bottom,open=false]")

    return commands


def build_hvac_and_solar(x: int, y_roof: int, z: int) -> List[str]:
    """
    Construct industrial rooftop HVAC unit, daylight solar array, and comm mast.
    """
    commands = []
    # 2x2 HVAC unit
    for dx in range(2):
        for dz in range(2):
            commands.append(f"setblock {x + dx} {y_roof + 1} {z + dz} {DISTRICT_PALETTE['hvac_body']}")
            commands.append(f"setblock {x + dx} {y_roof + 2} {z + dz} {DISTRICT_PALETTE['hvac_vent']}")
    
    # Exhaust hopper
    commands.append(f"setblock {x + 2} {y_roof + 1} {z} minecraft:hopper[facing=down]")
    commands.append(f"setblock {x + 2} {y_roof + 1} {z + 1} minecraft:anvil[facing=north]")

    # Solar panels (2x1)
    commands.append(f"setblock {x - 1} {y_roof + 1} {z} {DISTRICT_PALETTE['solar']}")
    commands.append(f"setblock {x - 1} {y_roof + 1} {z + 1} {DISTRICT_PALETTE['solar']}")

    # Communication mast
    for dy in range(1, 4):
        commands.append(f"setblock {x} {y_roof + 2 + dy} {z} {DISTRICT_PALETTE['mast']}")
    commands.append(f"setblock {x} {y_roof + 6} {z} {DISTRICT_PALETTE['lightning_rod']}")

    return commands


def build_window_flower_box(x: int, y: int, z: int, facing: str = "south", flower: str = "spruce_sapling") -> List[str]:
    """
    Attach spruce trapdoor flower box holding potted plants beneath windows.
    """
    commands = []
    # Offset based on facing
    oz = 1 if facing == "south" else (-1 if facing == "north" else 0)
    ox = 1 if facing == "east" else (-1 if facing == "west" else 0)
    
    bx = x + ox
    bz = z + oz
    commands.append(f"setblock {bx} {y} {bz} minecraft:spruce_trapdoor[half=top,open=false]")
    commands.append(f"setblock {bx} {y + 1} {bz} minecraft:flower_pot")
    if flower == "spruce_sapling":
        commands.append(f"setblock {bx} {y + 1} {bz} minecraft:potted_spruce_sapling")
    elif flower == "red_tulip":
        commands.append(f"setblock {bx} {y + 1} {bz} minecraft:potted_red_tulip")
    else:
        commands.append(f"setblock {bx} {y + 1} {bz} minecraft:potted_fern")

    return commands


def build_snow_flora(x: int, y: int, z: int) -> List[str]:
    """
    Place dark evergreen hedges, sweet berry clusters, and composter planters.
    """
    commands = []
    commands.append(f"setblock {x} {y} {z} {DISTRICT_PALETTE['planter']}")
    commands.append(f"setblock {x} {y + 1} {z} {DISTRICT_PALETTE['azalea']}")
    commands.append(f"setblock {x + 1} {y} {z} {DISTRICT_PALETTE['berry']}")
    commands.append(f"setblock {x - 1} {y} {z} minecraft:spruce_leaves[persistent=true]")

    return commands
