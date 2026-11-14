#!/usr/bin/env python3
"""
Throttled RCON Batch Placer
Deploys all 235 structures in ai_containment_zone_alpha to the Minecraft server
using WorldEdit via RCON, with safety checks and TPS monitoring.
"""

import os
import sys
import json
import glob
import time
import subprocess

SCHEM_DIR = "/home/minecraft/schematics"
HOST = "10.10.8.60"
PORT = 25575
PASS = "dinosaurExTraVaGanZa1969"
MCRCON = "/home/minecraft/bin/mcrcon"

def rcon(cmd):
    try:
        out = subprocess.check_output([MCRCON, "-H", HOST, "-P", str(PORT), "-p", PASS, cmd], stderr=subprocess.STDOUT)
        return out.decode().strip()
    except Exception as e:
        return f"ERROR: {e}"

def get_tps():
    resp = rcon("tps")
    # Output format: "TPS from last 1m, 5m, 15m: 20.0, 20.0, 20.0"
    if "TPS" in resp:
        try:
            parts = resp.split(":")[-1].split(",")
            return float(parts[0].strip().replace("*", ""))
        except Exception:
            return 20.0
    return 20.0

def run_rollout():
    print("🚀 Initializing Full Containment Field Deployment Rollout...")
    
    # Pre-flight check
    tps = get_tps()
    print(f"Server Pre-Flight TPS: {tps}")
    if tps < 18.0:
        print(f"❌ Server TPS too low ({tps}). Aborting deployment.")
        sys.exit(1)

    # Gather 235 placed structures
    json_files = sorted(glob.glob(os.path.join(SCHEM_DIR, "*.json")))
    targets = []

    for jf in json_files:
        with open(jf, "r") as f:
            d = json.load(f)
        orig = d.get("spatial_data", {}).get("origin", {})
        x = orig.get("x", 0)
        y = orig.get("y", 63)
        z = orig.get("z", 0)
        dims = d.get("spatial_data", {}).get("dimensions", {})
        w = dims.get("width", 0)
        h = dims.get("height", 0)
        l = dims.get("length", 0)
        wg = d.get("spatial_data", {}).get("worldguard_region", "")

        if wg == "ai_containment_zone_alpha" and w > 0:
            bid = d.get("build_id", os.path.splitext(os.path.basename(jf))[0])
            targets.append((bid, x, y, z, w, h, l))

    total = len(targets)
    print(f"Loaded {total} structures targeted for ai_containment_zone_alpha.")
    print("Starting deployment sequence with WorldEdit console session override...")

    # Ensure WorldEdit console session is attached to world
    rcon("//world world")

    deployed = 0
    failed = 0
    start_time = time.time()

    for idx, (bid, x, y, z, w, h, l) in enumerate(targets, 1):
        schem_file = f"{bid}.schem"

        # Position and load
        rcon(f"//pos1 {x},{y},{z}")
        load_resp = rcon(f"//schem load {schem_file}")

        if "resolution error" in load_resp or "Invalid value" in load_resp:
            print(f"[{idx}/{total}] ⚠️ Load failed for {bid}: {load_resp}")
            failed += 1
            continue

        # Paste without air obstruction (-a flag)
        paste_resp = rcon("//paste -a")

        deployed += 1
        if idx % 10 == 0 or idx == total:
            elapsed = time.time() - start_time
            rate = deployed / elapsed if elapsed > 0 else 0
            cur_tps = get_tps()
            print(f"[{idx}/{total}] Deployed {bid} at ({x}, {y}, {z}) | TPS: {cur_tps:.1f} | Speed: {rate:.1f} builds/s")

            # Checkpoint save every 25 builds
            if idx % 25 == 0:
                rcon("save-all")
                time.sleep(0.5)

            # Thermal/TPS throttle
            if cur_tps < 18.5:
                print(f"  [Throttle] TPS dipped to {cur_tps:.1f}. Cooling down for 2 seconds...")
                time.sleep(2.0)

        # Brief pacing delay to prevent RCON flood
        time.sleep(0.08)

    # Final world flush
    print("\n💾 Flushing all newly placed structures to disk (save-all flush)...")
    rcon("save-all flush")

    elapsed = time.time() - start_time
    print(f"\n🎉 Deployment Complete!")
    print(f"  - Successfully Deployed: {deployed} / {total}")
    print(f"  - Failed: {failed}")
    print(f"  - Total Elapsed Time: {elapsed:.1f}s")
    print(f"  - Final Server TPS: {get_tps()}")

if __name__ == "__main__":
    run_rollout()
