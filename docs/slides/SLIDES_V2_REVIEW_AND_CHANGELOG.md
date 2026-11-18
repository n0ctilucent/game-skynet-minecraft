# Presentation Review & "v2" Slides Architecture
**Document:** `docs/slides/SLIDES_V2_REVIEW_AND_CHANGELOG.md`  
**Project:** *The Quest for Greebling — Recreational AI Orchestration of Minecraft Activities*  
**Date:** November 2026  
**Author:** Franklin D. / Bitsmasher Minecraft AI Research  

---

## 1. Executive Summary

This review audits the original slide deck (`quest-for-greebling.tex`, `preamble.tex`, and `Makefile.am`) located in `docs/slides/`. Based on our codebase evolution (including the **Emerald Mirror pipeline**, **v5 Industrial aesthetic**, **dual-grade railway network**, **urban greebler**, and **Coral TPU safety interlocks**), a complete **v2 release** of the presentation has been engineered and compiled directly into `docs/slides/`:

* **`preamble-v2.tex`**: Modern 16:9 Beamer configuration with high-contrast theme, custom blocks, TikZ flow architecture, and syntax-highlighted code listings.
* **`quest-for-greebling-v2.tex`**: Comprehensive 25-slide presentation with strict structural flow, detailed technical explanations, speaker notes, and 100% `chktex` compliance.
* **`quest-for-greebling-v2.pdf`**: Production-ready, 25-page vector-rendered PDF presentation.
* **`Makefile.am` & `Makefile`**: Updated build targets (`make pdf-v2`, `make lint-v2`, `make all-slides`).

---

## 2. Comprehensive Audit of Legacy (v1) Slide Deck

### 2.1 Theme & Visual Styling Collisions
* **Conflicting Beamer Themes:** `quest-for-greebling.tex` loaded `\usetheme{Antibes}` (which uses a tree-based navigation header), while `preamble.tex` configured color overrides for `Madrid`-specific footers (`author in head/foot`, `title in head/foot`). This mismatch produced rendering anomalies and suppressed frame numbers.
* **Aspect Ratio:** The legacy deck used default 4:3 aspect ratio, causing awkward squishing on standard 16:9 displays and projectors.
* **Presenter Notes Contrast:** The template set `\pagecolor{yellow!5}` with off-white text, rendering notes completely unreadable during dual-screen presentations.
* **Raw Paragraphs vs. Visuals:** Several key slides (e.g., *What is a Greebling?*) presented unformatted walls of text without structural hierarchy or block styling.

### 2.2 Structural Flow & Sequencing Flaws
* **Informal Section Headers:** Slide 122 introduced Section 3 as `"party time"`, undermining the technical depth of the distributed systems architecture.
* **Orphaned Hardware Slide:** Slide 217 (*Hardware Specification: The Hailo-8L Cluster*) was placed *after* Slide 210 (*Thank You!*), followed by a second closing slide (*Questions?*).
* **Sparse Control Plane Details:** Slide 116 (*Pi-5 (stargate)*) contained a single bullet point (`Raspberry Pi5 8GB RAM...`) without explaining its role as the FastMCP hub, neural router, or telemetry listener.

### 2.3 Factual Gaps & Outdated Architecture
* **Missing Jetson Cluster Nodes:** The legacy slides omitted the Jetson Orin cluster (`10.10.12.90–.93`, Edge-J), which handles CUDA-accelerated voxel refinement and delta slicing.
* **Conflicting NPU Specifications:** Slide 107 cited Hailo-8 as `26 TOPS (INT8)`, while Slide 226 cited `13 TOPS per Node` (Hailo-8L) without clarifying the cluster configuration.
* **Omission of the Emerald Mirror Pipeline:** The 4-stage pipeline (Inference $\rightarrow$ Refinement $\rightarrow$ Validation $\rightarrow$ Throttled Injection) was not documented in the slides.
* **Absence of Modern Rail & Urban Features:** Recent major codebase milestones were completely missing from v1:
  1. *Dual-Grade Adaptive Rail Profile* (Ground $Y=64$ vs. Arched Masonry Viaducts with corbels, haunches, and $2\times 2$ piers).
  2. *Station Terminal Pavilions* ($5 \times 7$ covered termini with spruce boarding gates).
  3. *Post-Build Urban Greebler* (street infrastructure, hydrants, benches, HVAC mechanicals).
  4. *Intelligent Villager Population* (workstation-to-profession mapping).
  5. *Coral TPU Vision Safety Daemon* (`check_safety` on port 8808) and Digital Twin (`config/rail_registry.json`).

### 2.4 Code Quality & Build Automation
* **`chktex` Lint Failures:** Running `chktex -q quest-for-greebling.tex` failed with 23 warnings (unescaped double quotes `"` instead of ```` ``, informal ellipses `....`, unescaped braces in `\texttt`, and overfull horizontal boxes).
* **QR Code Overflows:** The repository URL on the closing slide overflowed the bounding box by 58 points.

---

## 3. The "v2" Slide Architecture & Improvements

### 3.1 Design System & Typography (`preamble-v2.tex`)
* **Aspect Ratio:** Standardized to widescreen `aspectratio=169` (1920x1080 native).
* **Color Palette:**
  * **Slate Background:** `#141821` (reduces eye fatigue, optimizes OLED/projector contrast).
  * **Electric Cyan Accent:** `#00d2ff` (headers, primary components, section breaks).
  * **Emerald Mirror Green:** `#00e676` (validation pipelines, successful states).
  * **Warning Amber:** `#ffb300` (watchdogs, safety interlocks).
  * **Deep Card Slate:** `#1e2533` (isolated content blocks).
* **Listings Environment:** Custom monospace styling with subtle border and dark background for Minecraft command payloads, bash invocations, and JSON schemas.
* **Readable Notes:** High-contrast presenter note page layout.

### 3.2 Slide Deck Structure (`quest-for-greebling-v2.tex`)

The v2 presentation is organized into 7 cohesive technical sections across 25 frames:

```mermaid
flowchart LR
    A["1. Vision & Greebling"] --> B["2. Distributed Hardware"]
    B --> C["3. In-World Telemetry"]
    C --> D["4. Emerald Mirror"]
    D --> E["5. Advanced Rail Transit"]
    E --> F["6. Urban Greebling"]
    F --> G["7. Safety & Digital Twin"]
```

#### Section 1: Vision & The Art of Greebling
1. **Title Slide:** High-resolution title branding with Franklin D., lab credentials (`minecraft.bitsmasher.net`), and repository metadata.
2. **Session Blueprint:** Two-column structured table of contents.
3. **What is Greebling? From Sci-Fi to Voxels:** Lucas/ILM Star Wars kitbashing origins, LEGO modular parallels, and the Minecraft voxel scaling challenge, paired with `images/SKYNET_TOWER_2196.png`.
4. **The Minecraft Schematic Paradigm:** Foundation schematics (skeletal anchors) vs. Delta schematics (air-wrapped decorative layers), paired with `images/SKYNET_HOUSE_5713.png`.

#### Section 2: Distributed Hardware Lab & Topology
5. **Physical Infrastructure:** 10-inch edge rack, 10G optical fiber backbone via UniFi Dream Machine, OpenBSD persistence (`blowfish`), paired with rack photo `images/20260421_082443.jpg`.
6. **Distributed System Topology:** Complete node breakdown (Chonk PaperMC, Stargate FastMCP, Skynet Hailo-8, Edge-T Coral TPU, Jetson CUDA cluster), paired with network map `images/greeblenet.png`.
7. **Edge Hardware Acceleration:** Direct side-by-side comparison of Hailo-8 M.2 (26 TOPS, INT8 `.hef` models) and Google Coral TPU (4 TOPS INT8 MDT daemon), featuring `images/AIHAT-26tops.png` and `images/asus-tinker-edge-t.png`.

#### Section 3: In-World Telemetry & Electronics
8. **World-Space Physical Detection & Bridging:** Detector rails, 1-tick repeater conditioning, command block `tellraw` JSON encapsulation, and async socket forwarding to Stargate port 5005.
9. **Zero-Tick Observer Signal Wall Architecture:** Instantaneous 0-tick vertical block update chains, physical dispatch (`STOP`/`CLEAR`), paired with `images/SKYNET_CASTLE_6945.png`.

#### Section 4: The Emerald Mirror Pipeline
10. **The 4-Stage World Evolution Pipeline:** Vector TikZ diagram showing Stargate Inference $\rightarrow$ Jetson Refinement $\rightarrow$ Skynet Hailo Validation $\rightarrow$ Chonk RCON Injection.
11. **Aesthetic Standard (v5 Industrial Palette):** Technical specification of fluted $3\times 3$ purpur pillars, dark prismarine girders, pearlescent froglights, and waxed copper temporal weathering, paired with in-game render `images/2026-03-23_15.41.46.png`.

#### Section 5: Advanced Rail Transit & Containment
12. **Dual-Grade Rail Architecture:** Ground level profile inside AI Containment Zone Alpha ($Y=64$) vs. Elevated Arched Masonry Viaducts (stone brick arches, corbels, haunches, $2\times 2$ piers, iron bar parapets), paired with `images/SKYNET_BRIDGE_1391.png`.
13. **Station Pavilions & Power Distribution:** $5 \times 7$ covered terminal pavilions, spruce boarding gates, 15-block redstone powering, and chunk-forceload batching, paired with `images/SKYNET_STATION_4478.png`.

#### Section 6: Urban Greebling & Autonomous Population
14. **Post-Build Urban Greebler Pipeline:** Procedural street infrastructure (lamps, hydrants, benches), human clutter (market stalls, tool racks), and rooftop HVAC chillers, paired with `images/2026-03-22_21.11.13.png`.
15. **Intelligent Workstation-to-Villager Population:** Demographic assignment mapping (smokers $\rightarrow$ butchers, blast furnaces $\rightarrow$ armorers, lecterns $\rightarrow$ librarians, stonecutters $\rightarrow$ masons) with TPS watchdog protection ($18.5$ baseline).

#### Section 7: Safety Interlocks & Verification
16. **Coral TPU Vision Interlock & Digital Twin:** Real-time entity clearance audit on `10.10.16.4:8808`, `rail_registry.json` digital twin state tracking, and pytest coverage.
17. **Roadmap & Autonomous Multi-Agent Swarms:** BlueMap visual feedback to Hailo-8, distributed Jetson swarm building, bi-directional redstone-to-hardware computing, paired with `images/Gemini_Generated_Image_xz297bxz297bxz29.png`.
18. **Project Resources & Discussion:** Clear contact links, open source stack summary, and vector QR code linking directly to the v2 slides.

---

## 4. Verification & Build Targets

### 4.1 Lint Verification (`chktex`)
The v2 TeX files achieve 100% documentation stability with zero errors or warnings:
```bash
$ cd docs/slides && make lint-v2
==> Initializing Skynet documentation audit (v2)...
==> Audit complete. Documentation stability: 100%
```

### 4.2 PDF Compilation
The v2 presentation compiles cleanly via `latexmk`:
```bash
$ cd docs/slides && make pdf-v2
latexmk -pdf -interaction=nonstopmode quest-for-greebling-v2.tex
...
Output written on quest-for-greebling-v2.pdf (25 pages, 31075801 bytes).
Latexmk: All targets (quest-for-greebling-v2.pdf) are up-to-date
```

---

## 5. Summary of Files in `docs/slides/`

| File | Status | Description |
| :--- | :--- | :--- |
| **`preamble-v2.tex`** | **New (v2)** | Modern 16:9 Beamer preamble, slate/cyan theme, listings & TikZ styling. |
| **`quest-for-greebling-v2.tex`** | **New (v2)** | 25-frame structured technical presentation source. |
| **`quest-for-greebling-v2.pdf`** | **New (v2)** | Compiled 25-page widescreen presentation. |
| **`SLIDES_V2_REVIEW_AND_CHANGELOG.md`**| **New (v2)** | Detailed review findings and v1 vs. v2 comparative changelog. |
| **`Makefile.am`** | **Updated** | Added `pdf-v2`, `lint-v2`, and updated `all-slides`/`clean-slides`. |
| **`Makefile`** | **Updated** | Synchronized with autotools build system for instant target execution. |
| `preamble.tex` | Legacy (v1) | Kept intact for historical reference and backward compatibility. |
| `quest-for-greebling.tex` | Legacy (v1) | Kept intact for historical reference and backward compatibility. |
| `quest-for-greebling.pdf` | Legacy (v1) | Kept intact for historical reference. |
