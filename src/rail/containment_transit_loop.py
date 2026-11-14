#!/usr/bin/env python3
"""
AI Containment Zone - Grand Orbital Transit Loop
------------------------------------------------
Computes collision-free routes between stations in ai_containment_zone_alpha,
synthesizes a high-detail 5-block-wide bi-directional rail viaduct with
powered rails, froglight illumination, and safety curbs, and deploys it
seamlessly to the live Minecraft server via RCON.

Placed in src/rail/ as part of the Skynet Rail Control Plane.
"""

import os
import sys
import glob
import json
import time
import heapq
import argparse
import subprocess

SCHEM_DIR = "/home/minecraft/schematics"
REGISTRY_PATH = "/home/franklin/workspace/gaming/game-skynet-minecraft/config/rail_registry.json"
HOST = "10.10.8.60"
PORT = 25575
PASS = "dinosaurExTraVaGanZa1969"
MCRCON = "/home/minecraft/bin/mcrcon"

# Sequence of 30 stations forming the Grand Orbital Ring around ai_containment_zone_alpha
ORBITAL_STATION_SEQUENCE = [
    # 1. North Industrial Spine (East -> West)
    "SKYNET_QUANTUM_FOUNDRY_NODE901",
    "SKYNET_STATION_1001",
    "SKYNET_STATION_3935",
    "end_industrial_station_v5",
    "SKYNET_STATION_2187",
    "SKYNET_STATION_5110",
    "SKYNET_STATION_6912",
    "SKYNET_STATION_9616",
    # 2. West Terminal Avenue (North -> South)
    "SKYNET_STATION_2691",
    "SKYNET_STATION_2072",
    "SKYNET_STATION_7397",
    "SKYNET_STATION_2212",
    "SKYNET_STATION_6074",
    "SKYNET_STATION_4249",
    "SKYNET_STATION_3018",
    # 3. South Return Line (West -> East)
    "SKYNET_STATION_4670",
    "SKYNET_STATION_9366",
    "SKYNET_STATION_7332",
    "SKYNET_STATION_4447",
    "SKYNET_STATION_4510",
    "SKYNET_STATION_3735",
    "SKYNET_STATION_1418",
    "SKYNET_STATION_7276",
    # 4. East Landmark Corridor (South -> North)
    "SKYNET_STATION_7604",
    "SKYNET_STATION_9980",
    "SKYNET_STATION_9093",
    "SKYNET_STATION_4183",
    "SKYNET_STATION_3341",
    "SKYNET_STATION_1506",
    "SKYNET_STATION_2196",
]


def rcon_exec(cmd: str) -> str:
    """Execute command via mcrcon binary."""
    try:
        out = subprocess.check_output(
            [MCRCON, "-H", HOST, "-P", str(PORT), "-p", PASS, cmd],
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        return out.decode().strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_server_tps() -> float:
    """Query current server TPS."""
    resp = rcon_exec("tps")
    if "TPS" in resp:
        try:
            parts = resp.split(":")[-1].split(",")
            return float(parts[0].strip().replace("*", ""))
        except Exception:
            return 20.0
    return 20.0


class ContainmentTransitRouter:
    """A* Pathfinding engine avoiding building bounding boxes in the containment area."""

    def __init__(self, schem_dir: str = SCHEM_DIR):
        self.schem_dir = schem_dir
        self.all_buildings = []
        self.stations = {}
        self._load_containment_data()

    def _load_containment_data(self):
        json_files = sorted(glob.glob(os.path.join(self.schem_dir, "*.json")))
        for jf in json_files:
            with open(jf, "r") as f:
                d = json.load(f)
            spatial = d.get("spatial_data", {})
            if spatial.get("worldguard_region") == "ai_containment_zone_alpha":
                dims = spatial.get("dimensions", {})
                w = dims.get("width", 0)
                l = dims.get("length", 0)
                h = dims.get("height", 0)
                if w > 0 and l > 0:
                    orig = spatial.get("origin", {})
                    bid = d.get("build_id", os.path.splitext(os.path.basename(jf))[0])
                    binfo = {
                        "id": bid,
                        "x1": orig.get("x", 0),
                        "x2": orig.get("x", 0) + w - 1,
                        "z1": orig.get("z", 0),
                        "z2": orig.get("z", 0) + l - 1,
                        "y": orig.get("y", 63),
                        "w": w,
                        "h": h,
                        "l": l,
                    }
                    self.all_buildings.append(binfo)
                    if "station" in bid.lower() or "foundry" in bid.lower():
                        self.stations[bid] = binfo

    def is_obstacle(self, x: int, z: int, ignore_ids: list) -> bool:
        """Check if (x, z) conflicts with any building (buffered for 5-wide viaduct)."""
        buffer = 2
        for b in self.all_buildings:
            if b["id"] in ignore_ids:
                continue
            if (b["x1"] - buffer) <= x <= (b["x2"] + buffer) and (
                b["z1"] - buffer
            ) <= z <= (b["z2"] + buffer):
                return True
        return False

    def astar_route(self, start: tuple, end: tuple, ignore_ids: list):
        """Orthogonal A* routing with straight-path preference."""
        sx, sz = start
        ex, ez = end
        heap = [(0, 0, sx, sz, [start])]
        visited = set()

        while heap:
            f, cost, x, z, path = heapq.heappop(heap)
            if (x, z) == (ex, ez):
                return path
            if (x, z) in visited:
                continue
            visited.add((x, z))

            for dx, dz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, nz = x + dx, z + dz
                if (nx, nz) in visited:
                    continue
                if self.is_obstacle(nx, nz, ignore_ids) and (nx, nz) != (ex, ez):
                    continue

                ncost = cost + 1
                # Penalty for changing direction encourages long straight spans
                if len(path) >= 2:
                    pdx = x - path[-2][0]
                    pdz = z - path[-2][1]
                    if (dx, dz) != (pdx, pdz):
                        ncost += 3

                h = abs(nx - ex) + abs(nz - ez)
                heapq.heappush(heap, (ncost + h, ncost, nx, nz, path + [(nx, nz)]))
        return None

    def plan_orbital_circuit(self):
        """Calculate complete connected loop across all 30 stations."""
        circuit = []
        total_blocks = 0

        for i in range(len(ORBITAL_STATION_SEQUENCE)):
            s1_id = ORBITAL_STATION_SEQUENCE[i]
            s2_id = ORBITAL_STATION_SEQUENCE[(i + 1) % len(ORBITAL_STATION_SEQUENCE)]

            s1 = self.stations[s1_id]
            s2 = self.stations[s2_id]

            s1_cx = s1["x1"] + s1["w"] // 2
            s2_cx = s2["x1"] + s2["w"] // 2

            # Pick portals closest to the destination
            p1 = (
                (s1_cx, s1["z1"])
                if abs(s1["z1"] - s2["z1"]) < abs(s1["z2"] - s2["z1"])
                else (s1_cx, s1["z2"])
            )
            p2 = (
                (s2_cx, s2["z1"])
                if abs(s2["z1"] - p1[1]) < abs(s2["z2"] - p1[1])
                else (s2_cx, s2["z2"])
            )

            path = self.astar_route(p1, p2, [s1_id, s2_id])
            if not path:
                raise RuntimeError(f"Failed to find route from {s1_id} to {s2_id}!")

            circuit.append(
                {
                    "from_station": s1_id,
                    "to_station": s2_id,
                    "y_start": s1["y"] + 1,
                    "y_end": s2["y"] + 1,
                    "path": path,
                }
            )
            total_blocks += len(path)

        return circuit, total_blocks


class ContainmentViaductBuilder:
    """Translates 2D centerline paths into 5-block wide Minecraft commands."""

    @staticmethod
    def compress_spans(path: list) -> list:
        """Compress sequence of coordinates into contiguous straight (min, max) spans."""
        if len(path) < 2:
            return []
        spans = []
        curr_start = path[0]
        curr_dir = (path[1][0] - path[0][0], path[1][1] - path[0][1])

        for i in range(1, len(path)):
            dx = path[i][0] - path[i - 1][0]
            dz = path[i][1] - path[i - 1][1]
            if (dx, dz) != curr_dir:
                spans.append((curr_start, path[i - 1], curr_dir))
                curr_start = path[i - 1]
                curr_dir = (dx, dz)
        spans.append((curr_start, path[-1], curr_dir))
        return spans

    @classmethod
    def generate_commands_for_segment(cls, segment: dict) -> list:
        """
        Generate fill and setblock commands for a 5-wide viaduct:
          - Deck: polished_deepslate foundation
          - Dual Track: powered_rail on redstone_block (X-1 and X+1)
          - Median: yellow_concrete caution line with pearlescent froglights
          - Curbs: dark_prismarine_wall
          - Clearance: 3-block high air envelope
        """
        cmds = []
        path = segment["path"]
        y_track = segment["y_start"]
        spans = cls.compress_spans(path)

        for start_pt, end_pt, direction in spans:
            x1, z1 = start_pt
            x2, z2 = end_pt
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_z, max_z = min(z1, z2), max(z1, z2)

            is_z_run = direction[0] == 0

            if is_z_run:
                # Running along Z axis
                # Foundation deck
                cmds.append(
                    f"fill {min_x-2} {y_track-1} {min_z} {max_x+2} {y_track-1} {max_z} minecraft:polished_deepslate"
                )
                # Redstone power conductors under rails
                cmds.append(
                    f"fill {min_x-1} {y_track-1} {min_z} {min_x-1} {y_track-1} {max_z} minecraft:redstone_block"
                )
                cmds.append(
                    f"fill {min_x+1} {y_track-1} {min_z} {min_x+1} {y_track-1} {max_z} minecraft:redstone_block"
                )
                # Median line
                cmds.append(
                    f"fill {min_x} {y_track-1} {min_z} {max_x} {y_track-1} {max_z} minecraft:yellow_concrete"
                )
                # Dual Powered Rails
                cmds.append(
                    f"fill {min_x-1} {y_track} {min_z} {min_x-1} {y_track} {max_z} minecraft:powered_rail"
                )
                cmds.append(
                    f"fill {min_x+1} {y_track} {min_z} {min_x+1} {y_track} {max_z} minecraft:powered_rail"
                )
                # Guardrails
                cmds.append(
                    f"fill {min_x-2} {y_track} {min_z} {min_x-2} {y_track} {max_z} minecraft:dark_prismarine_wall"
                )
                cmds.append(
                    f"fill {min_x+2} {y_track} {min_z} {min_x+2} {y_track} {max_z} minecraft:dark_prismarine_wall"
                )
                # 3-Block Vertical Clearance Envelope
                cmds.append(
                    f"fill {min_x-1} {y_track+1} {min_z} {max_x+1} {y_track+3} {max_z} minecraft:air"
                )

                # Periodic Froglight Lamps along median (every 10 blocks)
                for cz in range(min_z, max_z + 1, 10):
                    cmds.append(
                        f"setblock {min_x} {y_track} {cz} minecraft:pearlescent_froglight"
                    )

            else:
                # Running along X axis
                # Foundation deck
                cmds.append(
                    f"fill {min_x} {y_track-1} {min_z-2} {max_x} {y_track-1} {max_z+2} minecraft:polished_deepslate"
                )
                # Redstone power conductors under rails
                cmds.append(
                    f"fill {min_x} {y_track-1} {min_z-1} {max_x} {y_track-1} {min_z-1} minecraft:redstone_block"
                )
                cmds.append(
                    f"fill {min_x} {y_track-1} {min_z+1} {max_x} {y_track-1} {min_z+1} minecraft:redstone_block"
                )
                # Median line
                cmds.append(
                    f"fill {min_x} {y_track-1} {min_z} {max_x} {y_track-1} {max_z} minecraft:yellow_concrete"
                )
                # Dual Powered Rails
                cmds.append(
                    f"fill {min_x} {y_track} {min_z-1} {max_x} {y_track} {min_z-1} minecraft:powered_rail"
                )
                cmds.append(
                    f"fill {min_x} {y_track} {min_z+1} {max_x} {y_track} {min_z+1} minecraft:powered_rail"
                )
                # Guardrails
                cmds.append(
                    f"fill {min_x} {y_track} {min_z-2} {max_x} {y_track} {min_z-2} minecraft:dark_prismarine_wall"
                )
                cmds.append(
                    f"fill {min_x} {y_track} {min_z+2} {max_x} {y_track} {min_z+2} minecraft:dark_prismarine_wall"
                )
                # 3-Block Vertical Clearance Envelope
                cmds.append(
                    f"fill {min_x} {y_track+1} {min_z-1} {max_x} {y_track+3} {max_z+1} minecraft:air"
                )

                # Periodic Froglight Lamps along median (every 10 blocks)
                for cx in range(min_x, max_x + 1, 10):
                    cmds.append(
                        f"setblock {cx} {y_track} {min_z} minecraft:pearlescent_froglight"
                    )

        # Place standard rail at corner turning junctions to allow smooth curvature
        for i in range(1, len(spans)):
            cx, cz = spans[i][0]
            # Replace corner tracks with standard rail
            cmds.append(
                f"setblock {cx-1} {y_track} {cz} minecraft:rail"
            )
            cmds.append(
                f"setblock {cx+1} {y_track} {cz} minecraft:rail"
            )
            cmds.append(
                f"setblock {cx} {y_track} {cz-1} minecraft:rail"
            )
            cmds.append(
                f"setblock {cx} {y_track} {cz+1} minecraft:rail"
            )
            cmds.append(
                f"setblock {cx} {y_track} {cz} minecraft:pearlescent_froglight"
            )

        return cmds


def update_rail_registry(circuit: list):
    """Register all 30 stations and loop segments into config/rail_registry.json."""
    if not os.path.exists(REGISTRY_PATH):
        print(f"Registry file not found at {REGISTRY_PATH}, skipping.")
        return

    with open(REGISTRY_PATH, "r") as f:
        data = json.load(f)

    if "containment_transit_loop" not in data:
        data["containment_transit_loop"] = {}

    stations_meta = {}
    for seg in circuit:
        sid = seg["from_station"]
        start_pt = seg["path"][0]
        stations_meta[sid] = {
            "name": f"Station {sid}",
            "coords": {"x": start_pt[0], "y": seg["y_start"], "z": start_pt[1]},
            "next_station": seg["to_station"],
            "track_type": "bi_directional_orbital_loop",
        }

    data["containment_transit_loop"]["active"] = True
    data["containment_transit_loop"]["total_stations"] = len(stations_meta)
    data["containment_transit_loop"]["stations"] = stations_meta
    data["containment_transit_loop"]["last_synced"] = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Successfully updated {REGISTRY_PATH} with 30 orbital loop stations.")


def main():
    parser = argparse.ArgumentParser(
        description="Grand Orbital Transit Loop Connector for AI Containment Area"
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Execute deployment of viaducts into live server via RCON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate paths and print statistics without placing blocks",
    )
    args = parser.parse_args()

    print("═══════════════════════════════════════════════════════════════════")
    print(" 🚀 SKYNET RAIL CONTROL PLANE: AI CONTAINMENT ORBITAL TRANSIT LOOP ")
    print("═══════════════════════════════════════════════════════════════════")

    router = ContainmentTransitRouter()
    print(f"Loaded {len(router.all_buildings)} buildings and {len(router.stations)} stations.")

    print("\nCalculating collision-free circuit paths across 30 perimeter stations...")
    circuit, total_track_blocks = router.plan_orbital_circuit()

    print(f"✅ Successfully computed closed orbital loop!")
    print(f"  - Total Stations Connected: {len(circuit)}")
    print(f"  - Total Trackway Distance: {total_track_blocks:,} blocks (~{total_track_blocks/1000:.2f} km)")
    print(f"  - Estimated Transit Time: ~{total_track_blocks / 8.0:.1f} seconds (~{total_track_blocks / 8.0 / 60:.1f} minutes)")

    # Always update registry
    update_rail_registry(circuit)

    if not args.deploy:
        print("\n[Dry Run Complete] To build the viaduct in-game, run with --deploy.")
        return

    # Deploy Phase
    print("\n🚀 Beginning Live In-Game Construction Sequence via RCON...")
    pre_tps = get_server_tps()
    print(f"Server Pre-Flight TPS: {pre_tps:.1f}")

    # Ensure WorldEdit console world context
    rcon_exec("//world world")

    total_cmds = 0
    start_time = time.time()

    for idx, segment in enumerate(circuit, 1):
        s1 = segment["from_station"]
        s2 = segment["to_station"]
        cmds = ContainmentViaductBuilder.generate_commands_for_segment(segment)

        # Force-load bounding box for this segment to avoid unloaded chunk errors
        p_xs = [p[0] for p in segment["path"]]
        p_zs = [p[1] for p in segment["path"]]
        min_x, max_x = min(p_xs), max(p_xs)
        min_z, max_z = min(p_zs), max(p_zs)

        rcon_exec(f"forceload add {min_x} {min_z} {max_x} {max_z}")

        # Execute viaduct commands
        for cmd in cmds:
            rcon_exec(cmd)
            total_cmds += 1

        # Clean up chunk tickets
        rcon_exec(f"forceload remove {min_x} {min_z} {max_x} {max_z}")

        cur_tps = get_server_tps()
        print(f"[{idx:02d}/{len(circuit)}] Linked {s1} ➔ {s2} ({len(segment['path'])} blocks, {len(cmds)} commands) | TPS: {cur_tps:.1f}")

        # Thermal/TPS throttle
        if cur_tps < 18.5:
            print(f"  [Throttle] TPS dipped to {cur_tps:.1f}. Cooling down 1.5s...")
            time.sleep(1.5)

        time.sleep(0.05)

    # Final cleanup of any lingering force loads
    rcon_exec("forceload remove all")
    rcon_exec("save-all flush")

    elapsed = time.time() - start_time
    final_tps = get_server_tps()
    print("\n🎉 Containment Orbital Rail Loop Deployment Complete!")
    print(f"  - Total Commands Executed: {total_cmds}")
    print(f"  - Elapsed Time: {elapsed:.1f}s")
    print(f"  - Final Server TPS: {final_tps:.1f}")


if __name__ == "__main__":
    main()
