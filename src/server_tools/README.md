# Server Tools — Minecraft Infrastructure Scripts

Direct RCON, status monitoring, and GUI tools for managing the Dreamland Minecraft server at `10.10.8.60:25575`.

---

## Files

### `mcrcon.py` — MCRCON Client

Thin wrapper around the mcrcon protocol for Python-based RCON communication. Used by all other tools in this directory and upstream (`rail/skynet_rail_control.py`, `server_tools/main.py`).

```python
from mcrcon import MCRcon
with MCRcon("10.10.8.60", os.environ["MC_PASS"]) as mcr:
    resp = mcr.command("/whitelist add bob")
```

### `main.py` — Entry Point / Sample

CLI entry point demonstrating RCON usage (adds a player to whitelist). Expects `MC_PASS` environment variable or falls back to config default.

- **Port:** 25575 (RCON)
- **Auth:** `MC_PASS` env var on chonk

### `status.py` — Java Server Probe

Uses `mcstatus` library to poll the server for online player count and latency. Targets `10.10.8.60:25565`.

```python
from mcstatus import JavaServer
server = JavaServer.lookup("10.10.8.60:25565")
status = server.status()  # players.online, latency (ms)
```

### `mc_gui.py` — Tkinter Status Dashboard

Matplotlib-backed GUI that graphically displays server status (player count, latency) with periodic refresh via threaded updates. Configurable `SERVER` and `REFRESH` interval (default: 30s).

### `requirements.txt` — Dependencies

Python package requirements for this module (mcstatus, mcrcon, tkinter/matplotlib if running GUI).

---

## Hardware & Topology Reference

| Service | Host | Port |
|---------|------|------|
| RCON Bridge | 10.10.8.60 | 25575 |
| BlueMap API | 10.10.8.60 | 8100 |
| Stargate MCP | 10.10.16.66 | 8765 |
| Skynet Core | 10.10.16.10 | 8766 |
| Edge-T Node | 10.10.16.4 | 8767 |

---

## RCON Command Reference (from MCRCON)

Full command list available via `/help` on the server. Key commands:

| Command | Description |
|---------|-------------|
| `/ban /pardon` | Player ban/unban |
| `/ban-ip /pardon-ip` | IP ban/unban |
| `/whitelist` | Manage whitelist |
| `/op /deop` | Operator management |
| `/gamemode` | Change player gamemode |
| `/tp` | Teleport players |
| `/kill` | Kill entity/player |
| `/kick` | Remove player from server |
| `/time /weather /difficulty` | Server state changes |
| `/save-all /save-on /save-off` | World save control |
| `/plugins` | List loaded plugins |
| `/timings` | Performance profiling |
| `/seed` | World seed |
| `/spawnpoint /setworldspawn` | Spawn management |
| `/give` | Item distribution |
| `/tell /say /me` | Chat/messaging |

---

## Setup

```sh
cd /home/franklin/workspace/gaming/game-skynet-minecraft/src/server_tools
python3 -m venv _test
. _test/bin/activate.fish  # or bin/activate for bash
pip install -r requirements.txt
```

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
