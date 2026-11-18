#!/usr/bin/env python3
from __future__ import annotations
"""
containment_rail_builder.py — Autonomous Railway & Corner Synthesis Engine
for AI Containment Zone Alpha (X in [-1539, -945], Z in [-913, -489], Rail Y=64).

Resolves corner-placement failure modes between buildings:
1. Powered rails cannot curve in vanilla Minecraft; all 90-degree orthogonal
   turns strictly employ standard unpowered rails (`minecraft:rail[shape=...]`).
2. Sub-surface roadbed at corner vertices strictly uses inert polished deepslate
   (`minecraft:polished_deepslate` at Y=63), suppressing redstone block power interference.
3. Explicit blockstate shape assignment prevents dynamic neighbour-snapping errors.
4. Generates Sponge .schem files, WorldEdit schematics, JSON manifests, and RCON deploy scripts.
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path

# Ensure local user site packages are accessible for mcrcon / mcschematic across venvs
user_site_313 = Path.home() / ".local/lib/python3.13/site-packages"
if user_site_313.exists() and str(user_site_313) not in sys.path:
    sys.path.append(str(user_site_313))

try:
    import mcschematic
except ImportError:
    mcschematic = None

try:
    from mcrcon import MCRcon
except ImportError:
    MCRcon = None

PROJECT_ROOT = Path("/home/minecraft")
SCHEM_DIR = PROJECT_ROOT / "schematics"
WE_SCHEM_DIR = PROJECT_ROOT / "plugins/WorldEdit/schematics"
BIN_DIR = PROJECT_ROOT / "bin"

# Boundary Envelope for AI Containment Zone Alpha
CONTAINMENT_BOUNDS = {
    "min_x": -1539, "max_x": -945,
    "min_z": -913,  "max_z": -489,
    "min_y": 40,    "max_y": 100,
    "rail_y": 64,
    "roadbed_y": 63
}

# Major Facilities & Transit Stations in Containment Zone Alpha
CONTAINMENT_FACILITIES = {
    "ai_lab_gateway": {
        "name": "AI Containment Lab Gateway",
        "coords": {"x": -1545, "y": 64, "z": -608},
        "junction_target": {"x": -1539, "y": 64, "z": -608}
    },
    "neural_core_staging": {
        "name": "Neural Core Testing Depot",
        "coords": {"x": -1242, "y": 64, "z": -701}
    },
    "data_vault_substation": {
        "name": "Containment Data Vault Substation",
        "coords": {"x": -1090, "y": 64, "z": -580}
    }
}


def calculate_corner_shape(dx_in: int, dz_in: int, dx_out: int, dz_out: int) -> str:
    """
    Computes the required vanilla Minecraft rail curve shape given normalized
    incoming and outgoing direction vectors.

    Vanilla curved rail shapes:
    - south_east: connects South (Z+1) and East (X+1)
    - south_west: connects South (Z+1) and West (X-1)
    - north_east: connects North (Z-1) and East (X+1)
    - north_west: connects North (Z-1) and West (X-1)
    """
    # Normalize vectors to signs (-1, 0, 1)
    din_x = 0 if dx_in == 0 else (1 if dx_in > 0 else -1)
    din_z = 0 if dz_in == 0 else (1 if dz_in > 0 else -1)
    dout_x = 0 if dx_out == 0 else (1 if dx_out > 0 else -1)
    dout_z = 0 if dz_out == 0 else (1 if dz_out > 0 else -1)

    # Inverted incoming direction represents where the track came from
    from_x, from_z = -din_x, -din_z
    to_x, to_z = dout_x, dout_z

    connected = {(from_x, from_z), (to_x, to_z)}

    # Match against canonical pairs:
    # North=(0, -1), South=(0, 1), East=(1, 0), West=(-1, 0)
    if connected == {(0, 1), (1, 0)}:
        return "south_east"
    elif connected == {(0, 1), (-1, 0)}:
        return "south_west"
    elif connected == {(0, -1), (1, 0)}:
        return "north_east"
    elif connected == {(0, -1), (-1, 0)}:
        return "north_west"
    else:
        raise ValueError(
            f"Invalid orthogonal 90-degree turn: incoming=({dx_in},{dz_in}), outgoing=({dx_out},{dz_out})"
        )


def validate_coordinates(x: int, z: int, margin: int = 10) -> bool:
    """Ensures coordinates reside within AI Containment Zone Alpha."""
    b = CONTAINMENT_BOUNDS
    # Allow 10 block margin for building interface aprons (e.g. ai-lab at X=-1545)
    return (b["min_x"] - margin <= x <= b["max_x"] + margin and
            b["min_z"] - margin <= z <= b["max_z"] + margin)


def build_corner_junction_schematic(
    turn_type: str,
    arm_length: int = 7
) -> tuple[mcschematic.MCSchematic, dict, dict]:
    """
    Synthesizes an isolated, mathematically verified 90-degree corner junction schematic.
    
    Turn Types:
    - 'NW': Travelling North (Z-) -> turns East (X+)  [shape=south_east]
    - 'NE': Travelling East (X+)  -> turns South (Z+) [shape=south_west]
    - 'SE': Travelling South (Z+) -> turns West (X-)  [shape=north_west]
    - 'SW': Travelling West (X-)  -> turns North (Z-) [shape=north_east]
    """
    schem = mcschematic.MCSchematic()
    w = arm_length * 2 + 1
    h = 8
    l = arm_length * 2 + 1
    cx, cz = arm_length, arm_length

    # Roadbed Y=0 (World Y=63), Rail Y=1 (World Y=64), Air Y=2..4 (World Y=65..67)
    
    # 1. Base foundation platform (Polished Deepslate)
    for x in range(w):
        for z in range(l):
            schem.setBlock((x, 0, z), "minecraft:polished_deepslate")

    # Determine arm geometry and corner shape
    if turn_type == "NW":
        # Enters from South (Z+), exits to East (X+)
        # Corner shape connects South and East
        corner_shape = "south_east"
        # Inflow track: from South along center X (z from cz+1 to l-1)
        inflow = [(cx, z, "north_south") for z in range(cz + 1, l)]
        # Outflow track: to East along center Z (x from cx+1 to w-1)
        outflow = [(x, cz, "east_west") for x in range(cx + 1, w)]
    elif turn_type == "NE":
        # Enters from West (X-), exits to South (Z+)
        corner_shape = "south_west"
        inflow = [(x, cz, "east_west") for x in range(0, cx)]
        outflow = [(cx, z, "north_south") for z in range(cz + 1, l)]
    elif turn_type == "SE":
        # Enters from North (Z-), exits to West (X-)
        corner_shape = "north_west"
        inflow = [(cx, z, "north_south") for z in range(0, cz)]
        outflow = [(x, cz, "east_west") for x in range(0, cx)]
    elif turn_type == "SW":
        # Enters from East (X+), exits to North (Z-)
        corner_shape = "north_east"
        inflow = [(x, cz, "east_west") for x in range(cx + 1, w)]
        outflow = [(cx, z, "north_south") for z in range(0, cz)]
    else:
        raise ValueError(f"Unknown turn_type: {turn_type}")

    # 2. Sub-surface Power Core (Redstone blocks strictly under straight powered runs)
    # CRITICAL: (cx, 0, cz) REMAINS POLISHED DEEPSLATE (NO REDSTONE)
    schem.setBlock((cx, 0, cz), "minecraft:polished_deepslate")

    # Inflow and Outflow arm placement
    for (x, z, axis) in inflow + outflow:
        # Powered rail on arm
        schem.setBlock((x, 0, z), "minecraft:redstone_block")
        schem.setBlock((x, 1, z), f"minecraft:powered_rail[shape={axis}]")

    # 3. CRITICAL CORNER PLACEMENT:
    # Must be standard rail (`minecraft:rail`), NOT `minecraft:powered_rail`
    schem.setBlock((cx, 1, cz), f"minecraft:rail[shape={corner_shape}]")

    # 4. Mandatory 3-block vertical passenger air clearance envelope (Y=2..4)
    for x in range(w):
        for z in range(l):
            for y in range(2, 5):
                schem.setBlock((x, y, z), "minecraft:air")

    # 5. Protective Guardrails & Corner Luminaire
    # Place wall buffers along the exterior turn shoulder
    schem.setBlock((cx, 1, cz - 1), "minecraft:polished_deepslate_wall")
    schem.setBlock((cx - 1, 1, cz), "minecraft:polished_deepslate_wall")
    schem.setBlock((cx - 1, 1, cz - 1), "minecraft:pearlescent_froglight")

    dimensions = {"width": w, "height": h, "length": l}
    corner_meta = {
        "turn_type": turn_type,
        "corner_shape": corner_shape,
        "vertex_relative": {"x": cx, "y": 1, "z": cz},
        "roadbed_block": "minecraft:polished_deepslate",
        "rail_block": f"minecraft:rail[shape={corner_shape}]"
    }

    return schem, dimensions, corner_meta


def build_building_interconnect_schematic() -> tuple[mcschematic.MCSchematic, dict, dict]:
    """
    Synthesizes the multi-segment connector from AI Containment Lab Gateway
    (-1545, 64, -608) turning Northward into the Orbital Line at (-1539, 64, -608).
    Includes the verified South-to-East / West-to-North corner junction.
    """
    schem = mcschematic.MCSchematic()
    
    # Span from X=-1546 to -1537 (width 10), Z=-615 to -605 (length 11), Y=63 to 68 (height 6)
    w, h, l = 12, 6, 14
    # Local coordinate mapping: X_world = -1546 + x, Z_world = -616 + z
    # Origin: (-1546, 63, -616)
    
    # 1. Base Roadbed
    for x in range(w):
        for z in range(l):
            schem.setBlock((x, 0, z), "minecraft:polished_deepslate")
            for y in range(1, 5):
                schem.setBlock((x, y, z), "minecraft:air")

    # Building spur comes from West at local Z=8 (World Z=-608), from x=1 to x=7 (World X=-1545 to -1539)
    # Corner vertex at local x=7, z=8 (World X=-1539, Z=-608)
    vertex_x, vertex_z = 7, 8

    # West-to-East spur track (coming out of AI Lab)
    for x in range(1, vertex_x):
        schem.setBlock((x, 0, vertex_z), "minecraft:redstone_block")
        schem.setBlock((x, 1, vertex_z), "minecraft:powered_rail[shape=east_west]")

    # Main orbital line running North-South along local x=7 (World X=-1539)
    # North run (z from 1 to vertex_z - 1)
    for z in range(1, vertex_z):
        schem.setBlock((vertex_x, 0, z), "minecraft:redstone_block")
        schem.setBlock((vertex_x, 1, z), "minecraft:powered_rail[shape=north_south]")

    # South run (z from vertex_z + 1 to l - 1)
    for z in range(vertex_z + 1, l - 1):
        schem.setBlock((vertex_x, 0, z), "minecraft:redstone_block")
        schem.setBlock((vertex_x, 1, z), "minecraft:powered_rail[shape=north_south]")

    # CRITICAL: Corner Vertex (Turn coming from AI Lab West heading North):
    # From West (-1, 0) to North (0, -1) => shape: north_west (or south_west for inbound/outbound)
    schem.setBlock((vertex_x, 0, vertex_z), "minecraft:polished_deepslate")
    schem.setBlock((vertex_x, 1, vertex_z), "minecraft:rail[shape=north_west]")

    # Anti-mob lighting
    schem.setBlock((vertex_x + 1, 1, vertex_z), "minecraft:pearlescent_froglight")
    schem.setBlock((vertex_x - 1, 1, vertex_z - 1), "minecraft:pearlescent_froglight")

    dims = {"width": w, "height": h, "length": l}
    meta = {
        "interconnect": "AI_LAB_TO_ORBITAL_TRUNK",
        "origin_world": {"x": -1546, "y": 63, "z": -616},
        "corner_world": {"x": -1539, "y": 64, "z": -608},
        "corner_shape": "north_west",
        "rail_type": "minecraft:rail"
    }
    return schem, dims, meta


def build_arched_viaduct_span(
    x1: int, z1: int, x2: int, z2: int,
    y_deck: int = 64, pier_interval: int = 10, power_interval: int = 15, seed: int = 42
) -> list[str]:
    """
    Generates an elevated arched masonry viaduct spanning open terrain/canyons.
    - Deck: stone_bricks with mossy/cracked accents and stone_brick_stairs[half=top] corbels.
    - Underside arches: semicircular haunches with inverted stone_brick_stairs & slabs.
    - Parapets: iron_bars interrupted every 6 blocks by cobblestone_wall stanchions.
    - Piers: 2x2 stone_bricks piers anchored down 4-8 blocks.
    - Power: sub-surface redstone_block under powered_rail spaced every 15 blocks (step % power_interval == 0).
    """
    import random
    rnd = random.Random(seed)
    commands = []
    y_bed = y_deck - 1

    dx = 1 if x2 >= x1 else -1
    dz = 1 if z2 >= z1 else -1

    step = 0
    if x1 != x2:
        for x in range(x1, x2 + dx, dx):
            is_powered = (step % power_interval == 0)
            if is_powered:
                commands.append(f"setblock {x} {y_bed} {z1} minecraft:redstone_block")
                commands.append(f"setblock {x} {y_deck} {z1} minecraft:powered_rail[shape=east_west]")
            else:
                brick = "minecraft:mossy_stone_bricks" if rnd.random() < 0.2 else "minecraft:stone_bricks"
                commands.append(f"setblock {x} {y_bed} {z1} {brick}")
                commands.append(f"setblock {x} {y_deck} {z1} minecraft:rail[shape=east_west]")

            for dy in range(1, 4):
                for offset in (-1, 0, 1):
                    commands.append(f"setblock {x} {y_deck + dy} {z1 + offset} minecraft:air keep")

            for offset, facing in [(-1, "north"), (1, "south")]:
                cz = z1 + offset
                commands.append(f"setblock {x} {y_bed} {cz} minecraft:stone_brick_stairs[half=top,facing={facing}]")
                if step % 6 == 0:
                    commands.append(f"setblock {x} {y_deck + 1} {cz} minecraft:cobblestone_wall")
                else:
                    commands.append(f"setblock {x} {y_deck + 1} {cz} minecraft:iron_bars")

            is_pier = (step % pier_interval == 0)
            if is_pier:
                for px in (x, x + (1 if dx > 0 else -1)):
                    for pz in (z1 - 1, z1):
                        for dy in range(1, 6):
                            commands.append(f"setblock {px} {y_bed - dy} {pz} minecraft:stone_bricks")
            else:
                dist_to_pier = min(step % pier_interval, pier_interval - (step % pier_interval))
                if dist_to_pier == 1:
                    commands.append(f"setblock {x} {y_bed - 1} {z1} minecraft:stone_brick_stairs[half=top,facing=east]")
                elif dist_to_pier == 2:
                    commands.append(f"setblock {x} {y_bed - 1} {z1} minecraft:stone_brick_slab[type=top]")

            step += 1

    elif z1 != z2:
        for z in range(z1, z2 + dz, dz):
            is_powered = (step % power_interval == 0)
            if is_powered:
                commands.append(f"setblock {x1} {y_bed} {z} minecraft:redstone_block")
                commands.append(f"setblock {x1} {y_deck} {z} minecraft:powered_rail[shape=north_south]")
            else:
                brick = "minecraft:mossy_stone_bricks" if rnd.random() < 0.2 else "minecraft:stone_bricks"
                commands.append(f"setblock {x1} {y_bed} {z} {brick}")
                commands.append(f"setblock {x1} {y_deck} {z} minecraft:rail[shape=north_south]")

            for dy in range(1, 4):
                for offset in (-1, 0, 1):
                    commands.append(f"setblock {x1 + offset} {y_deck + dy} {z} minecraft:air keep")

            for offset, facing in [(-1, "west"), (1, "east")]:
                cx = x1 + offset
                commands.append(f"setblock {cx} {y_bed} {z} minecraft:stone_brick_stairs[half=top,facing={facing}]")
                if step % 6 == 0:
                    commands.append(f"setblock {cx} {y_deck + 1} {z} minecraft:cobblestone_wall")
                else:
                    commands.append(f"setblock {cx} {y_deck + 1} {z} minecraft:iron_bars")

            is_pier = (step % pier_interval == 0)
            if is_pier:
                for pz in (z, z + (1 if dz > 0 else -1)):
                    for px in (x1 - 1, x1):
                        for dy in range(1, 6):
                            commands.append(f"setblock {px} {y_bed - dy} {pz} minecraft:stone_bricks")
            else:
                dist_to_pier = min(step % pier_interval, pier_interval - (step % pier_interval))
                if dist_to_pier == 1:
                    commands.append(f"setblock {x1} {y_bed - 1} {z} minecraft:stone_brick_stairs[half=top,facing=south]")
                elif dist_to_pier == 2:
                    commands.append(f"setblock {x1} {y_bed - 1} {z} minecraft:stone_brick_slab[type=top]")

            step += 1

    return commands


def build_dual_track_segment(
    x1: int, z1: int, x2: int, z2: int,
    axis: str = "X",
    power_interval: int = 15,
    y_deck: int = 64,
    y_roadbed: int = 63,
    roadbed_block: str = "minecraft:polished_deepslate",
    install_telemetry: bool = True,
    node_id: str = "CHONK-01",
    roadbed_style: str = "standard",
    deck_block: str = "minecraft:oak_planks",
    ballast_block: str = "minecraft:gravel",
    has_canopy: bool = False,
    facia_depth: int = 1
) -> list[str]:
    """
    Generates verified RCON commands for a dual-track pair corridor:
    - Tracks built in pairs with a one-block space (center median) between them
      to allow simultaneous travel in a single direction per track.
    - Exactly 3 blocks above the placed rails (Y_deck + 1..3, e.g. Y=65, 66, 67)
      are cleared to air so the player is not decapitated or suffocated.
    - Redstone powered rails placed every 15 blocks (step % power_interval == 0)
      with subsurface redstone_block at Y=63 to maintain continuous 8.0 m/s cart speed.
    - Detector rail sensors with embedded command blocks at corridor midpoints for
      live Chonk telemetry logging and verification.
    
    Roadbed Styles:
    - "standard": Deepslate foundation, 1-block air median, end buffers.
    - "timber_viaduct" / "gravel_ballast":
      5-block-wide timber bridge deck (oak_planks/spruce_planks) with outer facia dropping
      1-2 blocks below track plane; gravel ballast directly beneath each track lane;
      1-block center median topped with upright lanterns every 12-16 blocks;
      outer pedestrian maintenance shoulders with stone_brick_slab[type=top] curbs and
      continuous oak_fence guardrails topped with torches every 4-6 blocks;
      optional overhead translucent glass weather canopy.
    """
    commands = []

    if roadbed_style.lower() in ("timber_viaduct", "gravel_ballast", "viaduct"):
        if axis.upper() == "X":
            start_x = min(x1, x2)
            end_x = max(x1, x2)
            center_z = z1
            z_w1 = center_z - 2   # Outer shoulder/walkway 1
            z_t1 = center_z - 1   # Track 1 (Eastbound: +X)
            z_med = center_z      # Center Median: 1-block space
            z_t2 = center_z + 1   # Track 2 (Westbound: -X)
            z_w2 = center_z + 2   # Outer shoulder/walkway 2

            # 1. 3-block vertical passenger air clearance envelope above rails (Y=65..67)
            commands.append(f"fill {start_x} {y_deck + 1} {z_w1} {end_x} {y_deck + 3} {z_w2} minecraft:air keep")

            # 2. 5-block-wide timber bridge deck & outer side facia drops below track plane
            commands.append(f"fill {start_x} {y_roadbed} {z_w1} {end_x} {y_roadbed} {z_w2} {deck_block}")
            for fd in range(1, facia_depth + 1):
                commands.append(f"fill {start_x} {y_roadbed - fd} {z_w1} {end_x} {y_roadbed - fd} {z_w1} {deck_block}")
                commands.append(f"fill {start_x} {y_roadbed - fd} {z_w2} {end_x} {y_roadbed - fd} {z_w2} {deck_block}")

            # 3. Continuous gravel ballast bed beneath each track lane
            commands.append(f"fill {start_x} {y_roadbed} {z_t1} {end_x} {y_roadbed} {z_t1} {ballast_block}")
            commands.append(f"fill {start_x} {y_roadbed} {z_t2} {end_x} {y_roadbed} {z_t2} {ballast_block}")

            # 4. Center median timber divider with upright lanterns every 12-16 blocks
            commands.append(f"fill {start_x} {y_deck} {z_med} {end_x} {y_deck} {z_med} {deck_block}")
            for x in range(start_x, end_x + 1):
                step = x - start_x
                if step % 15 == 0:
                    commands.append(f"setblock {x} {y_deck + 1} {z_med} minecraft:lantern[hanging=false]")

            # 5. Outer maintenance walkways with stone_brick_slab curbs and oak_fence guardrails
            commands.append(f"fill {start_x} {y_roadbed} {z_w1} {end_x} {y_roadbed} {z_w1} minecraft:stone_brick_slab[type=top]")
            commands.append(f"fill {start_x} {y_roadbed} {z_w2} {end_x} {y_roadbed} {z_w2} minecraft:stone_brick_slab[type=top]")
            commands.append(f"fill {start_x} {y_deck} {z_w1} {end_x} {y_deck} {z_w1} minecraft:oak_fence")
            commands.append(f"fill {start_x} {y_deck} {z_w2} {end_x} {y_deck} {z_w2} minecraft:oak_fence")
            for x in range(start_x, end_x + 1):
                step = x - start_x
                if step % 5 == 0:
                    commands.append(f"setblock {x} {y_deck + 1} {z_w1} minecraft:torch")
                    commands.append(f"setblock {x} {y_deck + 1} {z_w2} minecraft:torch")

            # 6. Dual-track rail lanes with flush redstone block powering every interval
            commands.append(f"fill {start_x} {y_deck} {z_t1} {end_x} {y_deck} {z_t1} minecraft:rail[shape=east_west]")
            commands.append(f"fill {start_x} {y_deck} {z_t2} {end_x} {y_deck} {z_t2} minecraft:rail[shape=east_west]")
            for x in range(start_x, end_x + 1):
                step = x - start_x
                if step % power_interval == 0:
                    commands.append(f"setblock {x} {y_roadbed} {z_t1} minecraft:redstone_block")
                    commands.append(f"setblock {x} {y_deck} {z_t1} minecraft:powered_rail[shape=east_west]")
                    commands.append(f"setblock {x} {y_roadbed} {z_t2} minecraft:redstone_block")
                    commands.append(f"setblock {x} {y_deck} {z_t2} minecraft:powered_rail[shape=east_west]")

            # 7. Optional overhead translucent glass canopy
            if has_canopy:
                commands.append(f"fill {start_x} {y_deck + 4} {z_w1} {end_x} {y_deck + 4} {z_w1} {deck_block}")
                commands.append(f"fill {start_x} {y_deck + 4} {z_t1} {end_x} {y_deck + 4} {z_t2} minecraft:glass")
                commands.append(f"fill {start_x} {y_deck + 4} {z_w2} {end_x} {y_deck + 4} {z_w2} {deck_block}")

            # 8. Midpoint Telemetry Sensor Installation
            if install_telemetry:
                mid_x = (start_x + end_x) // 2
                if (mid_x - start_x) % power_interval == 0:
                    mid_x += 1
                commands.append(
                    f"setblock {mid_x} {y_roadbed} {z_t1} "
                    f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T1_EASTBOUND_SPEED_8.0\"}}"
                )
                commands.append(f"setblock {mid_x} {y_deck} {z_t1} minecraft:detector_rail[shape=east_west]")
                commands.append(
                    f"setblock {mid_x} {y_roadbed} {z_t2} "
                    f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T2_WESTBOUND_SPEED_8.0\"}}"
                )
                commands.append(f"setblock {mid_x} {y_deck} {z_t2} minecraft:detector_rail[shape=east_west]")

        elif axis.upper() == "Z":
            start_z = min(z1, z2)
            end_z = max(z1, z2)
            center_x = x1
            x_w1 = center_x - 2   # Outer shoulder/walkway 1
            x_t1 = center_x - 1   # Track 1 (Southbound: +Z)
            x_med = center_x      # Center Median: 1-block space
            x_t2 = center_x + 1   # Track 2 (Northbound: -Z)
            x_w2 = center_x + 2   # Outer shoulder/walkway 2

            # 1. 3-block vertical passenger air clearance envelope above rails (Y=65..67)
            commands.append(f"fill {x_w1} {y_deck + 1} {start_z} {x_w2} {y_deck + 3} {end_z} minecraft:air keep")

            # 2. 5-block-wide timber bridge deck & outer side facia drops below track plane
            commands.append(f"fill {x_w1} {y_roadbed} {start_z} {x_w2} {y_roadbed} {end_z} {deck_block}")
            for fd in range(1, facia_depth + 1):
                commands.append(f"fill {x_w1} {y_roadbed - fd} {start_z} {x_w1} {y_roadbed - fd} {end_z} {deck_block}")
                commands.append(f"fill {x_w2} {y_roadbed - fd} {start_z} {x_w2} {y_roadbed - fd} {end_z} {deck_block}")

            # 3. Continuous gravel ballast bed beneath each track lane
            commands.append(f"fill {x_t1} {y_roadbed} {start_z} {x_t1} {y_roadbed} {end_z} {ballast_block}")
            commands.append(f"fill {x_t2} {y_roadbed} {start_z} {x_t2} {y_roadbed} {end_z} {ballast_block}")

            # 4. Center median timber divider with upright lanterns every 12-16 blocks
            commands.append(f"fill {x_med} {y_deck} {start_z} {x_med} {y_deck} {end_z} {deck_block}")
            for z in range(start_z, end_z + 1):
                step = z - start_z
                if step % 15 == 0:
                    commands.append(f"setblock {x_med} {y_deck + 1} {z} minecraft:lantern[hanging=false]")

            # 5. Outer maintenance walkways with stone_brick_slab curbs and oak_fence guardrails
            commands.append(f"fill {x_w1} {y_roadbed} {start_z} {x_w1} {y_roadbed} {end_z} minecraft:stone_brick_slab[type=top]")
            commands.append(f"fill {x_w2} {y_roadbed} {start_z} {x_w2} {y_roadbed} {end_z} minecraft:stone_brick_slab[type=top]")
            commands.append(f"fill {x_w1} {y_deck} {start_z} {x_w1} {y_deck} {end_z} minecraft:oak_fence")
            commands.append(f"fill {x_w2} {y_deck} {start_z} {x_w2} {y_deck} {end_z} minecraft:oak_fence")
            for z in range(start_z, end_z + 1):
                step = z - start_z
                if step % 5 == 0:
                    commands.append(f"setblock {x_w1} {y_deck + 1} {z} minecraft:torch")
                    commands.append(f"setblock {x_w2} {y_deck + 1} {z} minecraft:torch")

            # 6. Dual-track rail lanes with flush redstone block powering every interval
            commands.append(f"fill {x_t1} {y_deck} {start_z} {x_t1} {y_deck} {end_z} minecraft:rail[shape=north_south]")
            commands.append(f"fill {x_t2} {y_deck} {start_z} {x_t2} {y_deck} {end_z} minecraft:rail[shape=north_south]")
            for z in range(start_z, end_z + 1):
                step = z - start_z
                if step % power_interval == 0:
                    commands.append(f"setblock {x_t1} {y_roadbed} {z} minecraft:redstone_block")
                    commands.append(f"setblock {x_t1} {y_deck} {z} minecraft:powered_rail[shape=north_south]")
                    commands.append(f"setblock {x_t2} {y_roadbed} {z} minecraft:redstone_block")
                    commands.append(f"setblock {x_t2} {y_deck} {z} minecraft:powered_rail[shape=north_south]")

            # 7. Optional overhead translucent glass canopy
            if has_canopy:
                commands.append(f"fill {x_w1} {y_deck + 4} {start_z} {x_w1} {y_deck + 4} {end_z} {deck_block}")
                commands.append(f"fill {x_t1} {y_deck + 4} {start_z} {x_t2} {y_deck + 4} {end_z} minecraft:glass")
                commands.append(f"fill {x_w2} {y_deck + 4} {start_z} {x_w2} {y_deck + 4} {end_z} {deck_block}")

            # 8. Midpoint Telemetry Sensor Installation
            if install_telemetry:
                mid_z = (start_z + end_z) // 2
                if (mid_z - start_z) % power_interval == 0:
                    mid_z += 1
                commands.append(
                    f"setblock {x_t1} {y_roadbed} {mid_z} "
                    f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T1_SOUTHBOUND_SPEED_8.0\"}}"
                )
                commands.append(f"setblock {x_t1} {y_deck} {mid_z} minecraft:detector_rail[shape=north_south]")
                commands.append(
                    f"setblock {x_t2} {y_roadbed} {mid_z} "
                    f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T2_NORTHBOUND_SPEED_8.0\"}}"
                )
                commands.append(f"setblock {x_t2} {y_deck} {mid_z} minecraft:detector_rail[shape=north_south]")
        else:
            raise ValueError(f"Unsupported axis: {axis}. Use 'X' or 'Z'.")

        return commands

    # Default 'standard' roadbed style (backward-compatible)
    if axis.upper() == "X":
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        center_z = z1
        z_t1 = center_z - 1  # Track 1 (Eastbound: +X)
        z_med = center_z     # Center Median: 1-block space
        z_t2 = center_z + 1  # Track 2 (Westbound: -X)

        # 1. 3-block vertical passenger air clearance envelope above rails (Y=65..67)
        commands.append(f"fill {start_x} {y_deck + 1} {z_t1} {end_x} {y_deck + 3} {z_t2} minecraft:air keep")
        # Ensure median block at rail level Y=64 is clear
        commands.append(f"fill {start_x} {y_deck} {z_med} {end_x} {y_deck} {z_med} minecraft:air keep")

        # 2. Sub-surface roadbed foundation at Y=63
        commands.append(f"fill {start_x} {y_roadbed} {z_t1} {end_x} {y_roadbed} {z_t2} {roadbed_block}")

        # 3. Rails at Y=64
        commands.append(f"fill {start_x} {y_deck} {z_t1} {end_x} {y_deck} {z_t1} minecraft:rail[shape=east_west]")
        commands.append(f"fill {start_x} {y_deck} {z_t2} {end_x} {y_deck} {z_t2} minecraft:rail[shape=east_west]")

        # 4. Concealed sub-surface powering every 15 blocks
        for x in range(start_x, end_x + 1):
            step = x - start_x
            if step % power_interval == 0:
                # Track 1 powered rail + subfloor redstone block
                commands.append(f"setblock {x} {y_roadbed} {z_t1} minecraft:redstone_block")
                commands.append(f"setblock {x} {y_deck} {z_t1} minecraft:powered_rail[shape=east_west]")
                # Track 2 powered rail + subfloor redstone block
                commands.append(f"setblock {x} {y_roadbed} {z_t2} minecraft:redstone_block")
                commands.append(f"setblock {x} {y_deck} {z_t2} minecraft:powered_rail[shape=east_west]")

        # 5. End buffers / terminal stops
        commands.append(f"setblock {start_x - 1} {y_deck} {z_t1} {roadbed_block}")
        commands.append(f"setblock {end_x + 1} {y_deck} {z_t1} {roadbed_block}")
        commands.append(f"setblock {start_x - 1} {y_deck} {z_t2} {roadbed_block}")
        commands.append(f"setblock {end_x + 1} {y_deck} {z_t2} {roadbed_block}")

        # 6. Telemetry Sensor Installation at midpoint
        if install_telemetry:
            mid_x = (start_x + end_x) // 2
            if (mid_x - start_x) % power_interval == 0:
                mid_x += 1
            commands.append(
                f"setblock {mid_x} {y_roadbed} {z_t1} "
                f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T1_EASTBOUND_SPEED_8.0\"}}"
            )
            commands.append(f"setblock {mid_x} {y_deck} {z_t1} minecraft:detector_rail[shape=east_west]")
            commands.append(
                f"setblock {mid_x} {y_roadbed} {z_t2} "
                f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T2_WESTBOUND_SPEED_8.0\"}}"
            )
            commands.append(f"setblock {mid_x} {y_deck} {z_t2} minecraft:detector_rail[shape=east_west]")

    elif axis.upper() == "Z":
        start_z = min(z1, z2)
        end_z = max(z1, z2)
        center_x = x1
        x_t1 = center_x - 1  # Track 1 (Southbound: +Z)
        x_med = center_x     # Center Median: 1-block space
        x_t2 = center_x + 1  # Track 2 (Northbound: -Z)

        # 1. 3-block vertical passenger air clearance envelope above rails (Y=65..67)
        commands.append(f"fill {x_t1} {y_deck + 1} {start_z} {x_t2} {y_deck + 3} {end_z} minecraft:air keep")
        # Ensure median block at rail level Y=64 is clear
        commands.append(f"fill {x_med} {y_deck} {start_z} {x_med} {y_deck} {end_z} minecraft:air keep")

        # 2. Sub-surface roadbed foundation at Y=63
        commands.append(f"fill {x_t1} {y_roadbed} {start_z} {x_t2} {y_roadbed} {end_z} {roadbed_block}")

        # 3. Rails at Y=64
        commands.append(f"fill {x_t1} {y_deck} {start_z} {x_t1} {y_deck} {end_z} minecraft:rail[shape=north_south]")
        commands.append(f"fill {x_t2} {y_deck} {start_z} {x_t2} {y_deck} {end_z} minecraft:rail[shape=north_south]")

        # 4. Concealed sub-surface powering every 15 blocks
        for z in range(start_z, end_z + 1):
            step = z - start_z
            if step % power_interval == 0:
                # Track 1 powered rail + subfloor redstone block
                commands.append(f"setblock {x_t1} {y_roadbed} {z} minecraft:redstone_block")
                commands.append(f"setblock {x_t1} {y_deck} {z} minecraft:powered_rail[shape=north_south]")
                # Track 2 powered rail + subfloor redstone block
                commands.append(f"setblock {x_t2} {y_roadbed} {z} minecraft:redstone_block")
                commands.append(f"setblock {x_t2} {y_deck} {z} minecraft:powered_rail[shape=north_south]")

        # 5. End buffers / terminal stops
        commands.append(f"setblock {x_t1} {y_deck} {start_z - 1} {roadbed_block}")
        commands.append(f"setblock {x_t1} {y_deck} {end_z + 1} {roadbed_block}")
        commands.append(f"setblock {x_t2} {y_deck} {start_z - 1} {roadbed_block}")
        commands.append(f"setblock {x_t2} {y_deck} {end_z + 1} {roadbed_block}")

        # 6. Telemetry Sensor Installation at midpoint
        if install_telemetry:
            mid_z = (start_z + end_z) // 2
            if (mid_z - start_z) % power_interval == 0:
                mid_z += 1
            commands.append(
                f"setblock {x_t1} {y_roadbed} {mid_z} "
                f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T1_SOUTHBOUND_SPEED_8.0\"}}"
            )
            commands.append(f"setblock {x_t1} {y_deck} {mid_z} minecraft:detector_rail[shape=north_south]")
            commands.append(
                f"setblock {x_t2} {y_roadbed} {mid_z} "
                f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:CART_PASS DATA:DUAL_TRACK_T2_NORTHBOUND_SPEED_8.0\"}}"
            )
            commands.append(f"setblock {x_t2} {y_deck} {mid_z} minecraft:detector_rail[shape=north_south]")
    else:
        raise ValueError(f"Unsupported axis: {axis}. Use 'X' or 'Z'.")

    return commands


def build_dual_track_schematic(
    length: int = 31,
    power_interval: int = 15,
    roadbed_block: str = "minecraft:polished_deepslate"
) -> tuple[mcschematic.MCSchematic, dict, dict]:
    """
    Synthesizes a modular dual-track pair schematic:
    - Width 3 (Track 1 at x=0, Median at x=1, Track 2 at x=2)
    - 3-block vertical clearance envelope at y=2..4 (air)
    - Subsurface roadbed at y=0
    - Powered rails every 15 blocks (z % power_interval == 0)
    """
    if mcschematic is None:
        raise RuntimeError("mcschematic module not available")

    schem = mcschematic.MCSchematic()
    w = 3
    h = 5
    l = length

    # Base roadbed y=0
    for x in range(w):
        for z in range(l):
            schem.setBlock((x, 0, z), roadbed_block)

    # 3-block vertical clearance envelope y=2..4
    for x in range(w):
        for z in range(l):
            for y in range(2, 5):
                schem.setBlock((x, y, z), "minecraft:air")

    # Center median x=1 at y=1 is air
    for z in range(l):
        schem.setBlock((1, 1, z), "minecraft:air")

    # Rails at y=1 on Track 1 (x=0) and Track 2 (x=2)
    for z in range(l):
        if z % power_interval == 0:
            schem.setBlock((0, 0, z), "minecraft:redstone_block")
            schem.setBlock((0, 1, z), "minecraft:powered_rail[shape=north_south]")
            schem.setBlock((2, 0, z), "minecraft:redstone_block")
            schem.setBlock((2, 1, z), "minecraft:powered_rail[shape=north_south]")
        else:
            schem.setBlock((0, 1, z), "minecraft:rail[shape=north_south]")
            schem.setBlock((2, 1, z), "minecraft:rail[shape=north_south]")

    dims = {"width": w, "height": h, "length": l}
    meta = {
        "fixture": "DUAL_TRACK_PAIR_CORRIDOR",
        "power_interval": power_interval,
        "median_width": 1,
        "clearance_height": 3,
        "roadbed_block": roadbed_block
    }
    return schem, dims, meta


def build_station_terminal_pavilion(
    x: int, y: int, z: int,
    facing: str = "east", station_name: str = "Terminal Pavilion"
) -> list[str]:
    """
    Construct a standardized 5x7 covered terminal station pavilion.
    Enforces 3-block lateral setback from building facades to prevent clipping.
    Includes stone brick foundation, spruce fence boarding gates, warm lighting,
    and detector rail telemetry trigger.
    """
    commands = []
    w, l = 5, 7
    half_w = w // 2

    # Foundation deck at Y-1 (Y=63)
    for dx in range(-half_w, half_w + 1):
        for dz in range(l):
            commands.append(f"setblock {x + dx} {y - 1} {z + dz} minecraft:stone_bricks")
            for dy in range(4):
                commands.append(f"setblock {x + dx} {y + dy} {z + dz} minecraft:air keep")

    # Corner support pillars (Polished Deepslate)
    for dx in (-half_w, half_w):
        for dz in (0, l - 1):
            for dy in range(4):
                commands.append(f"setblock {x + dx} {y + dy} {z + dz} minecraft:polished_deepslate")

    # Roof canopy at Y+4 (Stone Brick Slabs)
    for dx in range(-half_w - 1, half_w + 2):
        for dz in range(-1, l + 1):
            commands.append(f"setblock {x + dx} {y + 4} {z + dz} minecraft:stone_brick_slab[type=top]")

    # Center arrival/departure track
    track_axis = "north_south" if facing in ("north", "south") else "east_west"
    for dz in range(l):
        if dz == l // 2:
            # Detector rail triggers telemetry packet
            commands.append(f"setblock {x} {y} {z + dz} minecraft:detector_rail[shape={track_axis}]")
        elif dz in (0, l - 1):
            commands.append(f"setblock {x} {y - 1} {z + dz} minecraft:redstone_block")
            commands.append(f"setblock {x} {y} {z + dz} minecraft:powered_rail[shape={track_axis}]")
        else:
            commands.append(f"setblock {x} {y} {z + dz} minecraft:rail[shape={track_axis}]")

    # Boarding gates and platform railings along outer edge
    for dz in range(1, l - 1):
        if dz == l // 2:
            commands.append(f"setblock {x + half_w} {y} {z + dz} minecraft:spruce_fence_gate[facing=west,open=false]")
        else:
            commands.append(f"setblock {x + half_w} {y} {z + dz} minecraft:spruce_fence")
        commands.append(f"setblock {x - half_w} {y} {z + dz} minecraft:spruce_fence")

    # Warm interior lanterns hanging from canopy
    commands.append(f"setblock {x - 1} {y + 3} {z + 2} minecraft:lantern[hanging=true]")
    commands.append(f"setblock {x + 1} {y + 3} {z + l - 3} minecraft:lantern[hanging=true]")

    return commands


def build_station_terminal(
    x: int, y: int, z: int,
    facing: str = "east",
    dest_name: str = "Orbital Loop",
    origin_name: str = "Central Depot",
    node_id: str = "CHONK-01",
    length: int = 12
) -> list[str]:
    """
    Constructs an upgraded dual-bay enclosed terminal station house:
    - Enclosed stone and stone_bricks shell with recessed glass viewing windows
      and separate 2x3 inbound/outbound portal openings.
    - Polished andesite platform deck (Y) with stone_bricks wainscoting (Y+1)
      and ceiling-hung lanterns (lantern[hanging=true]).
    - 2-block-wide polished andesite center island with recessed shroomlight spine.
    - Recessed track troughs (Y-1) with detector_rail + powered_rail launch/arrestor
      array and oak_button on end-cap polished andesite block.
    - Directional oak_wall_sign placards over each portal ('Depart: ...' / 'Arrive: from ...').
    - Strictly validated against AI Containment boundaries.
    """
    if not validate_coordinates(x, z, margin=20):
        raise ValueError(
            f"Station terminal coordinates ({x}, {y}, {z}) exceed AI Containment boundaries "
            f"X in [{CONTAINMENT_BOUNDS['min_x']}, {CONTAINMENT_BOUNDS['max_x']}], "
            f"Z in [{CONTAINMENT_BOUNDS['min_z']}, {CONTAINMENT_BOUNDS['max_z']}]."
        )

    commands = []

    if facing.lower() in ("east", "west"):
        track_axis = "east_west"
        sign_facing = "east" if facing.lower() == "east" else "west"
        btn_facing = "east" if facing.lower() == "east" else "west"
        cap_step = 1 if facing.lower() == "east" else -1

        x1 = min(x, x + (length - 1 if facing.lower() == "east" else -(length - 1)))
        x2 = max(x, x + (length - 1 if facing.lower() == "east" else -(length - 1)))

        x_port = x2 if facing.lower() == "east" else x1
        x_cap = x1 if facing.lower() == "east" else x2

        # Transverse coordinates (Z axis): 8-block hall width
        z_wall_n = z - 4
        z_plat_n = z - 3
        z_t1 = z - 2       # Track 1: Arrival / Inbound
        z_isle_1 = z - 1   # Center Island (left)
        z_isle_2 = z       # Center Island (right) -> 2-block wide center island
        z_t2 = z + 1       # Track 2: Departure / Outbound
        z_plat_s = z + 2
        z_wall_s = z + 3

        # 1. Base foundation floor at Y-2
        commands.append(f"fill {x1} {y - 2} {z_wall_n} {x2} {y - 2} {z_wall_s} minecraft:stone")

        # 2. Recessed Track Troughs at Y-1
        commands.append(f"fill {x1} {y - 1} {z_t1} {x2} {y - 1} {z_t1} minecraft:rail[shape={track_axis}]")
        commands.append(f"fill {x1} {y - 1} {z_t2} {x2} {y - 1} {z_t2} minecraft:rail[shape={track_axis}]")

        # 3. Platform decks at Y (polished andesite)
        commands.append(f"fill {x1} {y} {z_plat_n} {x2} {y} {z_plat_n} minecraft:polished_andesite")
        commands.append(f"fill {x1} {y} {z_plat_s} {x2} {y} {z_plat_s} minecraft:polished_andesite")
        # 2-block wide center island platform
        commands.append(f"fill {x1} {y} {z_isle_1} {x2} {y} {z_isle_2} minecraft:polished_andesite")

        # 4. Recessed Shroomlight spine along center island
        for xi in range(x1 + 2, x2 - 1, 3):
            commands.append(f"setblock {xi} {y} {z_isle_1} minecraft:shroomlight")
            commands.append(f"setblock {xi} {y} {z_isle_2} minecraft:shroomlight")

        # 5. Clear passenger interior air envelope
        commands.append(f"fill {x1 + 1} {y} {z_t1} {x2 - 1} {y + 3} {z_t1} minecraft:air keep")
        commands.append(f"fill {x1 + 1} {y} {z_t2} {x2 - 1} {y + 3} {z_t2} minecraft:air keep")
        commands.append(f"fill {x1 + 1} {y + 1} {z_plat_n} {x2 - 1} {y + 3} {z_plat_s} minecraft:air keep")

        # 6. Stone bricks wainscoting at Y+1
        commands.append(f"fill {x1} {y + 1} {z_wall_n} {x2} {y + 1} {z_wall_n} minecraft:stone_bricks")
        commands.append(f"fill {x1} {y + 1} {z_wall_s} {x2} {y + 1} {z_wall_s} minecraft:stone_bricks")
        commands.append(f"fill {x1 + 1} {y + 1} {z_plat_n} {x2 - 1} {y + 1} {z_plat_n} minecraft:stone_brick_stairs[half=bottom,facing=south]")
        commands.append(f"fill {x1 + 1} {y + 1} {z_plat_s} {x2 - 1} {y + 1} {z_plat_s} minecraft:stone_brick_stairs[half=bottom,facing=north]")

        # 7. Enclosed stone/stone_bricks shell with recessed glass viewing windows
        commands.append(f"fill {x1} {y} {z_wall_n} {x2} {y + 4} {z_wall_n} minecraft:stone")
        commands.append(f"fill {x1} {y + 1} {z_wall_n} {x2} {y + 1} {z_wall_n} minecraft:stone_bricks")
        commands.append(f"fill {x1 + 2} {y + 2} {z_wall_n} {x2 - 2} {y + 3} {z_wall_n} minecraft:glass")

        commands.append(f"fill {x1} {y} {z_wall_s} {x2} {y + 4} {z_wall_s} minecraft:stone")
        commands.append(f"fill {x1} {y + 1} {z_wall_s} {x2} {y + 1} {z_wall_s} minecraft:stone_bricks")
        commands.append(f"fill {x1 + 2} {y + 2} {z_wall_s} {x2 - 2} {y + 3} {z_wall_s} minecraft:glass")

        # 8. End walls: closed bumper end & portal arrival/departure end
        commands.append(f"fill {x_cap} {y} {z_wall_n} {x_cap} {y + 4} {z_wall_s} minecraft:stone_bricks")
        commands.append(f"fill {x_port} {y} {z_wall_n} {x_port} {y + 4} {z_wall_s} minecraft:stone_bricks")

        # Separate 2x3 portal openings at x_port:
        # Inbound portal (Track 1)
        commands.append(f"fill {x_port} {y} {z_plat_n} {x_port} {y + 2} {z_t1} minecraft:air")
        commands.append(
            f"setblock {x_port} {y + 3} {z_t1} "
            f"minecraft:oak_wall_sign[facing={sign_facing}]{{front_text:{{messages:['\"Arrive:\"','\"from {origin_name}\"','\"\"','\"\"']}}}}"
        )

        # Outbound portal (Track 2)
        commands.append(f"fill {x_port} {y} {z_t2} {x_port} {y + 2} {z_plat_s} minecraft:air")
        commands.append(
            f"setblock {x_port} {y + 3} {z_t2} "
            f"minecraft:oak_wall_sign[facing={sign_facing}]{{front_text:{{messages:['\"Depart:\"','\"{dest_name}\"','\"\"','\"\"']}}}}"
        )

        # 9. Recessed Track Launch/Arrestor Array with End-Cap Button
        # End cap block at x_cap
        commands.append(f"setblock {x_cap} {y - 1} {z_t1} minecraft:polished_andesite")
        commands.append(f"setblock {x_cap} {y} {z_t1} minecraft:polished_andesite")
        commands.append(f"setblock {x_cap + cap_step} {y} {z_t1} minecraft:oak_button[facing={btn_facing}]")

        commands.append(f"setblock {x_cap} {y - 1} {z_t2} minecraft:polished_andesite")
        commands.append(f"setblock {x_cap} {y} {z_t2} minecraft:polished_andesite")
        commands.append(f"setblock {x_cap + cap_step} {y} {z_t2} minecraft:oak_button[facing={btn_facing}]")

        # Launch rails and telemetry detector array
        x_l1 = x_cap + cap_step
        commands.append(f"setblock {x_l1} {y - 2} {z_t1} minecraft:redstone_block")
        commands.append(f"setblock {x_l1} {y - 1} {z_t1} minecraft:powered_rail[shape={track_axis}]")
        commands.append(f"setblock {x_l1} {y - 2} {z_t2} minecraft:redstone_block")
        commands.append(f"setblock {x_l1} {y - 1} {z_t2} minecraft:powered_rail[shape={track_axis}]")

        x_l2 = x_cap + cap_step * 2
        commands.append(
            f"setblock {x_l2} {y - 2} {z_t1} "
            f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:STATION_LAUNCH TRACK:T1\"}}"
        )
        commands.append(f"setblock {x_l2} {y - 1} {z_t1} minecraft:detector_rail[shape={track_axis}]")
        commands.append(
            f"setblock {x_l2} {y - 2} {z_t2} "
            f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:STATION_LAUNCH TRACK:T2\"}}"
        )
        commands.append(f"setblock {x_l2} {y - 1} {z_t2} minecraft:detector_rail[shape={track_axis}]")

        x_l3 = x_cap + cap_step * 3
        commands.append(f"setblock {x_l3} {y - 2} {z_t1} minecraft:redstone_block")
        commands.append(f"setblock {x_l3} {y - 1} {z_t1} minecraft:powered_rail[shape={track_axis}]")
        commands.append(f"setblock {x_l3} {y - 2} {z_t2} minecraft:redstone_block")
        commands.append(f"setblock {x_l3} {y - 1} {z_t2} minecraft:powered_rail[shape={track_axis}]")

        # 10. Vaulted Ceiling & Ceiling-Hung Lanterns
        commands.append(f"fill {x1} {y + 4} {z_wall_n} {x2} {y + 4} {z_wall_s} minecraft:stone_bricks")
        commands.append(f"fill {x1 + 1} {y + 4} {z_plat_n} {x2 - 1} {y + 4} {z_plat_s} minecraft:air")
        commands.append(f"fill {x1} {y + 5} {z_wall_n} {x2} {y + 5} {z_wall_s} minecraft:stone")
        for xi in range(x1 + 2, x2 - 1, 3):
            commands.append(f"setblock {xi} {y + 3} {z_isle_1} minecraft:lantern[hanging=true]")

    elif facing.lower() in ("north", "south"):
        track_axis = "north_south"
        sign_facing = "south" if facing.lower() == "south" else "north"
        btn_facing = "south" if facing.lower() == "south" else "north"
        cap_step = 1 if facing.lower() == "south" else -1

        z1 = min(z, z + (length - 1 if facing.lower() == "south" else -(length - 1)))
        z2 = max(z, z + (length - 1 if facing.lower() == "south" else -(length - 1)))

        z_port = z2 if facing.lower() == "south" else z1
        z_cap = z1 if facing.lower() == "south" else z2

        # Transverse coordinates (X axis): 8-block hall width
        x_wall_w = x - 4
        x_plat_w = x - 3
        x_t1 = x - 2       # Track 1: Arrival / Inbound
        x_isle_1 = x - 1   # Center Island (left)
        x_isle_2 = x       # Center Island (right) -> 2-block wide center island
        x_t2 = x + 1       # Track 2: Departure / Outbound
        x_plat_e = x + 2
        x_wall_e = x + 3

        # 1. Base foundation floor at Y-2
        commands.append(f"fill {x_wall_w} {y - 2} {z1} {x_wall_e} {y - 2} {z2} minecraft:stone")

        # 2. Recessed Track Troughs at Y-1
        commands.append(f"fill {x_t1} {y - 1} {z1} {x_t1} {y - 1} {z2} minecraft:rail[shape={track_axis}]")
        commands.append(f"fill {x_t2} {y - 1} {z1} {x_t2} {y - 1} {z2} minecraft:rail[shape={track_axis}]")

        # 3. Platform decks at Y (polished andesite)
        commands.append(f"fill {x_plat_w} {y} {z1} {x_plat_w} {y} {z2} minecraft:polished_andesite")
        commands.append(f"fill {x_plat_e} {y} {z1} {x_plat_e} {y} {z2} minecraft:polished_andesite")
        commands.append(f"fill {x_isle_1} {y} {z1} {x_isle_2} {y} {z2} minecraft:polished_andesite")

        # 4. Recessed Shroomlight spine along center island
        for zi in range(z1 + 2, z2 - 1, 3):
            commands.append(f"setblock {x_isle_1} {y} {zi} minecraft:shroomlight")
            commands.append(f"setblock {x_isle_2} {y} {zi} minecraft:shroomlight")

        # 5. Clear passenger interior air envelope
        commands.append(f"fill {x_t1} {y} {z1 + 1} {x_t1} {y + 3} {z2 - 1} minecraft:air keep")
        commands.append(f"fill {x_t2} {y} {z1 + 1} {x_t2} {y + 3} {z2 - 1} minecraft:air keep")
        commands.append(f"fill {x_plat_w} {y + 1} {z1 + 1} {x_plat_e} {y + 3} {z2 - 1} minecraft:air keep")

        # 6. Stone bricks wainscoting at Y+1
        commands.append(f"fill {x_wall_w} {y + 1} {z1} {x_wall_w} {y + 1} {z2} minecraft:stone_bricks")
        commands.append(f"fill {x_wall_e} {y + 1} {z1} {x_wall_e} {y + 1} {z2} minecraft:stone_bricks")
        commands.append(f"fill {x_plat_w} {y + 1} {z1 + 1} {x_plat_w} {y + 1} {z2 - 1} minecraft:stone_brick_stairs[half=bottom,facing=east]")
        commands.append(f"fill {x_plat_e} {y + 1} {z1 + 1} {x_plat_e} {y + 1} {z2 - 1} minecraft:stone_brick_stairs[half=bottom,facing=west]")

        # 7. Enclosed stone/stone_bricks shell with recessed glass viewing windows
        commands.append(f"fill {x_wall_w} {y} {z1} {x_wall_w} {y + 4} {z2} minecraft:stone")
        commands.append(f"fill {x_wall_w} {y + 1} {z1} {x_wall_w} {y + 1} {z2} minecraft:stone_bricks")
        commands.append(f"fill {x_wall_w} {y + 2} {z1 + 2} {x_wall_w} {y + 3} {z2 - 2} minecraft:glass")

        commands.append(f"fill {x_wall_e} {y} {z1} {x_wall_e} {y + 4} {z2} minecraft:stone")
        commands.append(f"fill {x_wall_e} {y + 1} {z1} {x_wall_e} {y + 1} {z2} minecraft:stone_bricks")
        commands.append(f"fill {x_wall_e} {y + 2} {z1 + 2} {x_wall_e} {y + 3} {z2 - 2} minecraft:glass")

        # 8. End walls: closed bumper end & portal arrival/departure end
        commands.append(f"fill {x_wall_w} {y} {z_cap} {x_wall_e} {y + 4} {z_cap} minecraft:stone_bricks")
        commands.append(f"fill {x_wall_w} {y} {z_port} {x_wall_e} {y + 4} {z_port} minecraft:stone_bricks")

        # Separate 2x3 portal openings at z_port:
        # Inbound portal (Track 1)
        commands.append(f"fill {x_plat_w} {y} {z_port} {x_t1} {y + 2} {z_port} minecraft:air")
        commands.append(
            f"setblock {x_t1} {y + 3} {z_port} "
            f"minecraft:oak_wall_sign[facing={sign_facing}]{{front_text:{{messages:['\"Arrive:\"','\"from {origin_name}\"','\"\"','\"\"']}}}}"
        )

        # Outbound portal (Track 2)
        commands.append(f"fill {x_t2} {y} {z_port} {x_plat_e} {y + 2} {z_port} minecraft:air")
        commands.append(
            f"setblock {x_t2} {y + 3} {z_port} "
            f"minecraft:oak_wall_sign[facing={sign_facing}]{{front_text:{{messages:['\"Depart:\"','\"{dest_name}\"','\"\"','\"\"']}}}}"
        )

        # 9. Recessed Track Launch/Arrestor Array with End-Cap Button
        commands.append(f"setblock {x_t1} {y - 1} {z_cap} minecraft:polished_andesite")
        commands.append(f"setblock {x_t1} {y} {z_cap} minecraft:polished_andesite")
        commands.append(f"setblock {x_t1} {y} {z_cap + cap_step} minecraft:oak_button[facing={btn_facing}]")

        commands.append(f"setblock {x_t2} {y - 1} {z_cap} minecraft:polished_andesite")
        commands.append(f"setblock {x_t2} {y} {z_cap} minecraft:polished_andesite")
        commands.append(f"setblock {x_t2} {y} {z_cap + cap_step} minecraft:oak_button[facing={btn_facing}]")

        # Launch rails and telemetry detector array
        z_l1 = z_cap + cap_step
        commands.append(f"setblock {x_t1} {y - 2} {z_l1} minecraft:redstone_block")
        commands.append(f"setblock {x_t1} {y - 1} {z_l1} minecraft:powered_rail[shape={track_axis}]")
        commands.append(f"setblock {x_t2} {y - 2} {z_l1} minecraft:redstone_block")
        commands.append(f"setblock {x_t2} {y - 1} {z_l1} minecraft:powered_rail[shape={track_axis}]")

        z_l2 = z_cap + cap_step * 2
        commands.append(
            f"setblock {x_t1} {y - 2} {z_l2} "
            f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:STATION_LAUNCH TRACK:T1\"}}"
        )
        commands.append(f"setblock {x_t1} {y - 1} {z_l2} minecraft:detector_rail[shape={track_axis}]")
        commands.append(
            f"setblock {x_t2} {y - 2} {z_l2} "
            f"minecraft:command_block{{Command:\"say [TELEMETRY] NODE:{node_id} EVENT:STATION_LAUNCH TRACK:T2\"}}"
        )
        commands.append(f"setblock {x_t2} {y - 1} {z_l2} minecraft:detector_rail[shape={track_axis}]")

        z_l3 = z_cap + cap_step * 3
        commands.append(f"setblock {x_t1} {y - 2} {z_l3} minecraft:redstone_block")
        commands.append(f"setblock {x_t1} {y - 1} {z_l3} minecraft:powered_rail[shape={track_axis}]")
        commands.append(f"setblock {x_t2} {y - 2} {z_l3} minecraft:redstone_block")
        commands.append(f"setblock {x_t2} {y - 1} {z_l3} minecraft:powered_rail[shape={track_axis}]")

        # 10. Vaulted Ceiling & Ceiling-Hung Lanterns
        commands.append(f"fill {x_wall_w} {y + 4} {z1} {x_wall_e} {y + 4} {z2} minecraft:stone_bricks")
        commands.append(f"fill {x_plat_w} {y + 4} {z1 + 1} {x_plat_e} {y + 4} {z2 - 1} minecraft:air")
        commands.append(f"fill {x_wall_w} {y + 5} {z1} {x_wall_e} {y + 5} {z2} minecraft:stone")
        for zi in range(z1 + 2, z2 - 1, 3):
            commands.append(f"setblock {x_isle_1} {y + 3} {zi} minecraft:lantern[hanging=true]")
    else:
        raise ValueError(f"Unsupported facing: {facing}. Use 'east', 'west', 'north', or 'south'.")

    return commands


def save_schematic_and_manifest(
    schem: mcschematic.MCSchematic,
    dims: dict,
    meta: dict,
    schematic_name: str,
    description: str
):
    """Saves .schem to project schematics, WorldEdit directory, and writes metadata manifest."""
    SCHEM_DIR.mkdir(parents=True, exist_ok=True)
    WE_SCHEM_DIR.mkdir(parents=True, exist_ok=True)

    # Save binary Sponge schematic
    schem.save(str(SCHEM_DIR), schematic_name, mcschematic.Version.JE_1_20_1)
    schem.save(str(WE_SCHEM_DIR), schematic_name, mcschematic.Version.JE_1_20_1)

    manifest = {
        "fixture_id": schematic_name,
        "description": description,
        "sector": "ai_containment_zone_alpha",
        "spatial_bounds": CONTAINMENT_BOUNDS,
        "dimensions": dims,
        "corner_invariants": {
            "uses_unpowered_rail": True,
            "subsurface_inert_roadbed": True,
            "no_redstone_block_at_vertex": True
        },
        "metadata": meta
    }

    manifest_path = SCHEM_DIR / f"{schematic_name}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Saved {schematic_name}.schem and {schematic_name}.json")


def generate_rcon_deploy_script() -> Path:
    """Generates an executable shell script with verified RCON /fill and /setblock commands."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    script_path = BIN_DIR / "deploy_containment_rail_corners.sh"

    script_content = """#!/usr/bin/env bash
# deploy_containment_rail_corners.sh
# Deploys verified 90-degree rail corners and connects AI Containment buildings.
# Enforces standard unpowered rail at corners, non-redstone roadbed, and chunk forceloading.

MCRCON="/home/minecraft/bin/mcrcon"
if [[ ! -x "$MCRCON" ]]; then
    echo "Error: $MCRCON not found or not executable"
    exit 1
fi

RCON_PASS="dinosaurExTraVaGanZa1969"

exec_rcon() {
    "$MCRCON" -H 127.0.0.1 -P 25575 -p "$RCON_PASS" "$1"
}

echo "[*] Deploying AI Containment Rail Corners..."

# 1. Northwest Corner (-1539, 64, -913): South to East
echo "[-] Placing NW Corner at -1539 64 -913 (shape=south_east)..."
exec_rcon "forceload add -1539 -913"
exec_rcon "fill -1540 65 -914 -1538 67 -912 minecraft:air keep"
exec_rcon "setblock -1539 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -913 minecraft:rail[shape=south_east]"
exec_rcon "setblock -1538 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -913 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -912 minecraft:redstone_block"
exec_rcon "forceload remove -1539 -913"

# 2. Northeast Corner (-945, 64, -913): West to South
echo "[-] Placing NE Corner at -945 64 -913 (shape=south_west)..."
exec_rcon "forceload add -945 -913"
exec_rcon "fill -946 65 -914 -944 67 -912 minecraft:air keep"
exec_rcon "setblock -945 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -913 minecraft:rail[shape=south_west]"
exec_rcon "setblock -946 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -913 minecraft:redstone_block"
exec_rcon "setblock -945 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -912 minecraft:redstone_block"
exec_rcon "forceload remove -945 -913"

# 3. Southeast Corner (-945, 64, -489): North to West
echo "[-] Placing SE Corner at -945 64 -489 (shape=north_west)..."
exec_rcon "forceload add -945 -489"
exec_rcon "fill -946 65 -490 -944 67 -488 minecraft:air keep"
exec_rcon "setblock -945 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -489 minecraft:rail[shape=north_west]"
exec_rcon "setblock -946 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -489 minecraft:redstone_block"
exec_rcon "setblock -945 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -490 minecraft:redstone_block"
exec_rcon "forceload remove -945 -489"

# 4. Southwest Corner (-1539, 64, -489): East to North
echo "[-] Placing SW Corner at -1539 64 -489 (shape=north_east)..."
exec_rcon "forceload add -1539 -489"
exec_rcon "fill -1540 65 -490 -1538 67 -488 minecraft:air keep"
exec_rcon "setblock -1539 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -489 minecraft:rail[shape=north_east]"
exec_rcon "setblock -1538 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -489 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -490 minecraft:redstone_block"
exec_rcon "forceload remove -1539 -489"

# 5. AI Lab Gateway Spur Junction (-1539, 64, -608)
echo "[-] Placing AI Lab Connector at -1539 64 -608..."
exec_rcon "forceload add -1545 -608 -1539 -608"
exec_rcon "fill -1546 65 -609 -1538 67 -607 minecraft:air keep"
exec_rcon "setblock -1539 63 -608 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -608 minecraft:rail[shape=north_west]"
exec_rcon "setblock -1540 64 -608 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1540 63 -608 minecraft:redstone_block"
exec_rcon "setblock -1545 64 -608 minecraft:detector_rail[shape=east_west]"
exec_rcon "forceload remove -1545 -608 -1539 -608"

echo "[+] Rail corners and building connectors deployed successfully."
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)
    print(f"[+] Generated RCON deployment script at {script_path}")
    return script_path


def deploy_dual_track_test_corridor(
    rcon_host: str = "127.0.0.1",
    rcon_port: int = 25575,
    rcon_pass: str = "dinosaurExTraVaGanZa1969",
    start_x: int = -1535,
    end_x: int = -1455,
    center_z: int = -608,
    power_interval: int = 15,
    node_id: str = "CHONK-01"
) -> bool:
    """
    Deploys the dual-track pair test corridor into AI Containment Zone Alpha.
    Wrapped in chunk forceloading to ensure reliable block placement.
    """
    from mcrcon import MCRcon

    min_x, max_x = min(start_x, end_x), max(start_x, end_x)
    print(f"[*] Deploying Dual-Track Pair Test Corridor: X [{min_x}, {max_x}], Z={center_z}...")
    cmds = build_dual_track_segment(
        min_x, center_z, max_x, center_z,
        axis="X",
        power_interval=power_interval,
        install_telemetry=True,
        node_id=node_id
    )

    with MCRcon(rcon_host, rcon_pass, port=rcon_port, timeout=10) as mcr:
        # Forceload the test corridor chunks
        mcr.command(f"forceload add {min_x - 1} {center_z - 2} {max_x + 1} {center_z + 2}")
        for cmd in cmds:
            mcr.command(cmd)
        mcr.command(f"forceload remove {min_x - 1} {center_z - 2} {max_x + 1} {center_z + 2}")

    print(f"[+] Successfully deployed dual-track test corridor ({len(cmds)} commands executed).")
    return True


def verify_test_track_telemetry(
    rcon_host: str = "127.0.0.1",
    rcon_port: int = 25575,
    rcon_pass: str = "dinosaurExTraVaGanZa1969",
    log_path: str = "/home/minecraft/logs/latest.log",
    start_x: int = -1535,
    end_x: int = -1455,
    center_z: int = -608,
    node_id: str = "CHONK-01",
    timeout: float = 12.0
) -> dict:
    """
    Executes live verification tests on both Track 1 (Eastbound) and Track 2 (Westbound):
    1. Spawns test cart with passenger on Track 1 and accelerates along Eastbound run.
    2. Monitors latest.log on Chonk for telemetry emission.
    3. Spawns test cart with passenger on Track 2 and accelerates along Westbound run.
    4. Monitors latest.log on Chonk for telemetry emission.
    5. Verifies regex match, event type, node, and speed.
    6. Cleans up test entities and returns verified telemetry packets.
    """
    import re
    import time
    from mcrcon import MCRcon

    TELEMETRY_PATTERN = r"\[TELEMETRY\]\s+NODE:(?P<node>\S+)\s+EVENT:(?P<event>\S+)\s+DATA:(?P<data>\S+)"
    min_x, max_x = min(start_x, end_x), max(start_x, end_x)
    z_t1 = center_z - 1
    z_t2 = center_z + 1

    results = {
        "track_1_eastbound": None,
        "track_2_westbound": None,
        "success": False
    }

    with MCRcon(rcon_host, rcon_pass, port=rcon_port, timeout=10) as mcr:
        # Keep chunks loaded during live test run
        mcr.command(f"forceload add {min_x - 1} {center_z - 2} {max_x + 1} {center_z + 2}")

        # Clean up pre-existing entities using vanilla minecraft:kill
        mcr.command("minecraft:kill @e[type=minecart]")
        mcr.command("minecraft:kill @e[type=pig]")

        # --- Test Track 1 (Eastbound) ---
        print("[*] Testing Track 1 (Eastbound: +X direction)...")
        with open(log_path, "r") as f:
            f.seek(0, 2)
            pos_t1 = f.tell()

        spawn_x1 = min_x + 1
        mcr.command(f"summon minecraft:minecart {spawn_x1} 64 {z_t1} {{Motion:[0.8,0.0,0.0],Passengers:[{{id:\"minecraft:pig\",NoAI:1b}}]}}")

        t0 = time.time()
        while time.time() - t0 < timeout:
            with open(log_path, "r") as f:
                f.seek(pos_t1)
                for line in f:
                    match = re.search(TELEMETRY_PATTERN, line)
                    if match and "T1" in match.group("data"):
                        results["track_1_eastbound"] = {
                            "node": match.group("node"),
                            "event": match.group("event"),
                            "data": match.group("data"),
                            "raw_log": line.strip(),
                            "elapsed": round(time.time() - t0, 2)
                        }
                        break
            if results["track_1_eastbound"]:
                break
            time.sleep(0.3)

        # Clear Track 1 cart
        mcr.command("minecraft:kill @e[type=minecart]")
        mcr.command("minecraft:kill @e[type=pig]")

        # --- Test Track 2 (Westbound) ---
        print("[*] Testing Track 2 (Westbound: -X direction)...")
        with open(log_path, "r") as f:
            f.seek(0, 2)
            pos_t2 = f.tell()

        spawn_x2 = max_x - 1
        mcr.command(f"summon minecraft:minecart {spawn_x2} 64 {z_t2} {{Motion:[-0.8,0.0,0.0],Passengers:[{{id:\"minecraft:pig\",NoAI:1b}}]}}")

        t0 = time.time()
        while time.time() - t0 < timeout:
            with open(log_path, "r") as f:
                f.seek(pos_t2)
                for line in f:
                    match = re.search(TELEMETRY_PATTERN, line)
                    if match and "T2" in match.group("data"):
                        results["track_2_westbound"] = {
                            "node": match.group("node"),
                            "event": match.group("event"),
                            "data": match.group("data"),
                            "raw_log": line.strip(),
                            "elapsed": round(time.time() - t0, 2)
                        }
                        break
            if results["track_2_westbound"]:
                break
            time.sleep(0.3)

        # Final cleanup
        mcr.command("minecraft:kill @e[type=minecart]")
        mcr.command("minecraft:kill @e[type=pig]")
        mcr.command(f"forceload remove {min_x - 1} {center_z - 2} {max_x + 1} {center_z + 2}")

    t1_ok = results["track_1_eastbound"] is not None
    t2_ok = results["track_2_westbound"] is not None
    results["success"] = t1_ok and t2_ok

    if results["success"]:
        print("[+] Telemetry verification PASSED for both Track 1 and Track 2!")
    else:
        print(f"[-] Telemetry verification FAILED: T1={t1_ok}, T2={t2_ok}")

    return results


def deploy_containment_perimeter_railway(
    rcon_host: str = "127.0.0.1",
    rcon_port: int = 25575,
    rcon_pass: str = "dinosaurExTraVaGanZa1969",
    segment_size: int = 64,
    power_interval: int = 15
):
    """
    Deploys and connects the complete 2,036-block perimeter railway in AI Containment Zone Alpha:
    - North Arm: (-1538, 64, -913) to (-946, 64, -913)
    - East Arm:  (-945, 64, -912) to (-945, 64, -490)
    - South Arm: (-946, 64, -489) down to (-1538, 64, -489)
    - West Arm:  (-1539, 64, -490) up to (-1539, 64, -912)
    - 4 Verified Corners with inert polished deepslate roadbeds
    - AI Lab Gateway Spur and Station Pavilion
    - Powered rail spacing every 15 blocks to maintain full minecart speed
    All operations use chunk forceloading to prevent 'position not loaded' errors.
    """
    from mcrcon import MCRcon

    print(f"[*] Connecting to Minecraft RCON on {rcon_host}:{rcon_port} for full perimeter deployment...")
    with MCRcon(rcon_host, rcon_pass, port=rcon_port, timeout=10) as mcr:
        # 1. Deploy Corners First
        print("[-] Deploying 4 Verified Perimeter Corners...")
        corners = [
            ("NW", -1539, -913, "south_east", (-1538, -913, "east_west"), (-1539, -912, "north_south")),
            ("NE", -945, -913, "south_west", (-946, -913, "east_west"), (-945, -912, "north_south")),
            ("SE", -945, -489, "north_west", (-946, -489, "east_west"), (-945, -490, "north_south")),
            ("SW", -1539, -489, "north_east", (-1538, -489, "east_west"), (-1539, -490, "north_south")),
        ]
        for name, cx, cz, shape, pow_arm1, pow_arm2 in corners:
            mcr.command(f"forceload add {cx} {cz}")
            mcr.command(f"fill {cx-1} 65 {cz-1} {cx+1} 67 {cz+1} minecraft:air")
            mcr.command(f"setblock {cx} 63 {cz} minecraft:polished_deepslate")
            mcr.command(f"setblock {cx} 64 {cz} minecraft:rail[shape={shape}]")
            # Powered departure arms
            mcr.command(f"setblock {pow_arm1[0]} 63 {pow_arm1[1]} minecraft:redstone_block")
            mcr.command(f"setblock {pow_arm1[0]} 64 {pow_arm1[1]} minecraft:powered_rail[shape={pow_arm1[2]}]")
            mcr.command(f"setblock {pow_arm2[0]} 63 {pow_arm2[1]} minecraft:redstone_block")
            mcr.command(f"setblock {pow_arm2[0]} 64 {pow_arm2[1]} minecraft:powered_rail[shape={pow_arm2[2]}]")
            mcr.command(f"forceload remove {cx} {cz}")

        # 2. Deploy AI Lab Gateway Spur & Station Pavilion
        print("[-] Deploying AI Lab Gateway Spur and Covered Station Pavilion at (-1545, 64, -608)...")
        mcr.command("forceload add -1546 -610 -1538 -606")
        mcr.command("fill -1546 65 -609 -1538 67 -607 minecraft:air keep")
        mcr.command("setblock -1539 63 -608 minecraft:polished_deepslate")
        mcr.command("setblock -1539 64 -608 minecraft:rail[shape=north_west]")
        mcr.command("fill -1544 63 -608 -1540 63 -608 minecraft:polished_deepslate")
        mcr.command("fill -1544 64 -608 -1540 64 -608 minecraft:rail[shape=east_west]")
        mcr.command("setblock -1540 63 -608 minecraft:redstone_block")
        mcr.command("setblock -1540 64 -608 minecraft:powered_rail[shape=east_west]")
        mcr.command("setblock -1545 64 -608 minecraft:detector_rail[shape=east_west]")
        # Station Pavilion at AI Lab Entrance
        station_cmds = build_station_terminal_pavilion(-1545, 64, -608, facing="east", station_name="AI Lab Gateway")
        for scmd in station_cmds:
            mcr.command(scmd)
        mcr.command("forceload remove -1546 -610 -1538 -606")

        # 3. Deploy 4 Connecting Perimeter Arms in 64-block segments
        arms = [
            ("North Arm", -1537, -947, -913, "X", "east_west"),
            ("East Arm", -911, -491, -945, "Z", "north_south"),
            ("South Arm", -947, -1537, -489, "X", "east_west"),
            ("West Arm", -491, -911, -1539, "Z", "north_south")
        ]

        for arm_name, start, end, fixed, axis, track_shape in arms:
            print(f"[-] Laying {arm_name} (range {start} to {end})...")
            step_dir = 1 if end >= start else -1
            curr = start

            while (curr <= end if step_dir > 0 else curr >= end):
                next_val = curr + (segment_size - 1) * step_dir
                if step_dir > 0 and next_val > end:
                    next_val = end
                elif step_dir < 0 and next_val < end:
                    next_val = end

                if axis == "X":
                    x1, x2 = min(curr, next_val), max(curr, next_val)
                    z = fixed
                    mcr.command(f"forceload add {x1} {z} {x2} {z}")
                    mcr.command(f"fill {x1} 65 {z-1} {x2} 67 {z+1} minecraft:air keep")
                    mcr.command(f"fill {x1} 63 {z} {x2} 63 {z} minecraft:polished_deepslate")
                    mcr.command(f"fill {x1} 64 {z} {x2} 64 {z} minecraft:rail[shape={track_shape}]")
                    for x in range(x1, x2 + 1):
                        if abs(x) % power_interval == 0:
                            mcr.command(f"setblock {x} 63 {z} minecraft:redstone_block")
                            mcr.command(f"setblock {x} 64 {z} minecraft:powered_rail[shape={track_shape}]")
                        if abs(x) % 16 == 0:
                            mcr.command(f"setblock {x} 64 {z+1} minecraft:pearlescent_froglight")
                    mcr.command(f"forceload remove {x1} {z} {x2} {z}")
                else:  # axis == 'Z'
                    z1, z2 = min(curr, next_val), max(curr, next_val)
                    x = fixed
                    mcr.command(f"forceload add {x} {z1} {x} {z2}")
                    mcr.command(f"fill {x-1} 65 {z1} {x+1} 67 {z2} minecraft:air keep")
                    mcr.command(f"fill {x} 63 {z1} {x} 63 {z2} minecraft:polished_deepslate")
                    mcr.command(f"fill {x} 64 {z1} {x} 64 {z2} minecraft:rail[shape={track_shape}]")
                    for z in range(z1, z2 + 1):
                        if abs(z) % power_interval == 0:
                            mcr.command(f"setblock {x} 63 {z} minecraft:redstone_block")
                            mcr.command(f"setblock {x} 64 {z} minecraft:powered_rail[shape={track_shape}]")
                        if abs(z) % 16 == 0:
                            mcr.command(f"setblock {x+1} 64 {z} minecraft:pearlescent_froglight")
                    mcr.command(f"forceload remove {x} {z1} {x} {z2}")

                curr = next_val + step_dir

        # 4. Ensure AI Lab Gateway Junction is clean unpowered switch over inert stone
        mcr.command("forceload add -1540 -608 -1538 -608")
        mcr.command("setblock -1539 63 -608 minecraft:polished_deepslate")
        mcr.command("setblock -1539 64 -608 minecraft:rail[shape=north_south]")
        mcr.command("forceload remove -1540 -608 -1538 -608")

    print("[+] Successfully deployed all 2,036 blocks of the AI Containment Perimeter Railway!")


def main():
    parser = argparse.ArgumentParser(description="Containment Rail & Corner Builder")
    parser.add_argument("--all", action="store_true", help="Synthesize all corner schematics and manifests")
    parser.add_argument("--rcon-script", action="store_true", help="Generate standalone RCON deployment script")
    parser.add_argument("--execute-rcon", action="store_true", help="Execute generated RCON commands immediately")
    parser.add_argument("--deploy-perimeter", action="store_true", help="Deploy the complete connected perimeter railway")
    parser.add_argument("--deploy-dual-track-test", action="store_true", help="Deploy dual-track pair test corridor")
    parser.add_argument("--verify-telemetry", action="store_true", help="Verify dual-track test track via Chonk telemetry")
    parser.add_argument("--power-interval", type=int, default=15, help="Powered rail spacing interval (default: 15)")
    args = parser.parse_args()

    # Default to generating all if no specific flags given
    if not (args.all or args.rcon_script or args.execute_rcon or args.deploy_perimeter or args.deploy_dual_track_test or args.verify_telemetry):
        args.all = True
        args.rcon_script = True

    print("[*] Initiating AI Containment Railway Corner Synthesis...")

    if args.all and mcschematic is None:
        print("Error: mcschematic is required for building schematics. Run using:")
        print("  /home/franklin/workspace/gaming/game-skynet-minecraft/.venv313/bin/python3 src/containment_rail_builder.py")
        sys.exit(1)

    if args.all:
        corners = [
            ("NW", "CONTAINMENT_ORBITAL_CORNER_NW", "Northwest 90-degree Transit Corner (shape=south_east)"),
            ("NE", "CONTAINMENT_ORBITAL_CORNER_NE", "Northeast 90-degree Transit Corner (shape=south_west)"),
            ("SE", "CONTAINMENT_ORBITAL_CORNER_SE", "Southeast 90-degree Transit Corner (shape=north_west)"),
            ("SW", "CONTAINMENT_ORBITAL_CORNER_SW", "Southwest 90-degree Transit Corner (shape=north_east)"),
        ]

        for turn_type, name, desc in corners:
            s, dims, meta = build_corner_junction_schematic(turn_type)
            save_schematic_and_manifest(s, dims, meta, name, desc)

        # Connector between AI Lab and Orbital Line
        s_conn, dims_conn, meta_conn = build_building_interconnect_schematic()
        save_schematic_and_manifest(s_conn, dims_conn, meta_conn, "CONTAINMENT_AI_LAB_CONNECTOR",
                                    "AI Containment Lab Gateway to Western Orbital Viaduct Junction")

        # Modular dual-track corridor schematic
        s_dual, dims_dual, meta_dual = build_dual_track_schematic(length=31, power_interval=args.power_interval)
        save_schematic_and_manifest(s_dual, dims_dual, meta_dual, "CONTAINMENT_DUAL_TRACK_CORRIDOR",
                                    "Modular Dual-Track Pair Corridor with 1-Block Median and 15-Block Powering")

    if args.rcon_script or args.all:
        generate_rcon_deploy_script()

    if args.execute_rcon:
        import subprocess
        script = BIN_DIR / "deploy_containment_rail_corners.sh"
        if script.exists():
            print("[*] Executing RCON deployment...")
            subprocess.run([str(script)], check=True)

    if args.deploy_perimeter:
        deploy_containment_perimeter_railway(power_interval=args.power_interval)

    if args.deploy_dual_track_test:
        deploy_dual_track_test_corridor(power_interval=args.power_interval)

    if args.verify_telemetry:
        res = verify_test_track_telemetry()
        if not res["success"]:
            sys.exit(1)

    print("[+] Railway synthesis complete.")


if __name__ == "__main__":
    main()
