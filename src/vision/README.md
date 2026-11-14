# Vision — Visual Inference & NPU Pipeline

Edge TPU / Hailo-8L visual inference services for Minecraft world analysis, biome classification, and schematic aesthetic validation across Hub 06 (Mono-Eye Sensor) and Hub 01 (Skynet Inference Nexus).

---

## Architecture Overview

```
Hub 06 (Edge TPU Node, 10.10.16.4:8767)
    │
    ├── visualize_vault.py   → Flask API (:5000), biome classifier
    ├── visual_inference.py  → Standalone inference (biome_classifier_edgetpu.tflite)
    └── BlueMap tiles / screenshots  → image_path input
    │
    ▼
Stargate MCP Orchestrator (10.10.16.66:8765)
    │   receives { t2bm_environmental_prompt, hardware_accelerator, coordinates }
    │
Hub 01 (Skynet Core, 10.10.16.10:8766)
    └── vision_lite_overseer.py → human incursion scanning via RCON
    └── vision_overseer.py      → TPU MobileNetV2 inference engine
    │
    ▼
Skynet Vault / Schematics Pipeline
```

---

## Module Reference

### `visualize_vault.py` — Flask Vision API (Hub 06)

Flask service providing `/api/vision/infer` endpoint for biome-classification requests over the local network.

| Property | Value |
|----------|-------|
| Bind address | `0.0.0.0:5000` |
| Endpoint | `POST /api/vision/infer` |
| Model | `biome_classifier_edgetpu.tflite` |
| Labels | `models/biome_labels.txt` |
| Input | `{ "image_path": "chonk_telemetry/current_view_1212_670.jpg" }` |

**Response** (success):
```json
{
  "status": "success",
  "hardware": "edge_tpu",
  "hub": "06_mono_eye",
  "t2bm_environmental_prompt": "Design a building optimized for a ... environment. ..."
}
```

**Response** (error):
```json
{ "status": "failed", "error": "ERROR: TPU Hardware failure - ..." }
```

#### Internal Flow

1. Load `biome_classifier_edgetpu.tflite` via pycoral Edge TPU delegate
2. Load labels from `models/biome_labels.txt` (index → name mapping)
3. Resize input image to model input size using LANCZOS interpolation
4. Execute inference; top-2 classes with score ≥ 0.6
5. Translate classification into a T2BM environmental prompt string

---

### `visual_inference.py` — Standalone Inference Script

Standalone script for one-shot biome classification. Same pipeline as `visualize_vault.py` but invoked directly from CLI rather than over HTTP.

```sh
python visual_inference.py  # → requires target_image and coordinates to be set in source
```

**Target**: Hub 06 coordinates `(-1212, 76, -670)` — Mono-Eye Sensor sensor location.

---

### `vision_lite_overseer.py` — Human Incursion Scanner

Simulated USB Edge TPU 'Visual Cortex' that scans Minecraft chunks for non-Skynet (human) block presence using RCON queries.

```python
from vision.vision_lite_overseer import VisionLiteOverseer

overseer = VisionLiteOverseer()
state, score = overseer.scan_area(-1147, -621)  # returns ("INTENSION_HIGH", 7)
```

| Property | Value |
|----------|-------|
| Detection method | RCON `execute if block` probes for human blocks |
| Sampled blocks | `oak_planks`, `cobblestone`, `torch`, `glass_pane`, `chest`, `crafting_table` |
| Scan area | 15 random points in `{radius}x{radius}` around (x, z) |
| Y-level range | `FIELD_BOUNDS.y_base - 1` to `+8` (desert floor vicinity) |

**Classification thresholds**:

| Incursion Score | State | Meaning |
|-----------------|-------|---------|
| ≥ 5 | `INTENSION_HIGH` | Active human presence — trigger mutation / response |
| ≥ 2 | `CLASS_B_INCURSION` | Moderate human activity — flag for review |
| < 2 | `PRISTINE` | No significant human presence detected |

**Note**: This is a *simulated* inference — it uses RCON block probes rather than actual TPU vision processing. The actual TPU path goes through `vision_overseer.py`.

---

### `vision_overseer.py` — TPU MobileNetV2 Inference Engine

Real Edge TPU inference using MobileNetV2 (bird/insect classification model repurposed for Minecraft tile analysis).

| Property | Value |
|----------|-------|
| Model | `mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite` |
| Hardware lib | `/usr/lib/aarch64-linux-gnu/libedgetpu.so.1` |
| Input size | 224×224 RGB |
| Library | `tflite_runtime.interpreter` with Edge TPU delegate |

```python
from vision.vision_overseer import run_skynet_vision

result_index = run_skynet_vision("bluemap_tile_123.jpg")  # → argmax class index
```

---

### `tpu_service.py` — (Status unclear)

Referenced in the directory but code not inspected here. May be a TPU device management or health-check utility.

---

## Data Flow — T2BM Visual Constraint Pipeline

1. **Image capture** — BlueMap tile or screenshot at target coordinates
2. **TPU inference** (`visualize_vault.py` or `visual_inference.py`) → biome classification
3. **Prompt generation** — classification mapped to `{biome} environmental constraint string`
4. **Transmission** — POST to Stargate MCP:
   ```json
   {
     "hardware_accelerator": "edge_tpu",
     "hub": "06_mono_eye",
     "coordinates": { "x": -1212, "y": 76, "z": -670 },
     "t2bm_environmental_prompt": "...",
     "directive": "refine_t2bm_generation"
   }
   ```
5. **Stargate** passes constraint to LLM → generates biome-aware schematic prompt

---

## Model Files

| File | Purpose | Input Size | Framework |
|------|---------|-----------|-----------|
| `biome_classifier_edgetpu.tflite` | Biome/environment classification | Model-dependent (pycoral) | pycoral / Edge TPU |
| `mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite` | Tile/image classification | 224×224 | tflite_runtime + Edge TPU |
| `biome_labels.txt` | Biome label index mapping | N/A | Text (index → name) |

---

## Deployment

### Run the Flask Vision API (Hub 06):

```sh
cd /home/franklin/workspace/gaming/game-skynet-minecraft/src/vision
python visualize_vault.py
# Flask running on 0.0.0.0:5000
```

### Query from Stargate/Chonk:

```bash
curl -X POST http://10.10.16.4:5000/api/vision/infer \
  -H "Content-Type: application/json" \
  -d '{"image_path": "chonk_telemetry/current_view_1212_670.jpg"}'
```

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
