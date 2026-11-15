# Rail Module — Automated Railway Control & Telemetry

Automated rail infrastructure for the Skynet control plane. Manages railway switching via RCON, synchronizes live switch states with BlueMap POI markers, and processes real-time telemetry from cart sensors across the Bitsmasher cluster.

---

## Architecture

```
Hub-01 (Stargate)     Hub-00 (Skynet)         Hub-06 (Edge-T)
   LLM Traffic           Hailo-8L Path           Edge TPU Safety
   Orchestration        Optimization            Verification
       │                      │                      │
       └──────────┬───────────┴──────────────────────┘
                  │
          Rail Telemetry Layer
     ┌────────────┼─────────────┐
     ▼            ▼             ▼
  rail_mgr   skynet_ctl    telemetry_rx
```

| Node | Role |
|------|------|
| **Hub-01 (Stargate)** | LLM-based traffic orchestration — determines train priority and switch scheduling |
| **Hub-00 (Skynet)** | Hailo-8L NPU path optimization for multi-chunk rail systems (target: maintain 20 TPS) |
| **Hub-06 (Edge-T)** | Edge TPU entity proximity verification — aborts switch state changes if players/mobs are within 3 blocks |

---

## Components

### `rail_manager.py` — Core Rail Manager

Asynchronous rail management class with three primary responsibilities:

1. **RailRegistry** — Loads and watches `config/rail_registry.json`, maintaining a "digital twin" of all switch UUIDs, coordinates, names, and current states. Detects file changes automatically.
2. **MarkerManager** — Manages BlueMap `markers.json` POI entries for rail switches with dynamic color styling (green = active/primary route, red = inactive/siding).
3. **RailManager** — Coordinates RCON switch control: issues `/setblock <x> <y> <z> minecraft:powered_rail[powered=true/false]` commands via the rcon library and triggers verification loops on Edge-T.

### `skynet_rail_control.py` — Signal Tower Interface

Direct RCON bridge to Void-Tech signal towers at hub locations. Maps hub IDs to physical coordinates and toggles redstone blocks for zero-lag status transmission:

- **HUB_06** (-1212, 76, -670)
- **HUB_03** (-1283, 77, -658)

Uses `MCRcon` to connect to the Stargate node and send block state commands.

### `telemetry_receiver.py` — Cart Event Processor

Listens for rail cart trigger events (`CART_PASS`, sensor triggers, etc.) from detector rails across the network. Processes them through LLM orchestration to determine switch actions and priority routing. Logs to `logs/rail_traffic.log`.

### `containment_rail_builder.py` — Containment Rail & Corner Generator

Procedural 90° corner synthesis engine for `ai_containment_zone_alpha`:
- Enforces standard unpowered `minecraft:rail[shape=...]` on inert `minecraft:polished_deepslate` roadbed at $Y=63$.
- Computes canonical curved shapes (`south_east`, `south_west`, `north_west`, `north_east`).
- Emits Sponge `.schem` files for all four perimeter corners and the AI Lab Gateway interface spur.

### `deploy_containment_rail_corners.sh` — RCON Corner Deployment Script

Batch RCON script applying the four orbital loop corners and building spurs directly to PaperMC.

### `containment_transit_loop.py` — Containment Orbital Rail Generator & Deployer

Autonomous transit loop pathfinder and viaduct builder for `ai_containment_zone_alpha`:
- Connects 30 perimeter stations (including `SKYNET_QUANTUM_FOUNDRY_NODE901` and `end_industrial_station_v5`) into a closed 2.1 km bi-directional double-track transit circuit.
- Uses A* Manhattan routing with building bounding-box obstacle avoidance.
- Synthesizes 5-block wide industrial viaducts featuring:
  - Polished deepslate foundations & dark prismarine wall curbs
  - Dual powered rail tracks powered by embedded redstone blocks
  - Standard rail curved turns and pearlescent froglight median illumination
  - 3-block vertical clearance envelope preventing player suffocation
- Synchronizes station metadata and route topology with `config/rail_registry.json`.

### `rail_design.txt` / `rail_design2.txt` — Design Specifications

Architectural specifications for the automated rail system:
- Signal implementations (lamp signals, block swapper)
- RCON switch control protocol
- BlueMap POI integration requirements
- Hardware task allocation across the cluster
- TPS-aware scheduling thresholds (non-essential delays below 18.0 TPS)

---

## Data Flow

1. **Cart trigger** on detector rail → telemetry event published
2. **TelemetryReceiver** receives event, queries LLM at Hub-01 for routing decision
3. **Hailo-8L** at Hub-00 calculates optimal multi-chunk path
4. **Edge-T** at Hub-06 runs entity proximity check (abort if player/mob within 3 blocks)
5. On clearance, RCON sends `/setblock` to toggle the switch
6. Edge-T performs vision verification of block state change
7. BlueMap POI markers updated with new active/inactive color

---

## Configuration

| File | Purpose |
|------|---------|
| `config/rail_registry.json` | Switch registry (UUID, coords, name, state) — digital twin |
| `logs/rail_traffic.log` | Cart event and LLM orchestration logs |
| `logs/rail_safety.log` | Safety interlock events and proximity aborts |

---

## Signal Options (Design Reference)

### Option 1: Simple Lamp Signal
Detector rail → Redstone torch/torch chain → Red/Green lamp pair. Use redstone repeaters for signal timing. Best for simple one-way track segments.

### Option 2: Block Swapper
Two sticky pistons (green/red wool) controlled by RS-NOR latch with dual detector rails. Provides mechanical "flip-flop" visual at stations. Better for bidirectional tracks requiring pulse extenders.

---

## Next Steps

- Populate `config/rail_registry.json` with primary switch coordinates (Washington Station, Deep-Rail Project vertical transitions)
- Implement automated discovery: scan WorldEdit/schematic logs to auto-populate registry on new build deployment
- Add TPS-aware scheduling to Stargate orchestration layer
- Verify RCON user permissions for `/setblock` execution

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
