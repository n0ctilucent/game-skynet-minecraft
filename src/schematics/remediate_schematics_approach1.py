#!/usr/bin/env python3
"""
Remediation Script: Approach 1 - Physical Translation into AI Containment Field
Translates all 156 southern out-of-bounds builds into ai_containment_zone_alpha,
reclassifies spawn builds to spawn_district, and ensures zero AABB collisions.
"""

import glob
import json
import math
import os
import sys
from datetime import datetime

SCHEM_DIR = "/home/minecraft/schematics"
FIELD_MIN_X = -1539
FIELD_MAX_X = -945
FIELD_MIN_Z = -913
FIELD_MAX_Z = -489
BUFFER = 2  # Minimum 2-block buffer between builds


def collides(box, box_list, buf=BUFFER):
    for b in box_list:
        if (
            box["x1"] - buf < b["x2"]
            and box["x2"] + buf > b["x1"]
            and box["z1"] - buf < b["z2"]
            and box["z2"] + buf > b["z1"]
        ):
            return True
    return False


def run_remediation(dry_run=False):
    json_files = sorted(glob.glob(os.path.join(SCHEM_DIR, "*.json")))
    print(f"Loaded {len(json_files)} manifests from {SCHEM_DIR}")

    existing_in_bounds = []
    south_manifests = []
    spawn_manifests = []
    unknown_in_bounds = []

    for f in json_files:
        try:
            with open(f, "r") as jf:
                data = json.load(jf)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue

        orig = data.get("spatial_data", {}).get("origin", {})
        x = orig.get("x", 0)
        y = orig.get("y", 63)
        z = orig.get("z", 0)
        dims = data.get("spatial_data", {}).get("dimensions", {})
        w = dims.get("width", 0)
        h = dims.get("height", 0)
        l = dims.get("length", 0)
        wg = data.get("spatial_data", {}).get("worldguard_region", "")

        # Categorize
        if -50 <= x <= 50 and -50 <= z <= 50:
            spawn_manifests.append((f, data))
        elif FIELD_MIN_X <= x <= FIELD_MAX_X and FIELD_MIN_Z <= z <= FIELD_MAX_Z:
            if w > 0 and h > 0 and l > 0:
                existing_in_bounds.append(
                    {
                        "id": data.get("build_id", os.path.basename(f)),
                        "x1": x,
                        "y1": y,
                        "z1": z,
                        "x2": x + w,
                        "y2": y + h,
                        "z2": z + l,
                        "file": f,
                    }
                )
            if wg != "ai_containment_zone_alpha":
                unknown_in_bounds.append((f, data))
        elif FIELD_MIN_X <= x <= FIELD_MAX_X and z < FIELD_MIN_Z:
            south_manifests.append(
                {
                    "file": f,
                    "data": data,
                    "w": w,
                    "h": h,
                    "l": l,
                    "orig_x": x,
                    "orig_y": y,
                    "orig_z": z,
                }
            )

    print(f"Spawn manifests to reclassify: {len(spawn_manifests)}")
    print(f"Existing placed in-bounds builds: {len(existing_in_bounds)}")
    print(f"In-bounds manifests with unaligned tags: {len(unknown_in_bounds)}")
    print(f"South manifests to translate into field: {len(south_manifests)}")

    occupied_boxes = list(existing_in_bounds)
    repositioned_records = []
    now_iso = datetime.now().isoformat()

    # Deterministic sorting
    south_manifests.sort(key=lambda item: item["data"].get("build_id", ""))

    for item in south_manifests:
        w, h, l = item["w"], item["h"], item["l"]
        orig_x, orig_z = item["orig_x"], item["orig_z"]
        orig_y = item["orig_y"] if item["orig_y"] != 0 else 63
        bid = item["data"].get("build_id", os.path.basename(item["file"]))

        # Ideal linear projection into containment zone
        norm_z = (orig_z - (-1539)) / 594.0
        ideal_z = int(round(FIELD_MIN_Z + norm_z * (abs(FIELD_MAX_Z - FIELD_MIN_Z) - l)))
        ideal_x = min(max(orig_x, FIELD_MIN_X + 2), FIELD_MAX_X - w - 2)
        ideal_z = min(max(ideal_z, FIELD_MIN_Z + 2), FIELD_MAX_Z - l - 2)

        placed = False
        target_x, target_z = None, None

        for r in range(0, 300, 2):
            for dx in range(-r, r + 1, 2):
                for dz in (-r, r) if abs(dx) < r else range(-r, r + 1, 2):
                    tx = ideal_x + dx
                    tz = ideal_z + dz
                    if tx < FIELD_MIN_X + 2 or tx + w > FIELD_MAX_X - 2:
                        continue
                    if tz < FIELD_MIN_Z + 2 or tz + l > FIELD_MAX_Z - 2:
                        continue
                    cand = {
                        "id": bid,
                        "x1": tx,
                        "y1": orig_y,
                        "z1": tz,
                        "x2": tx + w,
                        "y2": orig_y + h,
                        "z2": tz + l,
                    }
                    if not collides(cand, occupied_boxes):
                        occupied_boxes.append(cand)
                        target_x, target_z = tx, tz
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            raise RuntimeError(f"Could not place {bid} without collision!")

        # Update metadata
        data = item["data"]
        data["spatial_data"]["origin"] = {
            "x": target_x,
            "y": orig_y,
            "z": target_z,
        }
        data["spatial_data"]["worldguard_region"] = "ai_containment_zone_alpha"

        if "provenance" not in data:
            data["provenance"] = {}
        data["provenance"]["repositioned_at"] = now_iso
        data["provenance"]["reposition_reason"] = "approach_1_boundary_alignment"
        data["provenance"]["previous_origin"] = {
            "x": orig_x,
            "y": orig_y,
            "z": orig_z,
        }

        repositioned_records.append((item["file"], data))

    # Process Spawn manifests
    spawn_records = []
    for f, data in spawn_manifests:
        data["spatial_data"]["worldguard_region"] = "spawn_district"
        if "provenance" not in data:
            data["provenance"] = {}
        data["provenance"]["repositioned_at"] = now_iso
        data["provenance"]["reposition_reason"] = "spawn_district_reclassification"
        spawn_records.append((f, data))

    # Process In-bounds unaligned tags
    tag_records = []
    for f, data in unknown_in_bounds:
        data["spatial_data"]["worldguard_region"] = "ai_containment_zone_alpha"
        tag_records.append((f, data))

    print(f"\nPrepared Updates:")
    print(f"  - Repositioned South Builds: {len(repositioned_records)}")
    print(f"  - Spawn District Reclassifications: {len(spawn_records)}")
    print(f"  - In-Bounds Region Tag Normalizations: {len(tag_records)}")

    if dry_run:
        print("\n[DRY RUN] No files modified.")
        return

    # Write files
    all_to_write = repositioned_records + spawn_records + tag_records
    for file_path, data in all_to_write:
        with open(file_path, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2)

    print(f"\nSuccessfully committed updates to {len(all_to_write)} JSON manifests.")

    # Verification: Overlap check within ai_containment_zone_alpha
    print("\nRunning Verification AABB Overlap Audit on Containment Field...")
    overlaps = []
    for i in range(len(occupied_boxes)):
        for j in range(i + 1, len(occupied_boxes)):
            b1 = occupied_boxes[i]
            b2 = occupied_boxes[j]
            if (
                b1["x1"] < b2["x2"]
                and b1["x2"] > b2["x1"]
                and b1["y1"] < b2["y2"]
                and b1["y2"] > b2["y1"]
                and b1["z1"] < b2["z2"]
                and b1["z2"] > b2["z1"]
            ):
                overlaps.append((b1, b2))

    if overlaps:
        print(f"⚠️  Verification FAILED: {len(overlaps)} overlaps found!")
        for b1, b2 in overlaps:
            print(f"  Conflict: {b1['id']} <--> {b2['id']}")
    else:
        print(f"✅ Verification PASSED: All {len(occupied_boxes)} structures in ai_containment_zone_alpha are conflict-free!")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_remediation(dry_run=dry_run)
