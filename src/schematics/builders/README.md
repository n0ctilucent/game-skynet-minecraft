# Builders — Modular Structure Generation

Procedural building modules for the Emerald Mirror pipeline. Each builder accepts an `MCSchematic` canvas and a JSON `prompt` dict (dimensions, materials, features), returning a fully constructed schematic ready for serialization.

---

## Registry

```python
from builders import BUILDERS

BUILDERS = {
    "house":      build_house       — House/cabin structure
    "wall":       build_wall         — Perimeter wall with optional crenellations
    "tower":      build_tower        — Cylindrical tower/spire
    "bridge":     build_bridge       — Flat or arched bridge/walkway
    "terrain":    build_terrain      — Natural terrain/garden generation
    "decoration": build_decoration   — Interior decoration templates
    "castle":     build_castle       — Castle with walls, towers, courtyard, gate
    "bank":       build_bank         — Grand bank with full interior (80×60×80)
    "cyberdyne":  build_cyberdyne   — Cyberdyne R&D Tower (Void-Tech style)
    "station":    build_station      — High-fidelity industrial station (v5 standards)
    "t2bm":       build_t2bm         — T2BM Interlayer Protocol intent→voxel mapper
}
```

---

## Builders

### `house.py` — House / Cabin Builder

Generates rectangular buildings with walls, floor, roof, windows, door, chimney, and lighting. Default 9×6×11 footprint configurable via prompt.

- **Materials**: primary/secondary/floor/roof/glass/door/light/accent/tertiary/slab
- **Features**: crenellations, overhang, foundation
- **Primitives used**: `cuboid_filled`, `cuboid_walls`, `flat_plane`, `line_y`

### `wall.py` — Wall / Fence Builder

Straight walls with optional crenellations (merlons every other block). Default 20 wide × 5 tall × 1 thick.

- **Materials**: primary wall body, slab top course, secondary stairs
- **Features**: `crenellations: true/false`

### `tower.py` — Tower / Spire Builder

Cylindrical towers with hollow interior, windows, peaked/dome roofs, and optional crenellations. Default 9×24×9 footprint (increased for v5 fluted standards).

- **v5 Industrial Palette** (defaults):
  - `primary`: polished deepslate bricks
  - `secondary` / `girder`: dark prismarine
  - `pillar`: purpur pillar (3x3 fluted core)
  - `light`: pearlescent froglight
  - `accent`: warped fence

### `bridge.py` — Bridge / Walkway Builder

Flat or arched bridges with railings. Default width 7, arch height 8, span 25 blocks. Follows v5 Industrial Standards.

- **v5 Palette** (defaults): polished deepslate bricks, dark prismarine girders, purpur pillars, warped fences, pearlescent froglight, polished andesite floor
- **Primitives used**: `cuboid_filled`, `flat_plane`, `line_z`

### `castle.py` — Castle / Fortification Builder

Complete castle with outer walls, corner towers, courtyard, and gate. Combines wall and tower primitives for a fortified enclosure. Default 25×12×25 footprint.

- **Materials**: primary (stone bricks), secondary (mossy stone bricks)
- **Primitives used**: `circle_xz`, `cone`, `cuboid_filled`, `cuboid_walls`, `cylinder`, `flat_plane`, `line_y`

### `bank.py` — Grand Bank Builder (80×60×80)

Massive, highly detailed bank with:
- Double-height lobby with quartz pillars and chandeliers
- Teller counter area with individual stations
- Iron-walled vault with treasure display
- Multiple furnished offices, conference room, break room
- Upper floors with manager suite
- Exterior columns, cornice detailing, grand staircase entrance
- Decorative roof with parapet

### `cyberdyne.py` — Cyberdyne R&D Tower Builder (13×40×13)

Tall redstone-infused tower themed as a research facility:
- **Ground floor**: Railway Integration Lab (track beds, redstone indicators)
- **Middle floors**: Redstone Workshop (circuit design areas)
- **Top**: Mycelial Data Core
- **Roof**: Mushroom-themed dome

Uses `blocks` module block constants and `interiors` room templates.

### `station2.py` — High-Fidelity Industrial Station Builder

v5-standard industrial station featuring:
- Fluted 3x3 pillars for structural depth
- Hanging grid-iron girders (dark prismarine + warped fences)
- Vaulted ceiling logic
- Platform foundation with polished andesite

### `t2bm_expander.py` — T2BM Interlayer Protocol Builder

Translates high-level architectural intents into voxel-density structures. Supports:

| Intent | Output |
|--------|--------|
| `neural_anchor` | Neural anchor structure |
| `neural_vault` | Neural vault (crying obsidian core) |
| `neural_tower` | Neural tower with Void-Tech aesthetic |

**Palette**: deepslate tiles → polished tuff → crying obsidian → pearlescent froglight → purpur pillar → tinted glass.

### `terrain.py` — Terrain / Garden Builder

Natural-looking terrain blobs and flat gardens using simplex-style noise approximation (layered sine/cosine harmonics). Seeds with configurable random offsets for organic shapes.

### `interiors.py` — Interior Furnishing System

Reusable furniture placement and room furnishing routines:
- **Individual pieces**: desk, chair, table, chandelier, bed, chest, crafting table, furnace, bookshelf, lantern, torch, flower pot, barrel, painting
- **Room suites**: office, vault, conference room, break room, manager suite
- Uses `blocks` module for correct orientation handling

### `decoration.py` — Decoration Templates

Furniture groupings and decorative block templates: bed, chest, crafting table, furnace, bookshelf, lantern, torch, flower pot, barrel, painting. Relative block placements for easy insertion into any structure.

---

## Core Primitives (`primitives.py`)

Low-level geometric helpers all builders use. All coordinates relative to schematic origin (0, 0, 0):

| Function | Shape |
|----------|-------|
| `cuboid_filled()` | Solid box |
| `cuboid_hollow()` | Box shell (6 faces) |
| `cuboid_walls()` | Four wall faces only |
| `flat_plane()` | 2D plane (XY, XZ, or YZ) |
| `line_x()` / `line_y()` / `line_z()` | Single-axis block line |
| `circle_xz()` | Circle in XZ plane |
| `cylinder()` | Vertical cylinder |
| `cone()` | Tapered cone |
| `arch()` | Arched span (half-circle + pillars) |
| `dome()` | Hemispherical roof |

---

## Block Constants (`blocks.py`)

Predefined block objects with orientation support:

```python
# Access via B.<TYPE>(<variant>)
B.polished_deepslate()
B.purpur_pillar()
B.dark_prismarine()
B.crying_obsidian()
B.pearlescent_froglight()
B.tinted_glass()
B.fence(mat)   — with facing direction
B.slab(mat, "bottom"/"top")
B.stairs(mat)  — with facing/half
```

---

## Usage

```python
import mcschematic
from builders import BUILDERS

schem = mcschematic.MCSchematic()
prompt = {
    "dimensions": {"width": 20, "height": 15, "length": 20},
    "materials": {
        "primary": "minecraft:polished_tuff",
        "secondary": "minecraft:crying_obsidian",
    },
    "features": {"crenellations": True}
}

builder = BUILDERS["tower"]
builder(schem, prompt)

schem.save("output/my_tower.schem")
```

---

## v5 Industrial Standards (Applied to Builders)

- **Voxel Density**: Min 20×15×25 bounding box
- **Rule of Three**: Base → Pillar → Girder layers mandatory
- **Fluted Pillars**: 3x3 purpur pillar footprint with stair shadowing
- **Industrial Lighting**: pearlescent froglight at girder intersections
- **Grid-Iron Girders**: dark prismarine + warped fence intersections

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
