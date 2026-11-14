#!/usr/bin/env python3
"""
Regenerates all core procedural schematics (.schem) using the upgraded greebling engine:
- builders.station2 (with platform safety lines, dual rails, curtain glass, greeble conduits)
- builders.bridge (with fluted supports, suspension cables, exterior greeble pass)
- builders.tower (with fluted columns, greeble pass, antennas)
- builders.house (with eaves, lighting, exterior greeble pass)
- builders.castle (with weathering, crenellations, exterior greeble pass)
"""

import os
import sys
import json
import glob

# Add workspace modules
sys.path.insert(0, "/home/franklin/workspace/gaming/game-skynet-minecraft/src/schematics")
import mcschematic
from builders import bridge, castle, house, tower, station2

BUILDER_MAP = {
    "BRIDGE": bridge.build_bridge,
    "CASTLE": castle.build_castle,
    "HOUSE": house.build_house,
    "TOWER": tower.build_tower,
    "STATION": station2.build,
}

SCHEM_DIR = "/home/minecraft/schematics"
WE_SCHEM_DIR = "/home/minecraft/plugins/WorldEdit/schematics"

def run_greeble_regeneration():
    json_files = sorted(glob.glob(os.path.join(SCHEM_DIR, "SKYNET_*.json")))
    print(f"Found {len(json_files)} SKYNET manifests to process...")

    regenerated = 0
    skipped = 0

    for jf in json_files:
        with open(jf, "r") as f:
            meta = json.load(f)

        bid = meta.get("build_id", "")
        parts = bid.split("_")
        if len(parts) < 2:
            skipped += 1
            continue

        btype = parts[1]
        builder_fn = BUILDER_MAP.get(btype)
        if not builder_fn:
            skipped += 1
            continue

        dims = meta.get("spatial_data", {}).get("dimensions", {})
        w = dims.get("width", 15)
        h = dims.get("height", 20)
        l = dims.get("length", 15)

        prompt = {
            "name": bid,
            "dimensions": {"width": w, "height": h, "length": l},
            "features": {
                "void_tech": True,
                "has_roof": True,
                "crenellations": True,
                "has_rail_bed": (btype in ["BRIDGE", "STATION"]),
                "vaulted_ceiling": True
            }
        }

        # Build with upgraded greeble logic
        schem = mcschematic.MCSchematic()
        builder_fn(schem, prompt)

        # Save to SCHEM_DIR
        schem.save(SCHEM_DIR, bid, mcschematic.Version.JE_1_21_1)

        # Update hardlink / copy in WorldEdit schematics directory
        we_path = os.path.join(WE_SCHEM_DIR, f"{bid}.schem")
        target_path = os.path.join(SCHEM_DIR, f"{bid}.schem")
        if os.path.exists(we_path):
            os.remove(we_path)
        os.link(target_path, we_path)

        regenerated += 1
        if regenerated % 25 == 0:
            print(f"  Regenerated {regenerated} schematics with greebling...")

    print(f"\n[DONE] Successfully regenerated {regenerated} schematics with greebling engine (skipped {skipped}).")

if __name__ == "__main__":
    run_greeble_regeneration()
