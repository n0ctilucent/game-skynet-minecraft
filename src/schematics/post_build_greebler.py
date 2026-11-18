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
from typing import Union

# Tool and validation paths
RCON_TOOL = "/home/franklin/.openclaw/workspace-mc/tools/rcon.py"
HEALTH_TOOL = "/home/franklin/.openclaw/workspace-mc/tools/health.py"
SAFETY_TEST = "/home/franklin/workspace/gaming/game-skynet-minecraft/test/test_schematic_boundary_safety.py"
CONTAINMENT_BUILDER = "/home/minecraft/src/containment_rail_builder.py"

# Ensure builders path is available for urban_greebler
BUILDERS_DIR = "/home/franklin/workspace/gaming/game-skynet-minecraft/src/schematics/builders"
if BUILDERS_DIR not in sys.path:
    sys.path.insert(0, BUILDERS_DIR)

import urban_greebler

# Ground-truth AI Containment Zone Alpha bounds
CONTAINMENT_BOUNDS = {
    "x": (-1539, -945),
    "z": (-913, -489),
    "y_min": 60,
    "y_max": 128,
    "y_foundation": 63,
    "y_street": 64
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


_MCR_SESSION = None

def get_rcon_session():
    global _MCR_SESSION
    if _MCR_SESSION is not None:
        return _MCR_SESSION
    try:
        from mcrcon import MCRcon
        rcon_pass = os.environ.get("MC_RCON_PASS", "dinosaurExTraVaGanZa1969")
        rcon_host = os.environ.get("MC_RCON_HOST", "127.0.0.1")
        mcr = MCRcon(rcon_host, rcon_pass, port=25575, timeout=10)
        mcr.connect()
        _MCR_SESSION = mcr
        return _MCR_SESSION
    except Exception:
        return None

def close_rcon_session():
    global _MCR_SESSION
    if _MCR_SESSION is not None:
        try:
            _MCR_SESSION.disconnect()
        except Exception:
            pass
        _MCR_SESSION = None

def rcon_execute(cmd: str) -> str:
    """Execute command via persistent MCRcon session, falling back to rcon.py or direct connection."""
    mcr = get_rcon_session()
    if mcr is not None:
        try:
            return mcr.command(cmd)
        except Exception:
            global _MCR_SESSION
            _MCR_SESSION = None
            mcr = get_rcon_session()
            if mcr is not None:
                return mcr.command(cmd)

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
    """Manage chunk forceloading across bounding envelope, splitting large regions into <=128-block batches."""
    action = "add" if enable else "remove"
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_z, max_z = min(z1, z2), max(z1, z2)
    step = 128
    for x in range(min_x, max_x + 1, step):
        chunk_x2 = min(x + step - 1, max_x)
        for z in range(min_z, max_z + 1, step):
            chunk_z2 = min(z + step - 1, max_z)
            rcon_execute(f"forceload {action} {x} {z} {chunk_x2} {chunk_z2}")


def validate_boundary_safety(x: int, z: int, margin: int = 10) -> bool:
    """Ensure coordinates reside strictly within AI Containment Zone Alpha (with 10-block apron for facility interfaces)."""
    bx = CONTAINMENT_BOUNDS["x"]
    bz = CONTAINMENT_BOUNDS["z"]
    return (bx[0] - margin <= x <= bx[1] + margin) and (bz[0] - margin <= z <= bz[1] + margin)


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


def compile_urban_greebles(manifest: dict) -> list[str]:
    """Compile street-level infrastructure, human clutter, and rooftop mechanicals."""
    cmds = []
    
    # Promenades
    for p in manifest.get("street_promenades", []):
        f = p.get("from", [-1200, -700])
        t = p.get("to", [-1180, -700])
        cmds.extend(urban_greebler.build_promenade(
            f[0], f[1], t[0], t[1],
            y=p.get("y", 63), width=p.get("width", 3), seed=p.get("seed", 42)
        ))

    # Lamp posts
    for lp in manifest.get("lamp_posts", []):
        cmds.extend(urban_greebler.build_lamp_post(
            lp["x"], lp.get("y", 63), lp["z"],
            style=lp.get("style", "warm"), height=lp.get("height", 4)
        ))

    # Guardrails
    for gr in manifest.get("guardrails", []):
        f = gr.get("from", [-1200, -700])
        t = gr.get("to", [-1180, -700])
        cmds.extend(urban_greebler.build_guardrail(
            f[0], f[1], t[0], t[1], y=gr.get("y", 64)
        ))

    # Market stalls
    for ms in manifest.get("market_stalls", []):
        cmds.extend(urban_greebler.build_market_stall(
            ms["x"], ms.get("y", 63), ms["z"],
            facing=ms.get("facing", "south"), theme=ms.get("theme", "red_white")
        ))

    # Gathering nooks
    for gn in manifest.get("gathering_nooks", []):
        cmds.extend(urban_greebler.build_gathering_nook(
            gn["x"], gn.get("y", 63), gn["z"]
        ))

    # Piers
    for pr in manifest.get("piers", []):
        cmds.extend(urban_greebler.build_pier(
            pr["x"], pr.get("y_water", 62), pr["z"],
            length=pr.get("length", 6), width=pr.get("width", 3), axis=pr.get("axis", "z")
        ))

    # Chimneys
    for ch in manifest.get("chimneys", []):
        cmds.extend(urban_greebler.build_chimney_vent(
            ch["x"], ch.get("y_roof", 70), ch["z"], height=ch.get("height", 4)
        ))

    # Rooftop mechanicals
    for rm in manifest.get("rooftop_mechanicals", []):
        cmds.extend(urban_greebler.build_hvac_and_solar(
            rm["x"], rm.get("y_roof", 75), rm["z"]
        ))

    # Window boxes
    for wb in manifest.get("window_boxes", []):
        cmds.extend(urban_greebler.build_window_flower_box(
            wb["x"], wb.get("y", 65), wb["z"],
            facing=wb.get("facing", "south"), flower=wb.get("flower", "spruce_sapling")
        ))

    # Snow flora
    for sf in manifest.get("snow_flora", []):
        cmds.extend(urban_greebler.build_snow_flora(
            sf["x"], sf.get("y", 63), sf["z"]
        ))

    # Terminal station pavilions
    for st in manifest.get("stations", []):
        cmds.extend(build_station_terminal_pavilion(
            st["x"], st.get("y", 64), st["z"],
            facing=st.get("facing", "east"),
            station_name=st.get("name", "Terminal Pavilion")
        ))

    return cmds


def execute_pipeline(manifest_path: Union[Path, dict, str], dry_run: bool = False, skip_tps: bool = False) -> dict:
    """Orchestrate 4-stage post-build greebling & urban detailing."""
    if isinstance(manifest_path, dict):
        manifest = manifest_path
    else:
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
        "urban_greeble_commands_executed": 0,
        "villagers_spawned": 0,
        "rail_commands_executed": 0
    }

    # Verify boundary safety for bounding box
    for x in (bbox["x1"], bbox["x2"]):
        for z in (bbox["z1"], bbox["z2"]):
            if not validate_boundary_safety(x, z):
                raise ValueError(f"Manifest bounding box point ({x}, {z}) violates AI Containment bounds.")

    urban_cmds = compile_urban_greebles(manifest)
    results["urban_greeble_count"] = len(urban_cmds)

    if dry_run:
        print(f"[DRY-RUN] Manifest validated for bbox: {bbox}")
        print(f"[DRY-RUN] Generated {len(urban_cmds)} urban greeble commands.")
        results["dry_run"] = True
        return results

    # Chunk residency
    force_load_region(bbox["x1"], bbox["z1"], bbox["x2"], bbox["z2"], enable=True)

    try:
        # Stage 1: Base RCON Batches
        for cmd in manifest.get("rcon_batches", []):
            rcon_execute(cmd)
            results["rcon_batches_executed"] += 1
            time.sleep(0.02)

        # Stage 2 & 3: Street Infrastructure, Clutter, and Rooftop Greebles
        for cmd in urban_cmds:
            rcon_execute(cmd)
            results["urban_greeble_commands_executed"] += 1
            time.sleep(0.01)

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

        # Decoupled Architecture Note:
        # Railway construction and closed-loop interconnects are managed independently
        # by containment_rail_builder.py. Greebling strictly accentuates buildings and streetscapes.
        if "rail_stubs" in manifest:
            print("[INFO] Decoupled architecture: 'rail_stubs' ignored by post_build_greebler; "
                  "dispatch to containment_rail_builder.py for dual-track loop interconnection.")

    finally:
        force_load_region(bbox["x1"], bbox["z1"], bbox["x2"], bbox["z2"], enable=False)
        close_rcon_session()

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
