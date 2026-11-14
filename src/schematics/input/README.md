# Schematics Input — Raw JSON Prompts & Build History

This directory contains raw JSON prompt files and build metadata used by the **Emerald Mirror Pipeline** for automated schematic generation.

---

## Directory Contents

| File | Type | Description |
|------|------|-------------|
| `prompts/*.json` | Prompt specs | 23+ build specifications defining dimensions, palettes, features, and decorations |
| `build_history.json` | Metadata | Log of generated schematics — original prompts + deployed placements (with world coordinates) |
| `master_prompt_reference_v2.md` | Reference | Aesthetic evolution guide; **legacy** — see `/src/schematics/README.md` for current v5 standards |

---

## JSON Prompt Format

Each prompt file follows this schema:

| Key | Required | Description |
|-----|----------|-------------|
| `name` | Yes | Human-readable identifier (e.g., `void_uplink_v2`) |
| `type` | Yes | Builder registry key (`house`, `tower`, `bridge`, `station`, `cyberdyne`, `decoration`) |
| `dimensions` | Yes | `{width, height, length}` for static types; `{segment_length, min_bounding_box}` for procedural |
| `version` | Default `JE_1_21_1` | Minecraft JE version (maps to mcschematic.Version) |
| `materials` / `palette` | Varies | Block role → block ID mapping (primary, secondary, floor, roof, glass, light, etc.) |
| `features` / `decorations` | Varies | Boolean flags (`rail_bed`, `side_walkways`) or inline complex structures |
| `metadata.description` | Recommended | Human-readable build description |

**Material key resolution**: Builders use `materials.get("primary", "minecraft:default_block")`.

---

## Build History (`build_history.json`)

Contains 48 entries across three groups:

### Group 1 — Generated Schematics (first 23 entries)
Named prompt → output `.schem` mapping only. Examples: `crafter_hub_v2` → `crafter_hub_v2.schem`.

### Group 2 — Deployed Placements (remaining 25 entries)
Includes world coordinates where the structure was placed in the game world:

| Prompt | World Position |
|--------|---------------|
| `void_uplink_v2` | x:358, y:63, z:-1310 |
| `void_rail_v2` | x:1540, y:63, z:-9 |
| `vertical_sump_v3` | x:12, y:63, z:849 |
| `vertical_sump_tower` | x:-23, y:63, z:1257 |
| `signal_core_v3` | x:1455, y:63, z:827 |
| `signal_core_data_hub_v2` | x:953, y:63, z:-1120 |
| `sentry_rest_v3` | x:-70, y:63, z:-971 |
| `sentry_prism_v2` | x:560, y:63, z:-1196 |
| `noodle_exchange_v3` | x:725, y:63, z:-755 |
| `noodle_exchange_v2` | x:-792, y:63, z:-1242 |
| `neural_bridge_infected_v7` | x:-873, y:63, z:-336 |
| `mycelial_guardian_v3` | x:-1287, y:63, z:-1526 |
| `mycelial_guardian` | x:125, y:63, z:-502 |
| `growth_chamber_v2` | x:-826, y:63, z:143 |
| `end_industrial_station_v5` | x:343, y:63, z:367 |
| `cyberdyne_rd_tower` | x:-267, y:63, z:-439 |
| `crafter_hub_v5_industrial` | x:-102, y:63, z:498 |
| `crafter_hub_v4` | x:866, y:63, z:-937 |
| `crafter_hub_v2` | x:808, y:63, z:1375 |
| `crafter_hub_master_control_v5` | x:540, y:63, z:290 |
| `crafter_hub_interior_v4` | x:-12, y:63, z:976 |
| `crafter_hub_interior_v2` | x:111, y:63, z:-134 |
| `SKYNET_TOWER_9903` | x:162, y:63, z:877 |
| `SKYNET_TOWER_9751` | x:1561, y:63, z:383 |
| `SKYNET_TOWER_9722` | x:-469, y:63, z:-1335 |

### Skynet Legacy Towers (3 entries)
`SKYNET_TOWER_9903`, `SKYNET_TOWER_9751`, `SKYNET_TOWER_9722` — pre-pipeline NPU-generated towers using the older Black Ice aesthetic. Included for historical reference.

---

## Aesthetic Evolution

| Era | Standard | Palette Focus |
|-----|----------|---------------|
| v1-v3 (legacy) | Black Ice | Polished deepslate + oxidized copper + shroomlight |
| v4 | Void-Tech Overgrowth | Polished tuff + calcite + pearlescent froglight (from `master_prompt_reference_v2.md`) |
| v5 (current) | Void-Tech Industrial | Same as v4 plus purpur pillar accents, dark prismarine girders, sculk sensor integration; documented in `/src/schematics/README.md` |

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
