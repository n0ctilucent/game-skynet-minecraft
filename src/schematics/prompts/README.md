# Prompts — Build Specifications (JSON)

JSON prompt files for the schematic generation pipeline. Each file defines a structure's dimensions, materials palette, features, and optional inline block-level decorations.

---

## Format Reference

All prompts accept these standard keys:

| Key | Required | Description |
|-----|----------|-------------|
| `name` | Yes | Human-readable identifier |
| `type` | Yes | Maps to builder registry key (`house`, `tower`, `bridge`, `station`, etc.) |
| `dimensions` | Yes | `{width, height, length}` or `{segment_length, min_bounding_box}` for procedural types |
| `version` | Default `JE_1_21_1` | Minecraft JE version (maps to mcschematic.Version) |
| `materials` / `palette` | Varies | Block definitions keyed by role name; builders resolve these by string lookup |
| `features` / `decorations` | Varies | Boolean flags or inline complex structure block maps |
| `metadata.description` | Recommended | Human-readable build description |

**Material key resolution**: Builders use `materials.get("primary", "minecraft:default_block")`. Common role keys include `primary`, `secondary`, `tertiary`, `floor`, `roof`, `glass`, `light`, `pillar`, `girder`, `accent`, `trim`, `conduit`, `greeble`.

---

## Catalog by Category

### Industrial Hubs — Crafter Hub Series

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `crafter_hub_v2.json` | 7×7×7 | house | house | Automated manufacturing unit with Crafter block as central logic gate; polished tuff + calcite palette |
| `crafter_hub_v4.json` | 7×7×7 | house | house | V4 interior — "Computational Ender-Core" aesthetic; identical dims to v2, updated materials/interior decorations |
| `crafter_hub_v5_industrial.json` | 21×16×29 | station | station (station2) | High-fidelity industrial hub with 3×3 fluted pillars, suspended grid girders, vaulted roof; purpur pillar + dark prismarine palette |
| `crafter_tech_magic_v5.json` | 25×18×40 | station | station (station2) | Large-scale industrial terminal. Expanded palette with pearlescent froglight light boxes and iron bar greebling; wall recess depth 2 |
| `crafter_hub_master_control_v5.json` | 13×9×13 | decoration | decoration | Master Control Room — glass floor over sub-level, expanded logic core (5×5), observation deck, tech-noir furnishings; lectern terminals + chain railings |

### Towers

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `cyberdyne_rd_tower.json` | 13×40×13 | cyberdyne | cyberdyne | Cyberdyne Systems R&D Tower — polished deepslate body, redstone veins/shroomlight lighting, mushroom-block dome roof; Railway Integration Lab → Redstone Workshop → Mycelial Data Core vertical zoning |
| `mycelial_guardian.json` | 15×25×15 | tower | tower | Massive mushroom-themed statue — mushroom stem + oxidized copper body, red mush room-block dome, cyan stained glass, shroomlight core, water moat |
| `mycelial_guardian_v3.json` | 11×25×11 | tower | tower | "Landmark Monument" variant — symmetrical statue using biological materials, sea lantern secondary, lightning rod antenna, dome roof |
| `sentry_prism_v2.json` | 5×15×5 | tower | tower | Perimeter defense post — polished tuff body with tinted glass stealth panels, pearlescent froglight signal indicators, top observation deck |
| `signal_core_data_hub_v2.json` | 9×16×9 | house (type) → tower (category) | tower/bridge hybrid | Signal Core Data Hub V2 — polished deepslate with oxidized copper accents, moss carpet floor, bioluminescent lobby, shroomlight + copper bulb indicators |
| `signal_core_v3.json` | 9×10×9 | house → tower | tower | "Comms Array" — oxidized copper body with lit copper bulbs as pulsing redstone core, cyan stained glass coolant windows, flat roof |
| `vertical_sump_tower.json` | 11×35×11 | tower | tower | Vertical Sump Logistics Tower — polished deepslate + oxidized copper stairs/shroomlight lighting, dome roof, crenellations; connects Rail Yard (Y:63) ↔ Deep Station (Y:31) |
| `vertical_sump_v3.json` | 9×32×9 | tower | tower | "Industrial Bridge" variant — utilitarian shaft using dark prismarine + polished deepslate, top deck, cyan stained glass windows |
| `void_uplink_v2.json` | 7×45×7 | tower | tower | High-altitude signal transmitter (tallest at Y:45) — polished tuff + calcite body, lightning rod accents, tinted glass conduit shafts, pearlescent froglight, end rod antennae; hollow interior with antenna feature |

### Bridges / Rail

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `noodle_exchange_v2.json` | 7×7×7 | house → bridge | bridge/house hybrid | "Noodle Economy Exchange" — polished deepslate + oxidized copper, gray concrete floor, flat roof, iron door (north), track beds + bioluminescent shroomlight accents |
| `noodle_exchange_v3.json` | 7×7×7 | house → bridge | bridge/house hybrid | "Trade Standard" — simplified v3 with integrated Crafter core; polished deepslate + oxidized copper palette |
| `void_rail_v2.json` | 11×9×20 | bridge | bridge | Futuristic Deep-Rail terminus — polished tuff frame with purpur pillar supports, gray concrete floor, calcite vaulted ceiling, pearlescent froglight lighting; rail bed + side walkways feature flags |

### Structures / Buildings

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `growth_chamber_v2.json` | 9×8×9 | house | house | Sterile hydroponics lab — calcite + polished tuff bricks, smooth quartz floor, cherry leaf accent (mycelial mutation study), pearlescent froglight, tinted glass windows, flat roof |
| `industrial_station.json` / `end_industrial_station_v5.json` | 25×18×35 | station | station (station2) | High-detail automated End-Tech hub — purpur pillar pillars, dark prismarine girders, polished andesite floor, sea lantern lighting; vaulted industrial roof, high greebling, exposed beams, 2 interior platforms, foundation depth 3 |
| `sentry_rest_v3.json` | 11×8×13 | house | house | "Foundational" retreat — polished deepslate plinth with dark oak log framing, steep peaked roof (dark oak stairs), cyan stained glass windows, oxidized copper bulb lighting |

### Neural / Specialized

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `neural_bridge_infected_v7.json` | seg 20, min 20×15×25 | procedural | neural_bridge_v8_pathfinder / custom | v5-tier Void-Tech Overgrowth bridge — TPU-driven with INTENSION_HIGH trigger. 3-layer directive: Base (polished tuff bricks/chiseled tuff), Structural (crying obsidian stress points + purpur pillars), Sensory (sculk sensors in tinted glass housings). Palette includes sculk infection core, crying obsidian anchors, pearlescent froglights; mycelial mutation carpet/cherry leaves. Hydro-pod crafter center, 4 lightning rod antennae arrays |

### Test / Validation

| Prompt | Dimensions | Type | Builder Match | Notes |
|--------|-----------|------|---------------|-------|
| `test_house.json` | 10×10×10 | house | house | Minimal test prompt — void_tech feature flag; used for pipeline validation and version compatibility checks |

---

## Paired Generated Schematics

Each prompt typically produces a `.schem` + `.json` output pair in `schem_files/`:

| Prompt | Output Files |
|--------|-------------|
| `crafter_hub_v2` | `crafter_hub_v2.schem` + `crafter_hub_v2.json` |
| `crafter_hub_interior_v2` | `crafter_hub_interior_v2.schem` + `.json` |
| `crafter_hub_v4` | `crafter_hub_v4.schem` + `.json` |
| `crafter_hub_interior_v4` | `crafter_hub_interior_v4.schem` + `.json` |
| `crafter_hub_master_control_v5` | `crafter_hub_master_control_v5.schem` + `.json` |
| `crafter_hub_v5_industrial` | `crafter_hub_v5_industrial.schem` + `.json` |
| `cyberdyne_rd_tower` | `cyberdyne_rd_tower.schem` + `.json` |
| `growth_chamber_v2` | `growth_chamber_v2.schem` + `.json` |
| `mycelial_guardian` | `mycelial_guardian.schem` + `.json` |
| `mycelial_guardian_v3` | `mycelial_guardian_v3.schem` + `.json` |
| `neural_bridge_infected_v7` | `neural_bridge_infected_v7.schem` + `.json` |
| `noodle_exchange_v2` | `noodle_exchange_v2.schem` + `.json` |
| `noodle_exchange_v3` | `noodle_exchange_v3.schem` + `.json` |
| `sentry_prism_v2` | `sentry_prism_v2.schem` + `.json` |
| `sentry_rest_v3` | `sentry_rest_v3.schem` + `.json` |
| `signal_core_v3` | `signal_core_v3.schem` + `.json` |
| `signal_core_data_hub_v2` | `signal_core_data_hub_v2.schem` + `.json` |
| `vertical_sump_tower` | `vertical_sump_tower.schem` + `.json` |
| `vertical_sump_v3` | `vertical_sump_v3.schem` + `.json` |
| `void_rail_v2` | `void_rail_v2.schem` + `.json` |
| `void_uplink_v2` | `void_uplink_v2.schem` + `.json` |

---

## Generation

```sh
python generate_schematic.py prompts/my_build.json
# Output: schem_files/my_build.schem + my_build.json
```

Output written flat to `schem_files/`. Each `.json` in output stores the full prompt metadata plus generated spatial_data (origin, dimensions).

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
