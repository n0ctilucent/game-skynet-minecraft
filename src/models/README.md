# Models — Inference Assets

Neural network models and inference utilities for the Skynet ecosystem, serving spatial density mapping (Hailo-8L NPU) and visual classification (Edge TPU).

---

## Directory Structure

```
src/models/
├── models.py         ── Gemini model listing utility
├── verify_models.py  ── Health check script for Neural Core assets
├── __init__.py       ── Empty package marker
└── hailo/
    └── yolov8s_h8l.hef  ── YOLOv8s object detection model (Hailo NPU)
```

---

## Model Inventory

### `yolov8s_h8l.hef` (Hailo-8L NPU)

| Property | Value |
|----------|-------|
| Location | `src/models/hailo/yolov8s_h8l.hef` |
| Size | **35 MB** |
| Framework | Hailo HEF (Hailo Executable Format) |
| Origin | Symlinked from `/usr/share/hailo-models/yolov8s_h8l.hef` |
| Role | Spatial density mapping and cluster inference for build site selection |

**What it does**: Object detection / spatial analysis that drives the NPUSpatialEngine's density calculations across the Minecraft world. Feeds into the NPUSpatialEngine's `get_optimal_vector` method which performs 10x10 block grid resolution sampling.

### `mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite` (Edge TPU)

| Property | Value |
|----------|-------|
| Location | Referenced but **not present** in this directory — likely stored elsewhere or generated at runtime |
| Framework | TensorFlow Lite, quantized for Edge TPU |
| Input size | 224×224 RGB |
| Role | Real-time visual inference via `vision_overseer.py` and `visualize_vault.py` |

**Note**: The current README claimed a local `vision_v1.tflite` model. This was inaccurate — the actual model is MobileNetV2 (bird/insect taxonomy) used for biome classification, consumed by the Hub 06 vision pipeline documented in `src/vision/README.md`.

---

## Utilities

### `verify_models.py` — Neural Core Health Check

Validates that required inference assets are present and reports sizes:

```bash
python3 src/models/verify_models.py
# --- Skynet Neural Core Health Check ---
# ✅ FOUND [Spatial Inference (Hailo-8L)]: yolov8s_h8l.hef (34.92 MB)
# ❌ MISSING [Visual Cortex (Edge TPU)]: mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite
# ⚠️ Neural Core status: DEGRADED
```

**Checks**:
- `yolov8s_h8l.hef` in `src/models/hailo/` — must exist (35 MB)
- `mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite` in `src/models/` root — may be missing or symlinked

**Exit code**: 0 = OPTIMAL, 1 = DEGRADED

### `models.py` — Gemini Model Listing

Utility that lists available Google Gemini models via the Gemini API:

```python
# src/models/models.py
from google import genai
import os

api_key = os.getenv("GEMINI_API_KEY")  # Required
client = genai.Client(api_key=api_key)
for model in client.models.list():
    print(model.name)
```

> **Requires**: `GEMINI_API_KEY` environment variable. No pip dependency beyond `google-genai`.

---

## Dual-Inference Architecture

The system uses two parallel inference paths:

| Path | Hardware | Model | Location | Purpose |
|------|----------|-------|----------|---------|
| Spatial Density | Raspberry Pi 5 + Hailo-8L NPU | `yolov8s_h8l.hef` | `hailo/` | Build site selection, world density mapping |
| Visual Inference | USB Edge TPU | MobileNetV2 (quantized) | Hub 06 | Biome classification, schematic aesthetic validation |

Both paths feed into the **T2BM pipeline** — spatial results determine *where* to build, visual results determine *what style* fits the environment.

---

## Integration Points

| Consumer | Model Used | Path |
|----------|-----------|------|
| `npu_spatial_engine.py` (src/npu/) | YOLOv8s Hailo HEF | Spatial density queries via HailoRT |
| `vision_overseer.py` (src/vision/) | MobileNetV2 TFLite | Edge TPU delegate inference |
| `visualize_vault.py` (src/vision/) | Biome classifier TFLite | pycoral Edge TPU pipeline |
| `skynet_core.py` (src/schematics/) | Via `adaptive_mutation_v7.py` | Aesthetic validation gate |

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
