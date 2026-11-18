# 🍄 D R E A M L A N D

Welcome to a world that bridges over a decade of history with the cutting edge of AI-driven Minecraft engineering. 

[![View Slides](https://img.shields.io/badge/Presentation-Download_PDF_(v2)-blue?logo=adobe-acrobat-reader&logoColor=white)](https://github.com/n0ctilucent/game-skynet-minecraft/blob/main/docs/slides/quest-for-greebling-v2.pdf) [![Bandit Security Scan](https://github.com/n0ctilucent/game-skynet-minecraft/actions/workflows/bandit.yml/badge.svg)](https://github.com/n0ctilucent/game-skynet-minecraft/actions/workflows/bandit.yml)

![tech void nihilism as software architecture](https://github.com/n0ctilucent/game-skynet-minecraft/blob/main/static/images/skynet_unified_brain_architecture.png)

## 🌐 Server Information
*   **Server Address:** `minecraft.bitsmasher.net`
*   **Version:** Paper 1.21.1 / 26.2 (Java 21)
*   **Web Map (BlueMap):** [Click Here to View Port 8100](https://minecraft.bitsmasher.net:8100)
*   **Established:** 2012

## 🎮 How to Join

### **Java Edition (Recommended)**
1.  Launch Minecraft **Java Edition 1.21.1**.
2.  Click on **Multiplayer** then **Add Server**
3.  Enter `minecraft.bitsmasher.net` in the Server Address field
4.  Join and start your journey at **Washington Station (The Zero Point)**

## ✨ Current Features
*   **AI Containment Zone Alpha:** A 25.2-hectare testing field ($X \in [-1539, -945], Z \in [-913, -489]$) containing 237 active AI-generated structures.
*   **The Grand Orbital Transit Loop:** A 2.1 km bi-directional double-track automated scenic railway encircling the containment field, interconnecting 30 passenger stations and industrial landmarks via [`src/rail/containment_transit_loop.py`](file:///home/franklin/workspace/gaming/game-skynet-minecraft/src/rail/containment_transit_loop.py).
*   **The Deep-Rail Project:** Experience vertical logistics connecting the **Rail Yard (Y:63)** to the **Deep Station (Y:31)**.
*   **High-Detail Greebling & 5-Layer Reliefs:** Advanced architectural primitives with fluted pillars, stepped buttresses, external copper/deepslate conduit manifolds, rooftop HVAC chillers, and apex telemetry spires with pearlescent froglight pulse cores.
*   **Multi-Node Hardware Synthesis:** Next-generation flagship structures synthesized remotely on NVIDIA Jetson GPU hardware (`node901`), including the 45-block **Signal Siphon** and the 32-block **Quantum Foundry**.
*   **Emerald Mirror Pipeline:** A distributed AI pipeline that evolves the world through context-aware architectural greebling and spatial mutation.

## 🧠 AI Infrastructure
The Bitsmasher network operates as a **Distributed Neural Engine**, utilizing a multi-node control plane to manage autonomous urbanization while maintaining a strict **20 TPS** server performance target.

*   **Skynet (Hub-00):** Orchestrator & Vertex Gateway. Powered by a Raspberry Pi 5 with Hailo-8L NPU (13 TOPS) for spatial inference, A* pathfinding, procedural voxel generation, and batch RCON deployment.
*   **Stargate (Hub-01):** Control Plane and RCON proxy. Specialized in **Macro-Schematic Orchestration** via FastMCP (port 8989), telemetry event routing (port 5005), and T2BM WebSocket intent dispatch (port 8765).
*   **Edge-T (Hub-06):** Vision Overseer. Specialized in **Greebling Density Verification** using the Google Edge TPU to ensure aesthetic compliance and real-time rail proximity safety interlocks.
*   **Jetson Cluster (Node 901–904):** NVIDIA Jetson nodes responsible for CUDA-accelerated **Heavy Voxel Math**, spatial clustering, and hardware-accelerated synthesis of heavy brutalist spires and industrial foundries.
*   **Chonk (Host):** AMD Ryzen 9 9950X3D server hosting Paper 1.21.1 production runtime, WorldEdit console execution, and local Ollama inference.

## 🛠️ Critical Infrastructure & Operations
*   **ClusterFS Dependency:** The Hailo-8L NPU (Skynet) and Edge TPU (Edge-T) require a stable **ClusterFS mount** over `eth0` for shared vision datasets, spatial logs, and schematic exchange (`/home/minecraft/schematics/`).
*   **Throttled WorldEdit Deployment:** High-density batch placements run via [`src/schematics/batch_containment_deploy.py`](file:///home/franklin/workspace/gaming/game-skynet-minecraft/src/schematics/batch_containment_deploy.py), utilizing WorldEdit console sessions (`//world world`, `//schem load`, `//paste -a`) and dynamic TPS throttling (auto-pausing if TPS drops below 18.5) to deploy hundreds of structures at 20.0 TPS.
*   **Autonomous Rail Management:** The [`src/rail/`](file:///home/franklin/workspace/gaming/game-skynet-minecraft/src/rail/) suite manages digital-twin switch synchronization ([`config/rail_registry.json`](file:///home/franklin/workspace/gaming/game-skynet-minecraft/config/rail_registry.json)), BlueMap marker updates, and A* collision-free viaduct routing.

For instructions on running local models (like Llama 3.1) on the Stargate node, see:
👉 **[Ollama Integration Guide](docs/OLLAMA.md)**

For full system architecture, see the canonical server manual at:
👉 **[`/home/minecraft/docs/manual/`](file:///home/minecraft/docs/manual/)**

![tech void nihilism as building fashion](https://github.com/n0ctilucent/game-skynet-minecraft/blob/main/static/images/infographic.png)
