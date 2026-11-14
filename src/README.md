# src/ — Source Code Index

The `src/` directory is the operational heart of the **game-skynet-minecraft** project: a distributed, AI-driven Minecraft infrastructure built around the cyber-noir "Dreamland" theme. Each subdirectory encapsulates a distinct subsystem within the broader Skynet cluster control plane.

Below is an overview of every source folder.

---

## Core Orchestrators

### `skynet/` — Skynet Unified Brain
The primary AI orchestration layer for NPU-accelerated spatial inference and build coordination. Contains the main daemon (`skynet-daemon.py`), core logic (`skynet_core.py`, `skynet_unified.py`), controller agents (`skynet_controller.py`, `skynet_agent.py`, `skynet_self_aware.py`), and the neural push-button engine (`npu_spatial_engine.py`). Deployed via `deploy.sh`.

### `stargate/` — Stargate MCP Node
The Model Context Protocol server that bridges AI reasoning with Minecraft server-side tools (RCON, WorldEdit). Includes telemetry listeners (`telemetry_listener.py`) and cart-trigger handlers for real-time redstone/minecart event processing. Runs on Hub-01 (Stargate), listening for signals from the Chonk host.

### `schematics/` — Schematic Generation & Deployment
The operational hub for AI-generated Minecraft builds. Organized into:
- **Build generators** (`builders/`) — procedural builders for towers, bridges, houses, cyberdyne structures, interiors, terrain, walls, and the T2BM expander.
- **Injectors** (`inject_*.py` / `process_*.py`) — scripts that push generated schematics into the live world (monoliths, chronosplicer, cooling arrays, pulse relays, stabilizers).
- **Rail pathfinders** (`neural_bridge_v7.py`, `neural_bridge_v8_pathfinder.py`, `kinetic_rail_v5.py`, `neural_rail.py`) — A\*-style rail routing with NPU acceleration.
- **Prompts/** — JSON build prompts for each schematic type (crafter hubs, sentry prisms, growth chambers, noodle exchanges, etc.).
- **schem_files/** — Generated `.schem` + `.json` output artifacts and legacy schematics.
- **input/** — Build history logs (`build_history.json`) and master prompt references.

---

## Inference & Hardware

### `models/` — Neural Core Models
Dual-inference assets for the Skynet v7.1-RECLAMATION ecosystem:
- **Hailo-8L NPU**: `yolov8s_h8l.hef` — spatial density mapping and build site selection.
- **Edge TPU (USB)**: `vision_v1.tflite` — real-time aesthetic validation ("Black Ice" style compliance).

### `edge-t/` — Edge-T Tactical Node
Raspberry Pi 5 + Google Coral TPU USB configuration for the Skynet fabricator node. Includes the daemon (`edge-t-daemon.py`), decoration script, and systemd service files. Dedicated to high-density geometric expansion and reactive mutation verification.

### `jetson/` — Jetson Cluster
NVIDIA Jetson nodes for CUDA-accelerated voxel processing. Contains notes on cluster integration.

### `pycoral/` — Google Coral TPU Support
Coral USB Accelerator datasheet and notes for the Edge TPU integration path. Used alongside the Hailo-8L in hybrid inference mode.

### `hardware.txt`
Host registry mapping: IP addresses, ports, and roles for all cluster nodes (Stargate MCP, Skynet Core, Edge-T Node) plus bus mappings for RCON bridge and BlueMap API.

---

## Data & Infrastructure

### `database/` — Neural-Data Vault (MariaDB)
Sync infrastructure for the centralized MariaDB instance on the **blowfish** host (Hub-07). Contains:
- `sync_vault.py` — data synchronization logic.
- `vault_manager.py` — vault operations and backup coordination.

### `mapping/` — BlueMap Telemetry & Spatial Validation
Scripts and assets for managing the live BlueMap visualization interface:
- `bluemap_api.py` — dynamic marker injection for landmarks.
- `bluemap-linter.py` / `bluemap_linter.py` — map linting utilities.
- `verify_ai_field_coords.py` — coordinate validation for AI testing field hubs.
- `mapping.html` / `mapping.md` — front-end assets and documentation.

### `rail/` — Rail Network Management
Deep rail network automation: route design (`rail_design.txt`, `rail_design2.txt`), telemetry receiver, rail manager, and the skynet_rail_control system. Connects hubs across the Bitsmasher cluster.

### `redstone/` — Redstone Circuit Design
Scripts for building and testing redstone circuit logic used by the automation pipeline.

---

## Vision & Analysis

### `vision/` — Visual Inference Pipeline
TPU-accelerated visual processing:
- `visual_inference.py` / `visualize_vault.py` — image analysis and vault visualization.
- `tpu_service.py` — TPU inference service wrapper.
- `vision_lite_overseer.py` / `vision_overseer.py` — oversight and validation of generated builds against aesthetic standards.

---

## Server Operations

### `mcrcon/` — RCON Bridge & Server Tools
Minecraft RCON protocol library and server management tools:
- `mc_rcon.py` / `mcrcon.py` — core RCON client.
- `minecraft_client/` — modpack configs (`mods.list`, `modpack.ver`, `servers.dat`) and auto-mod loader.
- `routes/routes.py` — web application routing layer.
- `server_tools/` — admin panel (`mc_gui.py`), server status, and RCON CLI utilities.

### `server_tools/` (skynet root) — Custom Server Utilities
Forge/modpack packaging helpers, client folder management, and additional server management scripts. Contains the full RCON command reference.

---

## Mod Development

### `plugin/net.bitsmasher.mod/` — FranklinMod / EchoCommandMod
Java Forge mod project for custom Minecraft server features:
- `EchoCommand.java` / `EchoCommandMod.java` — echo command implementation.
- `ExampleMod.java` / `FranklinMod.java` — registry events and mod initialization.
- Standard Gradle build (`build.gradle`, `gradlew`) with mod resources.

---

## Utilities & Configuration

### `utils/` — Shared Utilities
Configuration helpers (`config_utils.py`) and shared Python utilities used across multiple subsystems.

### `blowfish/` — Neural-Data Vault Documentation
MariaDB initialization scripts, credential management procedures (`.envrc`), and security documentation for the blowfish host (OpenBSD 7.8).

### `diagrams/` — Architecture Diagrams
Visual diagrams including the unified brain topology (`skynet_unified_brain.png`).

### `music/` — Note Block Registry
Music-related utilities: note block registry mapping (`note_block_registry.py`) for in-game audio design.

### `__init__.py` (root) & `logging.conf`
Package initialization and Python logging configuration — defines per-daemon loggers (skynet, stargate, vision_overseer, rail_manager, etc.) with console/file handlers and rotating file support.

---

## Cross-Cutting Concerns

| Concern | Location | Purpose |
|---------|----------|---------|
| Logging config | `src/logging.conf` | Per-daemon log routing (console + rotating file) |
| T2BM spec | `src/schematics/GEMINI.md` | Intent-to-block mapping ("Black Ice" protocol) |
| Hardware matrix | `src/hardware.txt` | Host registry & bus mappings for all cluster nodes |
| Deployment | `src/skynet/deploy.sh`, `src/mcrcon/server_tools/setup.py` | Service installation across hosts |
| Verification | `src/models/verify_models.py`, `src/mapping/verify_ai_field_coords.py` | NPU model health & coordinate validation |

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
