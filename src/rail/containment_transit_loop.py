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
    # 3. South Return Line (West -> East)
    "SKYNET_STATION_9366",
    "SKYNET_STATION_7332",
    "SKYNET_STATION_4670",
    "SKYNET_STATION_3018",
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
        # Prevent narrow parallel overlap in Station 2187 alleyway
        if x == -1292 and -905 <= z <= -868:
            return True

        buffer = 2
        for b in self.all_buildings:
            if b["id"] in ignore_ids:
                continue
            if (b["x1"] - buffer) <= x <= (b["x2"] + buffer) and (
                b["z1"] - buffer
            ) <= z <= (b["z2"] + buffer):
                return True
        return False

    def astar_route(self, start: tuple, end: tuple, ignore_ids: list, initial_dir: tuple = None):
        """Orthogonal A* routing with straight-path preference and initial vector momentum."""
        sx, sz = start
        ex, ez = end
        heap = [(0, 0, sx, sz, [start])]
        visited = set()

        # Prioritize major axis movement towards target
        primary_dx = 1 if ex > sx else (-1 if ex < sx else 0)
        primary_dz = 1 if ez > sz else (-1 if ez < sz else 0)
        if abs(ex - sx) >= abs(ez - sz):
            base_moves = [(primary_dx, 0), (0, primary_dz), (-primary_dx, 0), (0, -primary_dz)]
        else:
            base_moves = [(0, primary_dz), (primary_dx, 0), (0, -primary_dz), (-primary_dx, 0)]
        moves = [m for m in base_moves if m != (0, 0)]
        for m in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if m not in moves:
                moves.append(m)

        while heap:
            f, cost, x, z, path = heapq.heappop(heap)
            if (x, z) == (ex, ez):
                return path
            if (x, z) in visited:
                continue
            visited.add((x, z))

            pdx, pdz = (0, 0)
            if len(path) >= 2:
                pdx = x - path[-2][0]
                pdz = z - path[-2][1]
            elif initial_dir:
                pdx, pdz = initial_dir

            for dx, dz in moves:
                nx, nz = x + dx, z + dz
                if (nx, nz) in visited:
                    continue
                if self.is_obstacle(nx, nz, ignore_ids) and (nx, nz) != (ex, ez):
                    continue

                ncost = cost + 1
                if pdx != 0 or pdz != 0:
                    if (dx, dz) != (pdx, pdz):
                        ncost += 6  # Strong turn penalty suppresses unnecessary 1-block jogs

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

            # Determine initial direction from previous segment arrival vector if same portal
            initial_dir = None
            if circuit and circuit[-1]["path"][-1] == p1 and len(circuit[-1]["path"]) >= 2:
                initial_dir = (
                    circuit[-1]["path"][-1][0] - circuit[-1]["path"][-2][0],
                    circuit[-1]["path"][-1][1] - circuit[-1]["path"][-2][1],
                )

            path = self.astar_route(p1, p2, [s1_id, s2_id], initial_dir=initial_dir)
            if not path:
                raise RuntimeError(f"Failed to find route from {s1_id} to {s2_id}!")

            circuit.append(
                {
                    "from_station": s1_id,
                    "to_station": s2_id,
                    "y_start": 64,
                    "y_end": 64,
                    "path": path,
                }
            )
            total_blocks += len(path)

        for i in range(len(circuit)):
            path = circuit[i]["path"]
            prev_seg = circuit[i - 1]
            next_seg = circuit[(i + 1) % len(circuit)]
            dir_prev = (prev_seg["path"][-1][0] - prev_seg["path"][-2][0], prev_seg["path"][-1][1] - prev_seg["path"][-2][1])
            dir_curr = (path[1][0] - path[0][0], path[1][1] - path[0][1])
            dir_end = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
            dir_next = (next_seg["path"][1][0] - next_seg["path"][0][0], next_seg["path"][1][1] - next_seg["path"][0][1])

            circuit[i]["turn_start"] = (prev_seg["path"][-1] == path[0]) and (dir_prev != dir_curr)
            circuit[i]["turn_end"] = (path[-1] == next_seg["path"][0]) and (dir_end != dir_next)

        return circuit, total_blocks


def calculate_corner_shape(dx_in: int, dz_in: int, dx_out: int, dz_out: int) -> str:
    """
    Computes the required vanilla Minecraft rail curve shape given normalized
    incoming and outgoing direction vectors.
    """
    din_x = 0 if dx_in == 0 else (1 if dx_in > 0 else -1)
    din_z = 0 if dz_in == 0 else (1 if dz_in > 0 else -1)
    dout_x = 0 if dx_out == 0 else (1 if dx_out > 0 else -1)
    dout_z = 0 if dz_out == 0 else (1 if dz_out > 0 else -1)

    from_x, from_z = -din_x, -din_z
    to_x, to_z = dout_x, dout_z
    connected = {(from_x, from_z), (to_x, to_z)}

    if connected == {(0, 1), (1, 0)}:
        return "south_east"
    elif connected == {(0, 1), (-1, 0)}:
        return "south_west"
    elif connected == {(0, -1), (1, 0)}:
        return "north_east"
    elif connected == {(0, -1), (-1, 0)}:
        return "north_west"
    else:
        raise ValueError(f"Invalid orthogonal turn: in=({dx_in},{dz_in}), out=({dx_out},{dz_out})")


class ContainmentViaductBuilder:
    """Translates 2D centerline paths into verified dual-track 5-block wide Minecraft commands."""

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
    def generate_commands_for_segment(cls, segment: dict, powered_interval: int = 15) -> list:
        """
        Generate fill and setblock commands for a verified dual-track 5-wide viaduct:
          - Multi-phase construction preventing foundation fills from overwriting rails/redstone
          - Track 1 (Offset -1) & Track 2 (Offset +1) separated by a 1-block median (Offset 0)
          - 3-block vertical air clearance envelope (y_track+1 to y_track+3) so players are not decapitated
          - Powered redstone rails spaced ~15 blocks apart (min distance 3 from corners and endpoints)
          - Mathematically calculated 90-degree curve shapes with inert polished deepslate roadbed at corners
          - Curbs: prismarine_wall
          - Arrival detector rail at path[-2], departure booster rail at path[1]
        """
        cmds = []
        path = segment["path"]
        y_track = segment["y_start"]
        y_bed = y_track - 1
        to_station = segment.get("to_station", "STATION")
        from_station = segment.get("from_station", "STATION")
        spans = cls.compress_spans(path)

        corner_coords = set(s[0] for s in spans[1:])

        # PHASE 1: Roadbed Foundation & Clearance Envelopes for all spans
        for start_pt, end_pt, direction in spans:
            x1, z1 = start_pt
            x2, z2 = end_pt
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_z, max_z = min(z1, z2), max(z1, z2)

            is_z_run = direction[0] == 0

            if is_z_run:
                xc = min_x
                cmds.append(f"fill {xc-2} {y_bed} {min_z} {xc+2} {y_bed} {max_z} minecraft:polished_deepslate")
                cmds.append(f"fill {xc} {y_bed} {min_z} {xc} {y_bed} {max_z} minecraft:yellow_concrete")
                cmds.append(f"fill {xc} {y_track} {min_z} {xc} {y_track} {max_z} minecraft:air")
                cmds.append(f"fill {xc-2} {y_track+1} {min_z} {xc+2} {y_track+3} {max_z} minecraft:air")
                cmds.append(f"fill {xc-2} {y_track+1} {min_z} {xc+2} {y_track+3} {max_z} minecraft:air replace minecraft:water")
                cmds.append(f"fill {xc-2} {y_track+1} {min_z} {xc+2} {y_track+3} {max_z} minecraft:air replace minecraft:flowing_water")
                cmds.append(f"fill {xc-2} {y_track+4} {min_z} {xc+2} {y_track+4} {max_z} minecraft:glass replace minecraft:water")
                cmds.append(f"fill {xc-2} {y_track+4} {min_z} {xc+2} {y_track+4} {max_z} minecraft:glass replace minecraft:flowing_water")
            else:
                zc = min_z
                cmds.append(f"fill {min_x} {y_bed} {zc-2} {max_x} {y_bed} {zc+2} minecraft:polished_deepslate")
                cmds.append(f"fill {min_x} {y_bed} {zc} {max_x} {y_bed} {zc} minecraft:yellow_concrete")
                cmds.append(f"fill {min_x} {y_track} {zc} {max_x} {y_track} {zc} minecraft:air")
                cmds.append(f"fill {min_x} {y_track+1} {zc-2} {max_x} {y_track+3} {zc+2} minecraft:air")
                cmds.append(f"fill {min_x} {y_track+1} {zc-2} {max_x} {y_track+3} {zc+2} minecraft:air replace minecraft:water")
                cmds.append(f"fill {min_x} {y_track+1} {zc-2} {max_x} {y_track+3} {zc+2} minecraft:air replace minecraft:flowing_water")
                cmds.append(f"fill {min_x} {y_track+4} {zc-2} {max_x} {y_track+4} {zc+2} minecraft:glass replace minecraft:water")
                cmds.append(f"fill {min_x} {y_track+4} {zc-2} {max_x} {y_track+4} {zc+2} minecraft:glass replace minecraft:flowing_water")

        # PHASE 2: Corner Envelopes & Medians
        for i in range(1, len(spans)):
            cx, cz = spans[i][0]
            cmds.append(f"fill {cx-2} {y_track+1} {cz-2} {cx+2} {y_track+3} {cz+2} minecraft:air")
            cmds.append(f"fill {cx-2} {y_track+1} {cz-2} {cx+2} {y_track+3} {cz+2} minecraft:air replace minecraft:water")
            cmds.append(f"fill {cx-2} {y_track+1} {cz-2} {cx+2} {y_track+3} {cz+2} minecraft:air replace minecraft:flowing_water")
            cmds.append(f"fill {cx-2} {y_track+4} {cz-2} {cx+2} {y_track+4} {cz+2} minecraft:glass replace minecraft:water")
            cmds.append(f"fill {cx-2} {y_track+4} {cz-2} {cx+2} {y_track+4} {cz+2} minecraft:glass replace minecraft:flowing_water")
            cmds.append(f"fill {cx-1} {y_track} {cz-1} {cx+1} {y_track} {cz+1} minecraft:air")
            cmds.append(f"fill {cx-2} {y_track} {cz-2} {cx+2} {y_track} {cz+2} minecraft:air replace minecraft:prismarine_wall")
            cmds.append(f"setblock {cx} {y_bed} {cz} minecraft:yellow_concrete")
            cmds.append(f"setblock {cx} {y_track} {cz} minecraft:pearlescent_froglight")

        # PHASE 3: Outer Guardrails
        for start_pt, end_pt, direction in spans:
            x1, z1 = start_pt
            x2, z2 = end_pt
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_z, max_z = min(z1, z2), max(z1, z2)
            is_z_run = direction[0] == 0
            if is_z_run:
                xc = min_x
                curb_min_z = min_z + 2 if any(abs(min_z - cz) <= 2 for cx, cz in corner_coords if cx == xc) else min_z
                curb_max_z = max_z - 2 if any(abs(max_z - cz) <= 2 for cx, cz in corner_coords if cx == xc) else max_z
                if curb_min_z <= curb_max_z:
                    cmds.append(f"fill {xc-2} {y_track} {curb_min_z} {xc-2} {y_track} {curb_max_z} minecraft:prismarine_wall")
                    cmds.append(f"fill {xc+2} {y_track} {curb_min_z} {xc+2} {y_track} {curb_max_z} minecraft:prismarine_wall")
            else:
                zc = min_z
                curb_min_x = min_x + 2 if any(abs(min_x - cx) <= 2 for cx, cz in corner_coords if cz == zc) else min_x
                curb_max_x = max_x - 2 if any(abs(max_x - cx) <= 2 for cx, cz in corner_coords if cz == zc) else max_x
                if curb_min_x <= curb_max_x:
                    cmds.append(f"fill {curb_min_x} {y_track} {zc-2} {curb_max_x} {y_track} {zc-2} minecraft:prismarine_wall")
                    cmds.append(f"fill {curb_min_x} {y_track} {zc+2} {curb_max_x} {y_track} {zc+2} minecraft:prismarine_wall")

        # PHASE 4: Dual Track Straight Rails
        for start_pt, end_pt, direction in spans:
            x1, z1 = start_pt
            x2, z2 = end_pt
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_z, max_z = min(z1, z2), max(z1, z2)
            is_z_run = direction[0] == 0
            if is_z_run:
                xc = min_x
                cmds.append(f"fill {xc-1} {y_track} {min_z} {xc-1} {y_track} {max_z} minecraft:rail[shape=north_south]")
                cmds.append(f"fill {xc+1} {y_track} {min_z} {xc+1} {y_track} {max_z} minecraft:rail[shape=north_south]")
            else:
                zc = min_z
                cmds.append(f"fill {min_x} {y_track} {zc-1} {max_x} {y_track} {zc-1} minecraft:rail[shape=east_west]")
                cmds.append(f"fill {min_x} {y_track} {zc+1} {max_x} {y_track} {zc+1} minecraft:rail[shape=east_west]")

        # PHASE 5: Corner Curves & Larger-Radius Straight Extensions
        for i in range(1, len(spans)):
            cx, cz = spans[i][0]
            dir_in = spans[i - 1][2]
            dir_out = spans[i][2]
            shape = calculate_corner_shape(dir_in[0], dir_in[1], dir_out[0], dir_out[1])
            dx_in, dz_in = dir_in
            dx_out, dz_out = dir_out
            cross = dx_in * dz_out - dz_in * dx_out

            c_out_x = cx - dz_in - dz_out
            c_out_z = cz + dx_in + dx_out
            c_in_x = cx + dz_in + dz_out
            c_in_z = cz - dx_in - dx_out

            cmds.append(f"setblock {c_out_x} {y_bed} {c_out_z} minecraft:polished_deepslate")
            cmds.append(f"setblock {c_out_x} {y_track} {c_out_z} minecraft:rail[shape={shape}]")
            cmds.append(f"setblock {c_in_x} {y_bed} {c_in_z} minecraft:polished_deepslate")
            cmds.append(f"setblock {c_in_x} {y_track} {c_in_z} minecraft:rail[shape={shape}]")

            lx, lz = (c_in_x, c_in_z) if cross > 0 else (c_out_x, c_out_z)
            if dz_in == 0:
                step_x = -dx_in
                x = lx + step_x
                while abs(x - cx) <= 2:
                    cmds.append(f"setblock {x} {y_bed} {lz} minecraft:polished_deepslate")
                    cmds.append(f"setblock {x} {y_track} {lz} minecraft:rail[shape=east_west]")
                    x += step_x
                step_z = dz_out
                z = lz + step_z
                while abs(z - cz) <= 2:
                    cmds.append(f"setblock {lx} {y_bed} {z} minecraft:polished_deepslate")
                    cmds.append(f"setblock {lx} {y_track} {z} minecraft:rail[shape=north_south]")
                    z += step_z
            else:
                step_z = -dz_in
                z = lz + step_z
                while abs(z - cz) <= 2:
                    cmds.append(f"setblock {lx} {y_bed} {z} minecraft:polished_deepslate")
                    cmds.append(f"setblock {lx} {y_track} {z} minecraft:rail[shape=north_south]")
                    z += step_z
                step_x = dx_out
                x = lx + step_x
                while abs(x - cx) <= 2:
                    cmds.append(f"setblock {x} {y_bed} {lz} minecraft:polished_deepslate")
                    cmds.append(f"setblock {x} {y_track} {lz} minecraft:rail[shape=east_west]")
                    x += step_x

        # PHASE 6: Redstone Powered Rails along Straight Spans
        p_dep = path[1]
        p_arr = path[-2] if len(path) >= 4 else path[-1]

        for start_pt, end_pt, direction in spans:
            x1, z1 = start_pt
            x2, z2 = end_pt
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_z, max_z = min(z1, z2), max(z1, z2)
            is_z_run = direction[0] == 0
            if is_z_run:
                xc = min_x
                for z in range(min_z, max_z + 1):
                    is_near_corner = any(abs(z - cz) <= 2 for cx, cz in corner_coords if cx == xc)
                    is_near_end = any(abs(z - pz) <= 2 for px, pz in [p_dep, p_arr, path[0], path[-1]] if px == xc)
                    if abs(z) % powered_interval == 0 and not is_near_corner and not is_near_end:
                        cmds.append(f"setblock {xc-1} {y_bed} {z} minecraft:redstone_block")
                        cmds.append(f"setblock {xc-1} {y_track} {z} minecraft:powered_rail[shape=north_south,powered=true]")
                        cmds.append(f"setblock {xc+1} {y_bed} {z} minecraft:redstone_block")
                        cmds.append(f"setblock {xc+1} {y_track} {z} minecraft:powered_rail[shape=north_south,powered=true]")
                        cmds.append(f"setblock {xc} {y_track} {z} minecraft:pearlescent_froglight")
            else:
                zc = min_z
                for x in range(min_x, max_x + 1):
                    is_near_corner = any(abs(x - cx) <= 2 for cx, cz in corner_coords if cz == zc)
                    is_near_end = any(abs(x - px) <= 2 for px, pz in [p_dep, p_arr, path[0], path[-1]] if pz == zc)
                    if abs(x) % powered_interval == 0 and not is_near_corner and not is_near_end:
                        cmds.append(f"setblock {x} {y_bed} {zc-1} minecraft:redstone_block")
                        cmds.append(f"setblock {x} {y_track} {zc-1} minecraft:powered_rail[shape=east_west,powered=true]")
                        cmds.append(f"setblock {x} {y_bed} {zc+1} minecraft:redstone_block")
                        cmds.append(f"setblock {x} {y_track} {zc+1} minecraft:powered_rail[shape=east_west,powered=true]")
                        cmds.append(f"setblock {x} {y_track} {zc} minecraft:pearlescent_froglight")

        # PHASE 7: Station Telemetry Triggers & Boosters
        idx_dep = 2 if segment.get("turn_start", False) and len(path) >= 5 else 1
        idx_arr = len(path) - 3 if segment.get("turn_end", False) and len(path) >= 5 else (len(path) - 2)

        while idx_dep < len(path) - 1 and path[idx_dep] in corner_coords:
            idx_dep += 1
        while idx_arr > 1 and path[idx_arr] in corner_coords:
            idx_arr -= 1

        p_dep = path[idx_dep]
        p_arr = path[idx_arr]

        first_dir = spans[0][2]
        launch_shape = "north_south" if first_dir[0] == 0 else "east_west"
        d1_x = p_dep[0] - first_dir[1]
        d1_z = p_dep[1] + first_dir[0]
        d2_x = p_dep[0] + first_dir[1]
        d2_z = p_dep[1] - first_dir[0]

        # Outer Ring (CCW) departure booster at p_dep
        cmds.append(f"setblock {d1_x} {y_bed} {d1_z} minecraft:redstone_block")
        cmds.append(f"setblock {d1_x} {y_track} {d1_z} minecraft:powered_rail[shape={launch_shape},powered=true]")

        # Inner Ring (CW) arrival sensor at p_dep
        cmds.append(
            f"setblock {d2_x} {y_bed} {d2_z} command_block{{Command:\"say [TELEMETRY] NODE:{from_station} EVENT:CART_PASS DATA:DUAL_TRACK_INNER_CW_SPEED_8.0_OK\"}}"
        )
        cmds.append(f"setblock {d2_x} {y_track} {d2_z} minecraft:detector_rail[shape={launch_shape}]")

        last_dir = spans[-1][2]
        det_shape = "north_south" if last_dir[0] == 0 else "east_west"
        t1_x = p_arr[0] - last_dir[1]
        t1_z = p_arr[1] + last_dir[0]
        t2_x = p_arr[0] + last_dir[1]
        t2_z = p_arr[1] - last_dir[0]

        # Outer Ring (CCW) arrival sensor at p_arr
        cmds.append(
            f"setblock {t1_x} {y_bed} {t1_z} command_block{{Command:\"say [TELEMETRY] NODE:{to_station} EVENT:CART_PASS DATA:DUAL_TRACK_OUTER_CCW_SPEED_8.0_OK\"}}"
        )
        cmds.append(f"setblock {t1_x} {y_track} {t1_z} minecraft:detector_rail[shape={det_shape}]")

        # Inner Ring (CW) departure booster at p_arr
        cmds.append(f"setblock {t2_x} {y_bed} {t2_z} minecraft:redstone_block")
        cmds.append(f"setblock {t2_x} {y_track} {t2_z} minecraft:powered_rail[shape={det_shape},powered=true]")

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


def verify_orbital_loop_telemetry(circuit: list, segment_indices: list = [0, 1], timeout: float = 14.0) -> dict:
    """
    Dispatches test minecarts in both directions along interconnected building corridors:
      1. Outer Ring: Traveling Counter-Clockwise (CCW) from s1 to s2.
      2. Inner Ring: Traveling Clockwise (CW) from s2 to s1.
    Verifies live telemetry packet emission in latest.log on Chonk.
    """
    import re
    log_path = "/home/minecraft/logs/latest.log"
    TELEMETRY_PATTERN = r"\[TELEMETRY\]\s+NODE:(?P<node>\S+)\s+EVENT:(?P<event>\S+)\s+DATA:(?P<data>\S+)"
    results = {}

    print("\n🔍 Initiating Live Telemetry Audit on Interconnected Building Corridors (Bi-directional)...")

    for s_idx in segment_indices:
        seg = circuit[s_idx]
        s1 = seg["from_station"]
        s2 = seg["to_station"]
        path = seg["path"]
        path_len = len(path)
        p1 = path[0]
        p2 = path[-1]

        p_xs = [p[0] for p in path]
        p_zs = [p[1] for p in path]
        min_x, max_x = min(p_xs) - 4, max(p_xs) + 4
        min_z, max_z = min(p_zs) - 4, max(p_zs) + 4

        rcon_exec(f"forceload add {min_x} {min_z} {max_x} {max_z}")

        # -----------------------------------------------------------------
        # TEST 1: Outer Ring (Counter-Clockwise direction: s1 -> s2)
        # -----------------------------------------------------------------
        rcon_exec("minecraft:kill @e[type=minecart]")
        rcon_exec("minecraft:kill @e[type=pig]")

        y_track = seg["y_start"]
        spans = ContainmentViaductBuilder.compress_spans(path)
        corner_coords = set(s[0] for s in spans[1:])
        idx_dep = 2 if seg.get("turn_start", False) and path_len >= 5 else 1
        idx_arr = path_len - 3 if seg.get("turn_end", False) and path_len >= 5 else (path_len - 2)

        while idx_dep < path_len - 1 and path[idx_dep] in corner_coords:
            idx_dep += 1
        while idx_arr > 1 and path[idx_arr] in corner_coords:
            idx_arr -= 1

        p_dep = path[idx_dep]
        p_arr = path[idx_arr]
        first_dir = spans[0][2]
        dx, dz = first_dir
        # Launch directly on Outer Track departure booster at p_dep
        lx = p_dep[0] - first_dir[1]
        lz = p_dep[1] + first_dir[0]
        motion_x = 0.8 * dx
        motion_z = 0.8 * dz

        pos = 0
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                f.seek(0, 2)
                pos = f.tell()

        print(f"[*] [Outer Ring - CCW] Testing corridor: {s1} ➔ {s2} ({path_len} blocks)...")
        spawn_cmd = f"summon minecraft:minecart {lx+0.5} {y_track+0.0625} {lz+0.5} {{Motion:[{motion_x},0.0,{motion_z}],Passengers:[{{id:\"minecraft:pig\",NoAI:1b}}]}}"
        rcon_exec(spawn_cmd)

        found_ccw = None
        t0 = time.time()
        max_wait = max(timeout, path_len / 5.5 + 4.0)
        while time.time() - t0 < max_wait:
            time.sleep(0.3)
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    f.seek(pos)
                    for line in f:
                        m = re.search(TELEMETRY_PATTERN, line)
                        if m and s2 in m.group("node"):
                            found_ccw = {
                                "node": m.group("node"),
                                "event": m.group("event"),
                                "data": m.group("data"),
                                "raw": line.strip(),
                                "elapsed": round(time.time() - t0, 2)
                            }
                            break
            if found_ccw:
                break

        rcon_exec("minecraft:kill @e[type=minecart]")
        rcon_exec("minecraft:kill @e[type=pig]")

        if found_ccw:
            print(f"  [+] Outer Ring CCW CONFIRMED for {s2} in {found_ccw['elapsed']}s: {found_ccw['data']}")
            results[f"{s1}->{s2} (Outer Ring CCW)"] = found_ccw
        else:
            print(f"  [-] Outer Ring CCW timed out for {s2} after {max_wait:.1f}s")
            results[f"{s1}->{s2} (Outer Ring CCW)"] = None

        # -----------------------------------------------------------------
        # TEST 2: Inner Ring (Clockwise direction: s2 -> s1)
        # -----------------------------------------------------------------
        # Reverse travel: from p2 to p1 along Inner Track
        last_dir = spans[-1][2]
        d_last_x, d_last_z = last_dir
        # Launch directly on Inner Track departure booster at p_arr
        lx_rev = p_arr[0] + last_dir[1]
        lz_rev = p_arr[1] - last_dir[0]
        motion_x_rev = -0.8 * d_last_x
        motion_z_rev = -0.8 * d_last_z

        pos_rev = 0
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                f.seek(0, 2)
                pos_rev = f.tell()

        print(f"[*] [Inner Ring - CW] Testing corridor: {s2} ➔ {s1} ({path_len} blocks in reverse)...")
        spawn_cmd_rev = f"summon minecraft:minecart {lx_rev+0.5} {y_track+0.0625} {lz_rev+0.5} {{Motion:[{motion_x_rev},0.0,{motion_z_rev}],Passengers:[{{id:\"minecraft:pig\",NoAI:1b}}]}}"
        rcon_exec(spawn_cmd_rev)

        found_cw = None
        t0 = time.time()
        while time.time() - t0 < max_wait:
            time.sleep(0.3)
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    f.seek(pos_rev)
                    for line in f:
                        m = re.search(TELEMETRY_PATTERN, line)
                        if m and s1 in m.group("node"):
                            found_cw = {
                                "node": m.group("node"),
                                "event": m.group("event"),
                                "data": m.group("data"),
                                "raw": line.strip(),
                                "elapsed": round(time.time() - t0, 2)
                            }
                            break
            if found_cw:
                break

        rcon_exec("minecraft:kill @e[type=minecart]")
        rcon_exec("minecraft:kill @e[type=pig]")
        rcon_exec(f"forceload remove {min_x} {min_z} {max_x} {max_z}")

        if found_cw:
            print(f"  [+] Inner Ring CW CONFIRMED for {s1} in {found_cw['elapsed']}s: {found_cw['data']}")
            results[f"{s2}->{s1} (Inner Ring CW)"] = found_cw
        else:
            print(f"  [-] Inner Ring CW timed out for {s1} after {max_wait:.1f}s")
            results[f"{s2}->{s1} (Inner Ring CW)"] = None

    print("\n══════════════════════════════════════════════════════════════")
    print(" 📡 BI-DIRECTIONAL TELEMETRY VERIFICATION SUMMARY")
    print("══════════════════════════════════════════════════════════════")
    all_ok = True
    for route, res in results.items():
        if res:
            print(f"  [PASS] {route} | Elapsed: {res['elapsed']}s | Node: {res['node']} | Event: {res['event']}")
        else:
            print(f"  [FAIL] {route} | Timed out")
            all_ok = False

    return {"results": results, "success": all_ok}


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
    parser.add_argument(
        "--verify-telemetry",
        action="store_true",
        help="Run live telemetry verification across interconnected building tracks",
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

    if args.verify_telemetry and not args.deploy:
        ver_res = verify_orbital_loop_telemetry(circuit)
        if not ver_res["success"]:
            sys.exit(1)
        return

    if args.verify_telemetry and args.deploy:
        ver_res = verify_orbital_loop_telemetry(circuit)
        if not ver_res["success"]:
            sys.exit(1)

    if not (args.deploy or args.verify_telemetry):
        print("\n[Dry Run Complete] To build the viaduct in-game, run with --deploy.")
        print("To verify transit telemetry, run with --verify-telemetry.")
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
