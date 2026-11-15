#!/usr/bin/env python3
"""
Post-build greebling, furnishing, villager population, and railway transit linker.
Consolidated orchestrator for the Emerald Mirror & T2BM architecture.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Tool and validation paths
RCON_TOOL = "/home/franklin/.openclaw/workspace-mc/tools/rcon.py"
HEALTH_TOOL = "/home/franklin/.openclaw/workspace-mc/tools/health.py"
SAFETY_TEST = "/home/franklin/workspace/gaming/game-skynet-minecraft/test/test_schematic_boundary_safety.py"
CONTAINMENT_BUILDER = "/home/minecraft/src/containment_rail_builder.py"

# Ground-truth AI Containment Zone Alpha bounds
CONTAINMENT_BOUNDS = {
    "x": (-1539, -945),
    "z": (-913, -489),
    "y_min": 60,
    "y_max": 128,
    "y_foundation": 63,
    "y_rail": 64
}

# Supported workstation-to-villager profession mapping
PROFESSION_MAP = {
    "minecraft:smoker": "minecraft:butcher",
    "minecraft:blast_furnace": "minecraft:armorer",
    "minecraft:furnace": "minecraft:armorer",
    "minecraft:lectern": "minecraft:librarian",
    "minecraft:barrel": "minecraft:fisherman",
    "minecraft:smithing_table": "minecraft:toolsmith",
    "minecraft:grindstone": "minecraft:weaponsmith",
    "minecraft:brewing_stand": "minecraft:cleric",
    "minecraft:composter": "minecraft:farmer",
    "minecraft:fletching_table": "minecraft:fletcher",
    "minecraft:cauldron": "minecraft:leatherworker",
    "minecraft:stonecutter": "minecraft:mason",
    "minecraft:loom": "minecraft:shepherd"
}


def parse_tps_from_output(raw_str: str) -> float:
    """Parse 1-minute TPS from formatted/color-coded string or numeric input."""
    if not raw_str:
        return 20.0
    # Strip Minecraft formatting codes (§a, §6, etc.)
    cleaned = re.sub(r"§[0-9a-fk-or]", "", str(raw_str))
    # Look for decimal following colon (e.g. from 'TPS from last 1m, 5m, 15m: 19.98, ...')
    match = re.search(r":\s*(\d+(?:\.\d+)?)", cleaned)
    if not match:
        match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return 20.0


def check_tps(min_tps: float = 19.0) -> bool:
    """Check server TPS using health.py or fallback direct RCON."""
    if os.path.exists(HEALTH_TOOL):
        try:
            res = subprocess.run(
                ["python3", HEALTH_TOOL],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                diag = data.get("rcon_diagnostics", {})
                raw_tps = diag.get("tps") or data.get("tps")
                val = parse_tps_from_output(raw_tps)
                return val >= min_tps
        except Exception:
            pass

    # Direct RCON fallback
    try:
        out = rcon_execute("tps")
        val = parse_tps_from_output(out)
        return val >= min_tps
    except Exception:
        # If server is unreachable or offline, report False
        return False


def rcon_execute(cmd: str) -> str:
    """Execute command via rcon.py or direct mcrcon."""
    if os.path.exists(RCON_TOOL):
        try:
            res = subprocess.run(
                ["python3", RCON_TOOL, cmd],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return res.stdout.strip()
        except Exception as e:
            # Fall back to mcrcon directly
            pass

    try:
        from mcrcon import MCRcon
        rcon_pass = os.environ.get("MC_RCON_PASS", "dinosaurExTraVaGanZa1969")
        rcon_host = os.environ.get("MC_RCON_HOST", "127.0.0.1")
        with MCRcon(rcon_host, rcon_pass, port=25575, timeout=5) as mcr:
            return mcr.command(cmd)
    except Exception as e:
        raise RuntimeError(f"RCON execution failed for '{cmd}': {e}")


def force_load_region(x1: int, z1: int, x2: int, z2: int, enable: bool = True) -> None:
    """Manage chunk forceloading across bounding envelope."""
    action = "add" if enable else "remove"
    rcon_execute(f"forceload {action} {x1} {z1} {x2} {z2}")


def validate_boundary_safety(x: int, z: int) -> bool:
    """Ensure coordinates reside strictly within AI Containment Zone Alpha."""
    bx = CONTAINMENT_BOUNDS["x"]
    bz = CONTAINMENT_BOUNDS["z"]
    return (bx[0] <= x <= bx[1]) and (bz[0] <= z <= bz[1])


def generate_villager_summon(x: int, y: int, z: int, workstation: str = None, profession: str = None) -> str:
    """Generate deterministic summon command with locked NBT and workstation profession."""
    if not profession and workstation:
        profession = PROFESSION_MAP.get(workstation, "minecraft:mason")
    elif not profession:
        profession = "minecraft:mason"

    nbt = (
        f'{{PersistenceRequired:1b,'
        f'VillagerData:{{level:2,profession:"{profession}",type:"minecraft:plains"}}}}'
    )
    return f"summon minecraft:villager {x} {y} {z} {nbt}"


def generate_rail_corridor_commands(x1: int, z1: int, x2: int, z2: int, y_rail: int = 64) -> list[str]:
    """
    Generate single-track tunnel/bridge commands between two points conforming
    to build-containment-railway (Loop 1 rules):
    - Roadbed at Y-1 (Y=63)
    - Track at Y (Y=64)
    - Redstone block at Y-1 under powered rails (every 32 blocks)
    - 3x3 clearance envelope
    """
    commands = []
    y_bed = y_rail - 1

    # Straight line along primary axis
    dx = 1 if x2 >= x1 else -1
    dz = 1 if z2 >= z1 else -1

    current_x = x1
    current_z = z1
    step = 0

    # Handle X traversal
    if x1 != x2:
        for x in range(x1, x2 + dx, dx):
            if not validate_boundary_safety(x, current_z):
                raise ValueError(f"Rail corridor at ({x}, {current_z}) breaches AI Containment boundary!")

            # 1. Clearance envelope (3-wide x 3-high)
            for dy in range(1, 4):
                for offset in (-1, 0, 1):
                    commands.append(f"setblock {x} {y_rail + dy} {current_z + offset} minecraft:air keep")

            # 2. Roadbed and Powering
            is_powered = (step % 32 == 0)
            if is_powered:
                commands.append(f"setblock {x} {y_bed} {current_z} minecraft:redstone_block")
                commands.append(f"setblock {x} {y_rail} {current_z} minecraft:powered_rail[shape=east_west]")
            else:
                commands.append(f"setblock {x} {y_bed} {current_z} minecraft:polished_deepslate")
                commands.append(f"setblock {x} {y_rail} {current_z} minecraft:rail[shape=east_west]")

            # 3. Pier supports every 8 blocks
            if step % 8 == 0:
                for dy in range(1, 5):
                    commands.append(f"setblock {x} {y_bed - dy} {current_z} minecraft:dark_prismarine_wall keep")

            step += 1
        current_x = x2

    # Handle Z traversal
    if z1 != z2:
        for z in range(z1, z2 + dz, dz):
            if not validate_boundary_safety(current_x, z):
                raise ValueError(f"Rail corridor at ({current_x}, {z}) breaches AI Containment boundary!")

            for dy in range(1, 4):
                for offset in (-1, 0, 1):
                    commands.append(f"setblock {current_x + offset} {y_rail + dy} {z} minecraft:air keep")

            is_powered = (step % 32 == 0)
            if is_powered:
                commands.append(f"setblock {current_x} {y_bed} {z} minecraft:redstone_block")
                commands.append(f"setblock {current_x} {y_rail} {z} minecraft:powered_rail[shape=north_south]")
            else:
                commands.append(f"setblock {current_x} {y_bed} {z} minecraft:polished_deepslate")
                commands.append(f"setblock {current_x} {y_rail} {z} minecraft:rail[shape=north_south]")

            if step % 8 == 0:
                for dy in range(1, 5):
                    commands.append(f"setblock {current_x} {y_bed - dy} {z} minecraft:dark_prismarine_wall keep")

            step += 1

    return commands


def execute_pipeline(manifest_path: Path, dry_run: bool = False, skip_tps: bool = False) -> dict:
    """Orchestrate 5-stage post-build greebling & integration."""
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    if not skip_tps and not dry_run:
        if not check_tps(19.0):
            raise RuntimeError("[ABORT] Server TPS below 19.0 threshold.")

    bbox = manifest.get("bounding_box", {
        "x1": -1200, "z1": -700, "x2": -1180, "z2": -680
    })

    results = {
        "rcon_batches_executed": 0,
        "villagers_spawned": 0,
        "rail_commands_executed": 0
    }

    # Verify boundary safety for bounding box
    for x in (bbox["x1"], bbox["x2"]):
        for z in (bbox["z1"], bbox["z2"]):
            if not validate_boundary_safety(x, z):
                raise ValueError(f"Manifest bounding box point ({x}, {z}) violates AI Containment bounds.")

    if dry_run:
        print(f"[DRY-RUN] Manifest validated for bbox: {bbox}")
        results["dry_run"] = True
        return results

    # Chunk residency
    force_load_region(bbox["x1"], bbox["z1"], bbox["x2"], bbox["z2"], enable=True)

    try:
        # Stage 2 & 3: Greeble and Furniture RCON Batches
        for cmd in manifest.get("rcon_batches", []):
            rcon_execute(cmd)
            results["rcon_batches_executed"] += 1
            time.sleep(0.02)

        # Stage 4: Villager Population
        for v in manifest.get("villager_spawns", []):
            cmd = generate_villager_summon(
                v["x"], v["y"], v["z"],
                workstation=v.get("workstation"),
                profession=v.get("profession")
            )
            rcon_execute(cmd)
            results["villagers_spawned"] += 1
            time.sleep(0.02)

        # Stage 5: Railway Linker
        for stub in manifest.get("rail_stubs", []):
            dest = stub.get("target_terminus")
            if dest:
                rail_cmds = generate_rail_corridor_commands(
                    stub["x"], stub["z"],
                    dest["x"], dest["z"],
                    y_rail=stub.get("y", 64)
                )
                for rcmd in rail_cmds:
                    rcon_execute(rcmd)
                    results["rail_commands_executed"] += 1

    finally:
        force_load_region(bbox["x1"], bbox["z1"], bbox["x2"], bbox["z2"], enable=False)

    return results


def main():
    parser = argparse.ArgumentParser(description="Execute post-build greebling pipeline.")
    parser.add_argument("--manifest", required=True, type=Path, help="Build manifest JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate without live server changes")
    parser.add_argument("--skip-tps", action="store_true", help="Bypass TPS verification")
    args = parser.parse_args()

    try:
        res = execute_pipeline(args.manifest, dry_run=args.dry_run, skip_tps=args.skip_tps)
        print(f"[SUCCESS] Pipeline completed: {json.dumps(res, indent=2)}")
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
