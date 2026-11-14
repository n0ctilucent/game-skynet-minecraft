# Database — MariaDB Neural-Data Vault (Hub 07)

MariaDB instance on **blowfish** (`10.10.12.15`) serving as the centralized data store for the Bitsmasher Void-Tech infrastructure.

---

## Host Overview

| Field | Value |
|-------|-------|
| Hostname | blowfish |
| OS | OpenBSD 7.8 |
| Internal IP | `10.10.12.15` |
| Role | Neural-Data Vault — primary SQL storage for Skynet intelligence and map telemetry |

---

## Database Schemas

### `skynet_vault`

Schema for build telemetry, architectural records, and spatial density data consumed by the NPUSpatialEngine.

**`build_history` table**:

```sql
CREATE TABLE build_history (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    x             INT NOT NULL,
    y             INT NOT NULL,
    z             INT NOT NULL,
    width         INT DEFAULT 10,
    depth         INT DEFAULT 10,
    schematic_name VARCHAR(255),
    ai_hardware   VARCHAR(50),
    timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (x, z),
    INDEX (ai_hardware)
);
```

| Column | Purpose |
|--------|---------|
| `name` | Build record identifier (`{hardware}_{schematic}_{x}_{z}`) |
| `x/y/z` | World placement coordinates |
| `width/depth` | Structure bounding-box dimensions |
| `schematic_name` | Source `.schem` file (e.g., `void_uplink_v2.schem`) |
| `ai_hardware` | Inference hardware tag: `hailo_8l`, `edge_tpu`, or `legacy_import` |
| `timestamp` | Auto-set insertion time |

### `bluemap`

Persistent storage backend for BlueMap tile data (replacing file-based storage). User `'bluemap'@'10.10.8.60'` with full access. See `setup.sql`.

### `luckperms`

Backend data store for LuckPerms plugin permissions sync. User `'luckperms'@'10.10.8.60'`.

---

## VaultManager API (`vault_manager.py`)

Python orchestrator for SQL operations on the `skynet_vault` database. Connects via `mariadb` Python connector to `blowfish:3306`.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `()` | Reads `DB_USER` / `DB_PASS` env vars; defaults to `skynet_admin` / `fakey-fake` for dev/test |
| `_get_connection` | `() -> Connection \| None` | Attempts mariadb.connect; prints error and returns `None` on failure |
| `log_build` | `(x, y, z, width, depth, schematic, hardware) -> None` | INSERTs a build telemetry record into `build_history` |
| `fetch_history` | `() -> list[dict]` | SELECTs all rows from `build_history`; returns dict-list (column names as keys) |
| `migrate_json` | `(json_path: str) -> None` | Parses a JSON array of records; calls `log_build` for each entry |

### Usage

```python
from src.database.vault_manager import VaultManager

vault = VaultManager()

# Log a new placement
vault.log_build(
    x=-1212, y=76, z=-670,
    width=15, depth=15,
    schematic="mono_eye_sensor_v2.schem",
    hardware="edge_tpu"
)

# Migrate legacy JSON records
vault.migrate_json("/path/to/cleaned_build_history.json")

# Query density data for spatial analysis
rows = vault.fetch_history()
```

---

## Sync Script (`sync_vault.py`)

Orchestration script that migrates legacy `history.json` to MariaDB and commits sample telemetry for Hub 06 (Edge TPU).

```sh
python sync_vault.py
# STATUS: Migrating legacy architectural records from history.json...
# STATUS: Committing architectural telemetry for Hub 06...
# SUCCESS: Stargate vault synchronization complete.
```

---

## Data Streams

| Source | Target DB | Notes |
|--------|-----------|-------|
| Skynet Inference Nexus (Hub 01) → AI logs | `skynet_vault.build_history` | Deep-storage cold cell for encrypted AI mutation logs |
| Mono-Eye Sensor (Hub 06, Edge TPU) → Sense/Net | `skynet_vault.build_history` | Vision node surveillance + environmental analysis |
| BlueMap plugin (chonk, `10.10.8.60`) → tiles | `bluemap.*` | SQL backend for Overworld/Nether map rendering |
| CoreProtect plugin → block changes | DB-managed per-plugin schema | Every block change in AI Testing Field logged |

---

## Security

- **Access control**: Restricted to Stargate MCP server + hardware nodes on `10.10.x.x` subnet
- **Password policy**: Strong unique credentials for system panel and database users
- **Host hardening**: OpenBSD 7.8 SELinux-style architecture mitigates backend exposure

---

## Backup & Sync

Daily backups via `bin/backup_to_git.sh` on the chonk host:

```bash
mysqldump -h 10.10.12.15 -u skynet_user skynet_vault > data/sql_vault_backup.sql
git add data/sql_vault_backup.sql
git commit -m "Vault Sync: Updated SQL build history from blowfish"
```

GitHub (`game-server-minecraft` repo) serves as the technical ledger — ultimate source of truth for both world files and synchronized SQL build history.

---

## Setup Notes (blowfish host)

```sh
# Install MariaDB on OpenBSD
doas pkg_add mariadb-server
doas rcctl enable mysqld
doas mariadb-install-db
doas rcctl start mysqld
doas mariadb-secure-installation
```

Initial DB setup: `setup.sql` — creates `bluemap` and `luckperms` databases with user accounts for `10.10.8.60`.

---

*Created for theDevilsVoice | Last Updated: 2026-11-06*
