# mcrcon — RCON Client Library & Server Tools

RCON (Remote Console) infrastructure for interacting with Minecraft servers in the Bitsmasher network.

---

## Directory Structure

```
src/mcrcon/
├── mcrcon.py           ── Core MCRcon client library (MIT licensed, forked from uncaught-exceptions/mcrcon v0.7.0)
├── __init__.py         ── McUtils class — shared config constants
├── app.py              ── Flask web interface for server monitoring
├── mc_rcon.py          ── Quick-start RCON script
├── mc_server.py        ── McServer class — mcstatus wrapper for ping/status/query
├── routes/
│   └── routes.py       ── Route definitions (stub)
├── server_tools/
│   ├── main.py         ── Standalone RCON CLI entry point
│   ├── status.py       ── Server status script (JavaServer lookup)
│   ├── setup.py        ── Package metadata (publishes as mcrcon v0.7.0)
│   └── requirements.txt ─ dev dependencies: mcstatus, rcon
├── minecraft_client/
│   ├── automodloader.py ─ Auto-mod downloader for TLauncher (Windows)
│   ├── mods.list       ─ Mod download manifest
│   ├── modpack.ver     ─ Version file (0.0.1)
│   └── servers.dat     ─ Minecraft server registry
├── templates/          ─ Flask HTML templates (index, history, status)
├── static/             ─ Web assets (HTML, CSS, JS for web interface)
└── __pycache__/        ─ Compiled bytecode
```

---

## Core Library — `mcrcon.py`

MIT-licensed RCON client supporting TLS encryption and context-manager lifecycle.

### Class: `MCRcon`

| Property | Default | Description |
|----------|---------|-------------|
| `host` | required | Server hostname / IP |
| `password` | required | RCON password (also read from `RCON_PASSWORD` env var) |
| `port` | 25575 | RCON port |
| `tlsmode` | 0 | TLS: 0=off, 1=SSL, 2=SSL+skip cert verification |
| `timeout` | 5s | Connection timeout (SIGALRM on non-Windows) |

### Usage

```python
# Context manager (recommended)
from mcrcon import MCRcon

with MCRcon("10.10.8.60", "your_password") as rcon:
    resp = rcon.command("/whitelist add bob")
    print(resp)

# Manual lifecycle
rcon = MCRcon("host", "pass", port=25575, tlsmode=0)
rcon.connect()
resp = rcon.command("/tp @p 0 64 0")
rcon.disconnect()
```

### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(host, password, port=25575, tlsmode=0, timeout=5)` | Initialize client |
| `connect()` | `() -> None` | Establish TCP connection, send auth packet |
| `disconnect()` | `() -> None` | Close socket |
| `command()` | `(cmd: str) -> str` | Send RCON command, return response string |

### Protocol Details

- **Packet format**: `<4-byte length><4-byte ID><1-byte type><command>\0\0>`
- **Response parsing**: Iterative read until TCP window empty (`select.select`)
- **Error cases**: `-1` ID → login failed; bad padding → exception

### CLI Entry Point

```bash
mcrcon 10.10.8.60 --password "dinosaur"    # interactive REPL
mcrcon 10.10.8.60 -t                        # with TLS
export RCON_PASSWORD="pass"; mcrcon host    # env var password
```

---

## Server Tools (`server_tools/`)

### `main.py` — Quick RCON Script

Connects to localhost on port 25575, reads password from `MC_PASS` env var (default: fallback string). Sends a test `/whitelist add bob` command. Used for rapid debugging.

```sh
MC_PASS="real_password" python main.py
```

### `status.py` — Server Status Checker

Uses `mcstatus.JavaServer.lookup()` to query server status, latency, and player count. Hardcoded target: `10.10.8.11:25565`.

```sh
python status.py
# The server has N player(s) online and replied in X ms
```

Supports three mcstatus operations:
- **`status()`** — player count, MOTD, favicon (all 1.7+ servers)
- **`ping()`** — latency only
- **`query()`** — full player list + mod info (requires `enable-query=true` in server.properties)

---

## Web Interface (`app.py`)

Flask application providing three pages for server monitoring:

| Route | Template | Content |
|-------|----------|---------|
| `/`, `/minecraft` | `index.html` | Landing page |
| `/history` | `history.html` | Server operation history |
| `/status` | `status.html` | Live status: player count, latency, query results |

**Host config** (from `__init__.py.McUtils`):

| Property | Value |
|----------|-------|
| Minecraft IP | `10.10.8.11` |
| Minecraft port | `25565` |
| Flask port | `9001` |

```sh
python app.py  # → http://10.10.8.11:9001
```

Uses `McServer` class (`mc_server.py`) which wraps mcstatus `JavaServer` for status lookups.

---

## Minecraft Client Tools (`minecraft_client/`)

### `automodloader.py` — Mod Pack Downloader

Auto-downloads mods from GitHub manifest to TLauncher's mod directory on Windows (`%APPDATA%/.minecraft/mods`). Checks version file against remote, downloads changed mods using `pretty_downloader`.

> **Note**: Windows-only (uses `%APPDATA%`, `os.system("cls")`, hardcoded TLauncher path).

### `servers.dat` — Server Registry

Protobuf-encoded server list. Current entry:
- **Name**: Commodore Clown College
- **IP**: `minecraft.bitsmasher.net`

### `mods.list` / `modpack.ver`

Mod manifest (URLs) and version tracker for auto-sync.

---

## Key IPs & Ports

| Service | Address | Port |
|---------|---------|------|
| RCON (chonk) | `10.10.8.60` | 25575 |
| Minecraft server | `10.10.8.11` | 25565 |
| Flask web interface | `10.10.8.11` | 9001 |
| Status check target | `10.10.8.11` | 25565 |

## Passwords

| Variable | Default Fallback | Used By |
|----------|-----------------|---------|
| `MC_PASS` / `RCON_PASSWORD` | (none for RCON, fallback in main.py) | All RCON clients |

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
