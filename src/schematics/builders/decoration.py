"""
decoration.py — Interior decoration and furniture builder.

Generates furniture groupings: beds, chests, bookshelves, lanterns,
crafting tables, furnaces, flower pots, barrels, etc.
"""

import mcschematic

# Decoration templates — relative block placements for each furniture type
DECORATION_BLOCKS = {
    "bed": [
        ((0, 0, 0), "minecraft:red_bed[facing=south,part=foot]"),
        ((0, 0, 1), "minecraft:red_bed[facing=south,part=head]"),
    ],
    "chest": [((0, 0, 0), "minecraft:chest[facing=south]")],
    "crafting_table": [((0, 0, 0), "minecraft:crafting_table")],
    "furnace": [((0, 0, 0), "minecraft:furnace[facing=south]")],
    "bookshelf": [((0, 0, 0), "minecraft:bookshelf")],
    "lantern": [((0, 0, 0), "minecraft:lantern")],
    "torch": [((0, 0, 0), "minecraft:torch")],
    "flower_pot": [((0, 0, 0), "minecraft:potted_poppy")],
    "barrel": [((0, 0, 0), "minecraft:barrel[facing=up]")],
    "painting": [
        ((0, 0, 0), "minecraft:air")
    ],  # Paintings are entities; place frame block
    "banner": [((0, 0, 0), "minecraft:white_banner")],
    "anvil": [((0, 0, 0), "minecraft:anvil[facing=south]")],
    "cauldron": [((0, 0, 0), "minecraft:cauldron")],
    "brewing_stand": [((0, 0, 0), "minecraft:brewing_stand")],
    "enchanting_table": [((0, 0, 0), "minecraft:enchanting_table")],
    "armor_stand": [((0, 0, 0), "minecraft:air")],  # Entity-based
    "jukebox": [((0, 0, 0), "minecraft:jukebox")],
    "bell": [((0, 0, 0), "minecraft:bell")],
}


def _get_positions(position_hint, count, w=7, l=7):
    """Generate block positions based on placement hints."""
    positions = []
    if position_hint == "center":
        positions.append((w // 2, 0, l // 2))
    elif position_hint == "corners":
        corners = [(1, 0, 1), (w - 2, 0, 1), (1, 0, l - 2), (w - 2, 0, l - 2)]
        positions.extend(corners[:count])
    elif position_hint == "walls":
        # Spread along north wall
        step = max(1, (w - 2) // max(1, count))
        for i in range(count):
            positions.append((1 + i * step, 0, 0))
    else:  # "auto" or unrecognized
        x, z = 1, 1
        for _ in range(count):
            positions.append((x, 0, z))
            x += 2
            if x >= w - 1:
                x = 1
                z += 2
    return positions


import re

from .t2bm_expander import T2BMExpander

T2BM_Expander = T2BMExpander

# ... (rest of imports and DECORATION_BLOCKS)


def _get_positions(position_hint, count, w=7, l=7):
    """Generate block positions based on placement hints."""
    positions = []
    if position_hint == "center":
        positions.append((w // 2, 0, l // 2))
    elif position_hint == "corners":
        corners = [(1, 0, 1), (w - 2, 0, 1), (1, 0, l - 2), (w - 2, 0, l - 2)]
        positions.extend(corners[:count])
    elif position_hint == "walls":
        # Spread along north wall
        step = max(1, (w - 2) // max(1, count))
        for i in range(count):
            positions.append((1 + i * step, 0, 0))
    else:  # "auto" or unrecognized
        x, z = 1, 1
        for _ in range(count):
            positions.append((x, 0, z))
            x += 2
            if x >= w - 1:
                x = 1
                z += 2
    return positions


def build_decoration(schem: mcschematic.MCSchematic, prompt: dict):
    decorations = prompt.get("decorations", [])
    dims = prompt.get("dimensions", {})
    mats = prompt.get("materials", {})
    w = dims.get("width", 7)
    l = dims.get("length", 7)

    # Regex to parse loop expressions like "x0to12" or "y0,2,4"
    range_parser = re.compile(r"([xyz])(-?\d+)(?:to(-?\d+))?|([xyz])(-?\d+(?:,-?\d+)*)")

    for dec in decorations:
        dec_type = dec.get("type", "lantern")

        if dec_type == "complex_structure":
            pos_offset = dec.get("position", {"x": 0, "y": 0, "z": 0})
            blocks = dec.get("blocks", {})
            for coord_str, mat_key in blocks.items():
                try:
                    # Resolve material key first
                    mat_parts = mat_key.split(".")
                    if len(mat_parts) == 2 and mat_parts[0] == "materials":
                        block_str = mats.get(mat_parts[1], "minecraft:air")
                    else:
                        block_str = mat_key  # Assume literal block string

                    # Handle loops or single points
                    if coord_str.startswith("loop_"):
                        loop_str = coord_str[5:].replace("_", "")
                        matches = range_parser.finditer(loop_str)

                        ranges = {}
                        for match in matches:
                            if match.group(1):  # x0to12 format
                                axis, start, end = (
                                    match.group(1),
                                    int(match.group(2)),
                                    match.group(3),
                                )
                                ranges[axis] = (
                                    range(start, int(end) + 1) if end else [start]
                                )
                            elif match.group(4):  # x0,2,4 format
                                axis, vals = match.group(4), match.group(5)
                                ranges[axis] = [int(v) for v in vals.split(",")]

                        x_coords = ranges.get("x", [0])
                        y_coords = ranges.get("y", [0])
                        z_coords = ranges.get("z", [0])

                        for x in x_coords:
                            for y in y_coords:
                                for z in z_coords:
                                    px = x + pos_offset.get("x", 0)
                                    py = y + pos_offset.get("y", 0)
                                    pz = z + pos_offset.get("z", 0)
                                    schem.setBlock((px, py, pz), block_str)

                    else:  # Handle single coordinate: x1_y2_z3
                        parts = coord_str.split("_")
                        coords = {}
                        for part in parts:
                            if len(part) > 1:
                                coords[part[0]] = int(part[1:])

                        px = coords.get("x", 0) + pos_offset.get("x", 0)
                        py = coords.get("y", 0) + pos_offset.get("y", 0)
                        pz = coords.get("z", 0) + pos_offset.get("z", 0)
                        schem.setBlock((px, py, pz), block_str)

                except (ValueError, IndexError) as e:
                    print(
                        f"  WARN: Could not parse complex_structure item '{coord_str}': {mat_key} -> {e}"
                    )
            continue

        # --- Legacy simple decoration logic ---
        position = dec.get("position", "auto")
        override_block = dec.get("block", None)

        template = DECORATION_BLOCKS.get(dec_type, [((0, 0, 0), "minecraft:lantern")])
        positions = _get_positions(position, 1, w, l)
        if not positions:
            continue
        px, py, pz = positions[0]
        for (dx, dy, dz), block in template:
            final_block = override_block if override_block else block
            schem.setBlock((px + dx, py + dy, pz + dz), final_block)

    return schem


# ═══════════════════════════════════════════════════════════════
#  GREEBLE PASS ENGINE (Emerald Mirror Exterior Refinement)
# ═══════════════════════════════════════════════════════════════

def apply_greeble_pass(schem: mcschematic.MCSchematic, w: int, h: int, l: int, theme: str = "industrial_singularity"):
    """
    Applies multi-layered exterior greebling to any schematic:
    1. External industrial conduit routing with junction boxes.
    2. HVAC / Tech clusters on flat roof planes.
    3. Structural rivet buttons and pressure valves on vertical pillars.
    4. Telemetry and lightning rod antennas on high elevations.
    """
    import random
    rnd = random.Random(w * 1000 + h * 100 + l)

    # Palette selection based on theme
    if theme == "void_tech":
        wall_pipe = "minecraft:tuff_wall"
        junction = "minecraft:chiseled_tuff"
        accent_btn = "minecraft:polished_blackstone_button"
        accent_trap = "minecraft:iron_trapdoor"
    else:  # industrial_singularity default
        wall_pipe = "minecraft:deepslate_tile_wall"
        junction = "minecraft:chiseled_deepslate"
        accent_btn = "minecraft:polished_deepslate_button"
        accent_trap = "minecraft:mangrove_trapdoor"

    # 1. External Conduit Routing (North & South walls)
    for z_face, facing in [(0, "north"), (l - 1, "south")]:
        offset_z = -1 if z_face == 0 else 1
        pipe_z = z_face + offset_z
        # Generate 1 to 2 vertical conduit runs per face
        num_pipes = max(1, w // 8)
        for i in range(num_pipes):
            pipe_x = 2 + i * (w // max(1, num_pipes))
            if pipe_x < w - 2:
                pipe_h = rnd.randint(h // 2, max(h // 2 + 1, h - 3))
                # Base junction
                schem.setBlock((pipe_x, 1, pipe_z), junction)
                for py in range(2, pipe_h):
                    schem.setBlock((pipe_x, py, pipe_z), wall_pipe)
                # Elbow junction into wall
                schem.setBlock((pipe_x, pipe_h, pipe_z), junction)
                # Valve
                schem.setBlock((pipe_x, pipe_h - 1, pipe_z + (-offset_z)), f"minecraft:tripwire_hook[facing={facing}]")

    # 2. Structural Rivets / Fastener Details on Corner Columns
    for cx in [0, w - 1]:
        for cz in [0, l - 1]:
            facing = "west" if cx == 0 else "east"
            btn_x = -1 if cx == 0 else 1
            for y in range(2, h - 2, 3):
                schem.setBlock((cx + btn_x, y, cz), f"{accent_btn}[facing={facing}]")

    # 3. Rooftop HVAC & Telemetry Arrays
    roof_y = h - 1
    # Check if roof is large enough for HVAC
    if w >= 8 and l >= 8:
        # Place HVAC Unit (2x2 with trapdoor vents)
        hx = w // 2 - 1
        hz = l // 2 - 1
        for dx in range(2):
            for dz in range(2):
                schem.setBlock((hx + dx, roof_y + 1, hz + dz), "minecraft:polished_deepslate")
                schem.setBlock((hx + dx, roof_y + 2, hz + dz), f"{accent_trap}[half=bottom]")
        # Exhaust fan/hopper adjacent
        schem.setBlock((hx + 2, roof_y + 1, hz), "minecraft:hopper[facing=down]")

    # 4. Telemetry / Lightning Rod Antenna with Froglight Pulse Core
    ant_x = w // 2
    ant_z = l // 2
    schem.setBlock((ant_x, roof_y + 1, ant_z), "minecraft:pearlescent_froglight")
    schem.setBlock((ant_x, roof_y + 2, ant_z), "minecraft:iron_bars")
    schem.setBlock((ant_x, roof_y + 3, ant_z), "minecraft:chain")
    schem.setBlock((ant_x, roof_y + 4, ant_z), "minecraft:lightning_rod")

    # 5. Entrance Plinth / Data Pedestal with Descriptive Sign & Froglight
    sign_text_line1 = f"[{theme[:10].upper()}]"
    sign_text_line2 = f"Vol: {w}x{h}x{l}"
    sign_text_line3 = "HW: AI-Cluster"
    sign_text_line4 = "Status: Active"

    # Pedestal at south entrance corner (0, 0, -1)
    schem.setBlock((0, 0, -1), "minecraft:polished_deepslate")
    schem.setBlock((0, 1, -1), "minecraft:pearlescent_froglight")
    sign_nbt = f"{{front_text:{{messages:['\"{sign_text_line1}\"','\"{sign_text_line2}\"','\"{sign_text_line3}\"','\"{sign_text_line4}\"']}}}}"
    schem.setBlock((0, 2, -1), f"minecraft:oak_sign[rotation=0]{sign_nbt}")

    # Corner Froglight Luminaires on Upper Cornice
    schem.setBlock((0, h - 2, 0), "minecraft:pearlescent_froglight")
    schem.setBlock((w - 1, h - 2, 0), "minecraft:pearlescent_froglight")
    schem.setBlock((0, h - 2, l - 1), "minecraft:pearlescent_froglight")
    schem.setBlock((w - 1, h - 2, l - 1), "minecraft:pearlescent_froglight")

    return schem

