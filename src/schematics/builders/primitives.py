"""
primitives.py — Core geometric primitive helpers.

These functions place blocks into an MCSchematic using basic geometry:
filled/hollow cuboids, cylinders, spheres, arches, lines, and circles.
All coords are relative to the schematic origin (0,0,0).
"""

import math

import mcschematic


def cuboid_filled(schem, x1, y1, z1, x2, y2, z2, block):
    """Fill a box from (x1,y1,z1) to (x2,y2,z2) inclusive."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                schem.setBlock((x, y, z), block)


def cuboid_hollow(schem, x1, y1, z1, x2, y2, z2, block):
    """Place only the outer shell of a box (6 faces)."""
    xlo, xhi = min(x1, x2), max(x1, x2)
    ylo, yhi = min(y1, y2), max(y1, y2)
    zlo, zhi = min(z1, z2), max(z1, z2)
    for x in range(xlo, xhi + 1):
        for y in range(ylo, yhi + 1):
            for z in range(zlo, zhi + 1):
                if x in (xlo, xhi) or y in (ylo, yhi) or z in (zlo, zhi):
                    schem.setBlock((x, y, z), block)


def cuboid_walls(schem, x1, y1, z1, x2, y2, z2, block):
    """Place only the 4 vertical walls (no floor/ceiling)."""
    xlo, xhi = min(x1, x2), max(x1, x2)
    ylo, yhi = min(y1, y2), max(y1, y2)
    zlo, zhi = min(z1, z2), max(z1, z2)
    for x in range(xlo, xhi + 1):
        for y in range(ylo, yhi + 1):
            for z in range(zlo, zhi + 1):
                if x in (xlo, xhi) or z in (zlo, zhi):
                    schem.setBlock((x, y, z), block)


def flat_plane(schem, x1, y, z1, x2, z2, block):
    """Fill a horizontal plane at height y."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            schem.setBlock((x, y, z), block)


def line_x(schem, y, z, x1, x2, block):
    """Line along X axis."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        schem.setBlock((x, y, z), block)


def line_y(schem, x, z, y1, y2, block):
    """Line along Y axis (pillar)."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        schem.setBlock((x, y, z), block)


def line_z(schem, x, y, z1, z2, block):
    """Line along Z axis."""
    for z in range(min(z1, z2), max(z1, z2) + 1):
        schem.setBlock((x, y, z), block)


def circle_xz(schem, cx, y, cz, radius, block, filled=False):
    """Draw a circle in the XZ plane at height y."""
    r2 = radius * radius
    ri2 = (radius - 1) * (radius - 1) if not filled else -1
    for x in range(-radius, radius + 1):
        for z in range(-radius, radius + 1):
            dist = x * x + z * z
            if dist <= r2 and (filled or dist >= ri2):
                schem.setBlock((cx + x, y, cz + z), block)


def cylinder(schem, cx, y1, cz, radius, height, block, filled=False):
    """Vertical cylinder centered at (cx, cz) from y1 to y1+height-1."""
    for y in range(y1, y1 + height):
        circle_xz(schem, cx, y, cz, radius, block, filled=filled)


def sphere(schem, cx, cy, cz, radius, block, filled=False):
    """Sphere centered at (cx, cy, cz)."""
    r2 = radius * radius
    ri2 = (radius - 1) * (radius - 1) if not filled else -1
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                dist = x * x + y * y + z * z
                if dist <= r2 and (filled or dist >= ri2):
                    schem.setBlock((cx + x, cy + y, cz + z), block)


def dome(schem, cx, cy, cz, radius, block, filled=False):
    """Upper hemisphere centered at (cx, cy, cz)."""
    r2 = radius * radius
    ri2 = (radius - 1) * (radius - 1) if not filled else -1
    for x in range(-radius, radius + 1):
        for y in range(0, radius + 1):
            for z in range(-radius, radius + 1):
                dist = x * x + y * y + z * z
                if dist <= r2 and (filled or dist >= ri2):
                    schem.setBlock((cx + x, cy + y, cz + z), block)


def arch_xz(schem, x1, y, z, x2, height, block):
    """Semi-circular arch spanning from x1 to x2 at z, peaking at y + height."""
    span = abs(x2 - x1)
    radius = span / 2.0
    cx = (x1 + x2) / 2.0
    base_y = y
    for xi in range(min(x1, x2), max(x1, x2) + 1):
        dx = xi - cx
        if abs(dx) <= radius:
            arch_h = int(
                math.sqrt(max(0, radius * radius - dx * dx)) * (height / radius)
            )
            for yi in range(base_y, base_y + arch_h + 1):
                schem.setBlock((xi, yi, z), block)


def cone(schem, cx, y_base, cz, base_radius, height, block):
    """Cone shape tapering from base_radius at y_base to point at y_base + height."""
    for y_off in range(height):
        r = max(0, int(base_radius * (1.0 - y_off / height)))
        if r == 0:
            schem.setBlock((cx, y_base + y_off, cz), block)
        else:
            circle_xz(schem, cx, y_base + y_off, cz, r, block, filled=True)


def pyramid(schem, x1, y_base, z1, x2, z2, height, block):
    """Square pyramid rising from the base rectangle."""
    for y_off in range(height):
        shrink = y_off
        nx1 = min(x1, x2) + shrink
        nz1 = min(z1, z2) + shrink
        nx2 = max(x1, x2) - shrink
        nz2 = max(z1, z2) - shrink
        if nx1 > nx2 or nz1 > nz2:
            break
        flat_plane(schem, nx1, y_base + y_off, nz1, nx2, nz2, block)


# ═══════════════════════════════════════════════════════════════
#  GREEBLING & 5-LAYER RELIEF PRIMITIVES (Emerald Mirror Spec)
# ═══════════════════════════════════════════════════════════════

def fluted_pillar_3x3(schem, cx, cz, y_start, y_end, core_block, stair_trim):
    """
    Constructs a 3x3 fluted structural column with indented stair relief:
    Central core block with recessed corner/side stairs.
    """
    for y in range(y_start, y_end + 1):
        # Central core
        schem.setBlock((cx, y, cz), f"{core_block}[axis=y]" if "pillar" in core_block or "log" in core_block else core_block)
        # Cardinal fluted trim
        schem.setBlock((cx + 1, y, cz), f"{stair_trim}[facing=west,half=bottom]")
        schem.setBlock((cx - 1, y, cz), f"{stair_trim}[facing=east,half=bottom]")
        schem.setBlock((cx, y, cz + 1), f"{stair_trim}[facing=north,half=bottom]")
        schem.setBlock((cx, y, cz - 1), f"{stair_trim}[facing=south,half=bottom]")


def stepped_buttress(schem, x, z, y_base, height, facing, block, stair_block, wall_block):
    """
    Creates a tapering vertical exterior buttress for structural realism.
    facing: 'north', 'south', 'east', 'west' (direction the buttress juts outward).
    """
    dx, dz = 0, 0
    opp_facing = "south"
    if facing == "north":
        dz = -1
        opp_facing = "south"
    elif facing == "south":
        dz = 1
        opp_facing = "north"
    elif facing == "east":
        dx = 1
        opp_facing = "west"
    elif facing == "west":
        dx = -1
        opp_facing = "east"

    # Base projection
    for dy in range(height):
        # Full block column against wall
        schem.setBlock((x, y_base + dy, z), block)
        if dy < height // 3:
            # Bottom tier: full block + stair projection
            schem.setBlock((x + dx, y_base + dy, z + dz), block)
            schem.setBlock((x + dx * 2, y_base + dy, z + dz * 2), f"{stair_block}[facing={facing},half=bottom]")
        elif dy < (2 * height) // 3:
            # Mid tier: single projection stair/wall
            schem.setBlock((x + dx, y_base + dy, z + dz), f"{stair_block}[facing={facing},half=bottom]")
        else:
            # Top tier: wall conduit
            schem.setBlock((x + dx, y_base + dy, z + dz), wall_block)


def greeble_conduit_run(schem, start_coord, end_coord, wall_block="minecraft:deepslate_tile_wall", junction_block="minecraft:chiseled_deepslate"):
    """
    Renders an external pipe / industrial conduit run with junction boxes.
    Coords are (x, y, z) tuples.
    """
    x1, y1, z1 = start_coord
    x2, y2, z2 = end_coord

    # Manhattan routing: Y then X then Z
    curr_x, curr_y, curr_z = x1, y1, z1
    schem.setBlock((curr_x, curr_y, curr_z), junction_block)

    # Vertical leg
    step_y = 1 if y2 >= y1 else -1
    for y in range(y1 + step_y, y2 + step_y, step_y):
        schem.setBlock((curr_x, y, curr_z), wall_block)
    curr_y = y2
    if curr_x != x2 or curr_z != z2:
        schem.setBlock((curr_x, curr_y, curr_z), junction_block)

    # X leg
    step_x = 1 if x2 >= x1 else -1
    for x in range(x1 + step_x, x2 + step_x, step_x):
        schem.setBlock((x, curr_y, curr_z), wall_block)
    curr_x = x2
    if curr_z != z2:
        schem.setBlock((curr_x, curr_y, curr_z), junction_block)

    # Z leg
    step_z = 1 if z2 >= z1 else -1
    for z in range(z1 + step_z, z2 + step_z, step_z):
        schem.setBlock((curr_x, curr_y, z), wall_block)
    schem.setBlock((x2, y2, z2), junction_block)


def coffered_ceiling_bay(schem, x1, y, z1, x2, z2, beam_block, panel_slab, light_block="minecraft:pearlescent_froglight", grid_interval=4):
    """
    Builds an industrial coffered ceiling with recessed light boxes.
    """
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            is_beam = (x % grid_interval == 0) or (z % grid_interval == 0)
            if is_beam:
                # Structural girder beam
                schem.setBlock((x, y, z), beam_block)
                # Recessed light at grid intersections
                if (x % grid_interval == 0) and (z % grid_interval == 0):
                    schem.setBlock((x, y + 1, z), light_block)
            else:
                # Recessed coffer panel
                schem.setBlock((x, y, z), f"{panel_slab}[type=top]")

