# Schematics & Emerald Mirror Pipeline

Distributed AI pipeline for procedural generation, greebling injection, and RCON deployment of Minecraft structures into the Bitsmasher server (`10.10.8.60`). Powered by the dual-inference cluster (Hailo-8L NPU + Edge TPU).

---

## Architecture

```
Stargate MCP (Orchestrator)        Skynet Core (Hub-00)
    10.10.16.66:8765                  10.10.16.10
         │                               │
         │  T2BM Intent Dispatch          │  Hailo-8L Spatial Inference
         ▼                               ▼
   Edge-T Node (Hub-06)              NPUSpatialEngine
    10.10.16.4:8767                  Adaptive_Mutation_v7
     │                                   │
     │  Aesthetic Validation            Vertex AI Delta Generation
     │                              ┌────┴────┐
     ▼                              ▼          ▼
  Vision_Overseer            Schema Gen   RCON Push
  (Edge TPU)                    │          to chonk
                                ▼
                    schem_files/ (.schem + .json)
                    prompts/ (build specs)
```

| Node | IP:Port | Role |
|------|---------|------|
| Stargate MCP | `10.10.16.66:8765` | Master orchestrator, LLM intent dispatch |
| Skynet Core | `10.10.16.10:8766` | Hailo-8L NPU spatial inference, Vertex AI coordination |
| Edge-T Node | `10.10.16.4:8767` | Edge TPU aesthetic validation, mutation scans |
| chonk (target) | `10.10.8.60:25575` | Minecraft server — RCON injection target |

---

## Directory Structure

### Top-Level Scripts (`src/schematics/`)

| Script | Purpose |
|--------|---------|
| `generate_schematic.py` | Core generation engine — loads JSON prompt from `prompts/`, invokes builder, writes `.schem` + `.json` to `schem_files/` |
| `batch_generate.py` | Iterates multiple prompts for bulk generation runs |
| `batch_deploy.py` | Deploys generated schematics via RCON with throttle (0.05s/block), AABB overlap detection, and metadata tracking |
| `neural_bridge_v7.py` | Neural bridge structure generator with block rotation support |
| `neural_bridge_v8_pathfinder.py` | Intelligent rail-link calculator — uses A* pathfinding + BlueMap marker push |
| `neural_rail.py` | Neural rail network generation logic |
| `neural_rail_v7_nexus.py` | V7 nexus variant — high-density rail interchange generator |
| `kinetic_rail_v5.py` | Kinetic rail system with Hailo-8L optimized throughput (0.005s/block) |
| `neural_pathfinder.py` | A* pathfinding engine optimized for Hailo-8L NPU — 5-block grid resolution over AI testing field bounds (`min_x=-1539, max_x=-945, min_z=-913, max_z=-489`) |
| `palette_gen.py` | Void-Tech block palette with weighted random selection (standard + aggressive mutation modes) |
| `validate_no_overlaps.py` | Pre-deployment 3D AABB overlap detection across all registered builds in `schem_files/` |
| `validate_schems.py` | Schema integrity validation using mcschematic library |
| `validate_existing.py` | NBT schematic file health check via nbtlib |
| `place_ai_field_signs.py` | Auto-places AI warning/signage blocks in the AI Testing Field area (hourly cycle) |
| `hailo_deploy.py` | Hailo-accelerated deployment pipeline entry point |
| `generate_noodle_exchange.py` | Noodle Exchange structure generator |
| `generate_rail_sentinel.py` | Rail sentinel tower generator |

### Injectors & Process Scripts

**Injectors** (sends schematics to server via RCON):

| Script | Structure Target |
|--------|-----------------|
| `inject_alien_craft.py` | Alien Craft artifact structure |
| `inject_chronosplicer.py` | Chronosplicer temporal device |
| `inject_cooling_array.py` | Cooling array / thermal management unit |
| `inject_monolith.py` | Monolith I (legacy) |
| `inject_monolith_v2.py` | Monolith II (revised spec) |
| `inject_pulse_relay.py` | Pulse relay station |
| `inject_stabilizer.py` | Stabilizer tower |

**Process scripts** (parses/transforms schematic definitions):

| Script | Companion Injector |
|--------|-------------------|
| `process_alien_craft.py` | → `inject_alien_craft.py` |
| `process_chronosplicer.py` | → `inject_chronosplicer.py` |
| `process_cooling_array.py` | → `inject_cooling_array.py` |
| `process_monolith.py` | → `inject_monolith.py` |
| `process_monolith_v2.py` | → `inject_monolith_v2.py` |
| `process_pulse_relay.py` | → `inject_pulse_relay.py` |
| `process_stabilizer.py` | → `inject_stabilizer.py` |

### `builders/` — Modular Structure Builders

```
BUILDERS = {
    "house":     build_house       — House/cabin structure
    "wall":      build_wall         — Perimeter defense walls
    "tower":     build_tower        — Vertical tower structures
    "bridge":    build_bridge       — Span/bridge structures
    "terrain":   build_terrain      — Terrain shaping/greebling
    "decoration":build_decoration  — Decorative elements
    "castle":    build_castle       — Castle/fortress structures
    "bank":      build_bank         — Grand bank with full interior
    "cyberdyne": build_cyberdyne   — Cyberdyne tower (Void-Tech style)
    "station":   build_station      — High-fidelity industrial station (fluted pillars, grid-iron girders, integrated lighting)
    "t2bm":      build_t2bm         — T2BM Interlayer Protocol builder
}
```

Additional builders not in registry:

| Module | Notes |
|--------|-------|
| `station2.py` | High-fidelity industrial station with fluted pillars, grid-iron girders, integrated lighting |
| `t2bm_expander.py` | T2BM Interlayer bridge — maps abstract intents to voxel layouts |
| `terrain.py` | Terrain generation and greebling |
| `interiors.py` | Interior furnishing system and room templates |
| `blocks.py` | Block rotation, facing, axis, half, hinge property engine |

### `prompts/` — JSON Build Specifications

25 prompt files defining structures for generation. Naming reflects version history:

- **crafter_hub** v2/v4/v5 variants — Industrial crafter hub configurations
- **cyberdyne_rd_tower.json** — Cyberdyne research tower spec
- **growth_chamber_v2.json** — Agricultural growth chamber
- **industrial_station.json** — Industrial station template
- **mycelial_guardian** v2/v3 — Biotech mycelial guardian structure
- **neural_bridge_infected_v7.json** — Infected neural bridge variant
- **noodle_exchange** v2/v3 — Rail noodle exchange terminus
- **sentry_prism**, **sentry_rest** — Sentry monitoring structures
- **signal_core** variants — Signal core/data hub configurations
- **vertical_sump_tower**, **vertical_sump_v3** — Vertical rail transition tower
- **void_rail_v2.json**, **void_uplink_v2.json** — Void-tech rail infrastructure
- **test_house.json** — Test/validation house

### `schem_files/` — Generated Schematics

Flat directory containing `.schem` + `.json` pairs. Each build has a paired metadata file with `build_id`, `spatial_data` (origin, dimensions), and `schematic_type`.

| Category | Examples |
|----------|----------|
| **SKYNET_TOWER** (92 entries) | SKYNET_TOWER_1011 through SKYNET_TOWER_9903 — numbered tower builds |
| **crafter_hub** v2-v5 | Industrial crafter hub interior and master control schematics |
| **neural_bridge** | neural_bridge_infected_v7.json + .schem |
| **noodle_exchange** | v2/v3 rail exchange terminus |
| **signal_core** | Signal core + data hub variants |
| **vertical_sump** | Vertical sump tower v3 |
| **void_rail/uplink** | Void-tech rail and uplink infrastructure |
| **mycelial_guardian** | Biotech guardian structure |
| **cyberdyne_rd_tower** | Cyberdyne research tower |
| **growth_chamber_v2** | Agricultural growth chamber |
| **sentry_prism/rest** | Sentry monitoring structures |

### `schem_files/legacy/` — Archived Schematics

Older builds preserved from pre-Emerald Mirror era:
- `castle-vonbarron.schematic` — Castle reference build
- `mc-tower.schematic` / `old-home.schematic` — Early tower/home prototypes
- `small-medium-castle.schematic` — Medium castle variant
- Numbered legacy files (7906, 16931, 17404, 17410)

### `input/` — Reference Data

| File | Purpose |
|------|---------|
| `master_prompt_reference_v2.md` | Master prompt spec for AI-assisted generation |
| `build_history.json` | Build deployment history and tracking |
| `README.md` | Skynet Architect documentation — dual-inference architecture, v7 Void-Tech standards |

### `builders/` subfiles (detailed)

| Module | Role |
|--------|------|
| `bank.py` | Grand bank with full interior builder |
| `bridge.py` | Span/bridge structure generator |
| `castle.py` | Castle/fortress procedural builder |
| `cyberdyne.py` | Cyberdyne tower (Void-Tech aesthetic) |
| `decoration.py` | Decorative element placement |
| `house.py` | House/cabin structure builder |
| `interiors.py` | Room templates and interior furnishing |
| `primitives.py` | Low-level building primitives |
| `station2.py` | High-fidelity industrial station (v5 standards) |
| `t2bm_expander.py` | T2BM Interlayer Protocol — intent → voxel mapping |
| `terrain.py` | Terrain shaping and greebling |
| `tower.py` | Vertical tower structure generator |
| `wall.py` | Perimeter wall builder |

---

## v5 Industrial Standards (Emerald Mirror)

All schematics must adhere to the following specifications:

- **Voxel Density**: Minimum bounding box of 20×15×25 for geometric detail resolution
- **Rule of Three**: Mandatory Base Layer → Structural Pillar Layer → Accent Girder Layer (prevents flat surfaces)
- **Fluted Pillars**: 3×3 footprint with `purpur_pillar` cores surrounded by oriented stairs for recessed shadowing
- **Industrial Lighting**: `pearlescent_froglight` at girder intersections (purple-white temperature glow)
- **Grid-Iron Girders**: Intersecting beams using `dark_prismarine` + `warped_fences`

### Void-Tech Tier Standards (v7+)

- **Foundation**: Polished/Chiseled Tuff and Calcite
- **Energy**: Crying Obsidian and Tinted Glass housing redstone cores
- **Girders**: Dark Prismarine suspended via lightning rods + end rods
- **Kinetic Logic**: Sculk Sensors linked to Copper Bulbs for proximity bioluminescence
- **Economic Integration**: Crafter blocks ("Hydro-Pods") every 20m on bridges

---

## Delivery & Deployment

### Injection Throttling
To maintain a stable **20 TPS target**, all block injections must implement a **0.05s delay per block**. Kinetic rail variant uses optimized 0.005s/block via Hailo-8L throughput.

### RCON Configuration
Environment variables required:
- `CHONK_IP` — Minecraft server address (`10.10.8.60`)
- `RCON_PASS` — RCON password (use `direnv`; never hardcode)
- `RCON_PORT` — Default 25575

### Workflow

1. Create JSON prompt in `prompts/`
2. Run: `python generate_schematic.py prompts/my_build.json`
3. Output `.schem` + `.json` written to `schem_files/`
4. Validate: `python validate_no_overlaps.py`
5. Deploy: `python batch_deploy.py` (auto-pushes to chonk via RCON)

### Schematic Format

Uses **Sponge Schematic v3** format (`.schem`) compatible with WorldEdit. Each build has a paired `.json` metadata file.

---

## Emergency / Safety Checks

- **AABB Overlap**: `validate_no_overlaps.py` must pass before any deployment
- **Vision Overseer**: Edge TPU aesthetic validation runs pre-deployment on complex structures
- **TPS Monitor**: Deployment throttles below 18 TPS during heavy building cycles
- **RCON Permissions**: Verify RCON user has `/setblock` execution rights

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
