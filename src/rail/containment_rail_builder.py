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

try:
    import mcschematic
except ImportError:
    mcschematic = None

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
# Enforces standard unpowered rail at corners and non-redstone roadbed.

MCRCON="/home/minecraft/bin/mcrcon"
if [[ ! -x "$MCRCON" ]]; then
    echo "Error: $MCRCON not found or not executable"
    exit 1
fi

RCON_PASS="minecraft"

exec_rcon() {
    "$MCRCON" -H 127.0.0.1 -P 25575 -p "$RCON_PASS" "$1"
}

echo "[*] Deploying AI Containment Rail Corners..."

# 1. Northwest Corner (-1539, 64, -913): South to East
echo "[-] Placing NW Corner at -1539 64 -913 (shape=south_east)..."
exec_rcon "setblock -1539 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -913 minecraft:rail[shape=south_east]"
exec_rcon "setblock -1538 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -913 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -912 minecraft:redstone_block"

# 2. Northeast Corner (-945, 64, -913): West to South
echo "[-] Placing NE Corner at -945 64 -913 (shape=south_west)..."
exec_rcon "setblock -945 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -913 minecraft:rail[shape=south_west]"
exec_rcon "setblock -946 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -913 minecraft:redstone_block"
exec_rcon "setblock -945 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -912 minecraft:redstone_block"

# 3. Southeast Corner (-945, 64, -489): North to West
echo "[-] Placing SE Corner at -945 64 -489 (shape=north_west)..."
exec_rcon "setblock -945 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -489 minecraft:rail[shape=north_west]"
exec_rcon "setblock -946 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -489 minecraft:redstone_block"
exec_rcon "setblock -945 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -490 minecraft:redstone_block"

# 4. Southwest Corner (-1539, 64, -489): East to North
echo "[-] Placing SW Corner at -1539 64 -489 (shape=north_east)..."
exec_rcon "setblock -1539 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -489 minecraft:rail[shape=north_east]"
exec_rcon "setblock -1538 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -489 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -490 minecraft:redstone_block"

# 5. AI Lab Gateway Spur Junction (-1539, 64, -608)
echo "[-] Placing AI Lab Connector at -1539 64 -608..."
exec_rcon "setblock -1539 63 -608 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -608 minecraft:rail[shape=north_west]"
exec_rcon "setblock -1540 64 -608 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1540 63 -608 minecraft:redstone_block"
exec_rcon "setblock -1545 64 -608 minecraft:detector_rail[shape=east_west]"

echo "[+] Rail corners and building connectors deployed successfully."
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)
    print(f"[+] Generated RCON deployment script at {script_path}")
    return script_path


def main():
    parser = argparse.ArgumentParser(description="Containment Rail & Corner Builder")
    parser.add_argument("--all", action="store_true", help="Synthesize all corner schematics and manifests")
    parser.add_argument("--rcon-script", action="store_true", help="Generate standalone RCON deployment script")
    parser.add_argument("--execute-rcon", action="store_true", help="Execute generated RCON commands immediately")
    args = parser.parse_args()

    # Default to generating all if no specific flags given
    if not (args.all or args.rcon_script or args.execute_rcon):
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

    if args.rcon_script or args.all:
        generate_rcon_deploy_script()

    if args.execute_rcon:
        import subprocess
        script = BIN_DIR / "deploy_containment_rail_corners.sh"
        if script.exists():
            print("[*] Executing RCON deployment...")
            subprocess.run([str(script)], check=True)

    print("[+] Railway synthesis complete.")


if __name__ == "__main__":
    main()
