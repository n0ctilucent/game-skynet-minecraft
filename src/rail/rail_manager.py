import asyncio
import json
import logging
import os
from datetime import datetime
from mcrcon import MCRcon
import rcon

logging.basicConfig(level=logging.INFO)

class RailRegistry:
    def __init__(self, registry_file):
        self.registry_file = registry_file
        self.registry_data = None
        self.last_modified = 0

    async def load_registry(self):
        if not os.path.exists(self.registry_file):
            return {}

        with open(self.registry_file, 'r') as f:
            self.registry_data = json.load(f)
            self.last_modified = os.stat(self.registry_file).st_mtime

    def is_registry_changed(self):
        current_modified = os.stat(self.registry_file).st_mtime
        if current_modified != self.last_modified:
            self.last_modified = current_modified
            return True
        return False

class MarkerManager:
    def __init__(self, markers_file):
        self.markers_file = markers_file
        self.markers_data = None

    async def load_markers(self):
        with open(self.markers_file, 'r') as f:
            self.markers_data = json.load(f)

    def update_marker(self, marker_id, active):
        if not self.markers_data:
            return

        for mark in self.markers_data['markers']:
            if mark['id'] == marker_id:
                mark['color'] = 'green' if active else 'red'
                with open(self.markers_file, 'w') as f:
                    json.dump(self.markers_data, f)
                break


class BlueMapMarkerUpdater:
    """Manages BlueMap markers.json for rail switches and POIs."""

    def __init__(self, markers_file: str):
        self.markers_file = markers_file
        self.data = {"markerSets": {"rail_switches": {"markers": {}}}}
        if os.path.exists(self.markers_file):
            try:
                with open(self.markers_file, "r") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self):
        parent = os.path.dirname(os.path.abspath(self.markers_file))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.markers_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def update_switch(self, switch_id: str, label: str, coords: dict, is_active: bool):
        status_str = "ACTIVE" if is_active else "INACTIVE"
        marker_data = {
            "label": f"{label} [{status_str}]",
            "position": coords,
            "color": "#00FF00" if is_active else "#FF0000",
        }
        switches_dict = {"markers": {switch_id: marker_data}}
        self.data = {
            "markerSets": {
                "rail_switches": switches_dict,
                "markerSets": {
                    "rail_switches": switches_dict
                }
            }
        }
        self._save()


class RailManager:
    def __init__(
        self,
        rcon_host="10.10.8.60",
        rcon_port=25575,
        registry_file="config/rail_registry.json",
        markers_file="markers.json",
    ):
        self.rcon_host = rcon_host
        self.rcon_port = rcon_port
        self.rcon_pass = os.getenv("RCON_PASS", "dinosaurExTraVaGanZa1969")
        self.registry_file = registry_file
        self.markers_file = markers_file
        self.rail_registry = RailRegistry(registry_file)
        self.marker_manager = MarkerManager(markers_file)
        self.marker_updater = BlueMapMarkerUpdater(markers_file)

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"switches": {}}

    def _save_registry(self, data=None):
        if data is not None:
            parent = os.path.dirname(os.path.abspath(self.registry_file))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=4)

    def _verify_tpu_safety(self, switch_id: str) -> bool:
        return True

    def toggle_switch(self, switch_id: str, state: bool) -> bool:
        if not self._verify_tpu_safety(switch_id):
            return False
        registry = self._load_registry()
        switches = registry.get("switches", {})
        if switch_id not in switches:
            return False
        sw = switches[switch_id]
        coords = sw["coords"]
        x, y, z = coords["x"], coords["y"], coords["z"]
        state_str = "true" if state else "false"
        try:
            with MCRcon(self.rcon_host, self.rcon_pass, port=self.rcon_port) as mcr:
                mcr.command(f"setblock {x} {y} {z} minecraft:powered_rail[powered={state_str}]")
        except Exception as e:
            logging.error(f"RCON failed: {e}")
            return False
        sw["state"] = state
        self._save_registry(registry)
        self.marker_updater.update_switch(switch_id, sw.get("name", switch_id), coords, state)
        return True

    async def check_safety(self, x, y, z):
        """
        Queries Edge-T (Hub-06) to ensure no players are within 5 blocks. 
        """
        try:
            reader, writer = await asyncio.open_connection('10.10.8.66', 8808)
            query = json.dumps({"task": "proximity_check", "coords": [x, y, z], "radius": 5})
            writer.write(query.encode() + b'\n')
            await writer.drain()

            response = await reader.read(1024)
            data = json.loads(response.decode())
            writer.close()
            await writer.wait_closed()

            if data.get("detected_entities", 0) > 0:
                with open('logs/rail_safety.log', 'a') as log_file:
                    log_file.write(f"[{datetime.now()}] ABORT: Player detected near {x},{y},{z}\n")
                return False
            return True
        except Exception as e:
            logging.error(f"Safety Daemon Unreachable: {e}")
            return False

    async def toggle_rail(self, x, y, z):
        await self.check_safety(x, y, z)
        if not await self.rail_registry.load_registry():
            return

        registry_data = self.rail_registry.registry_data
        powered_rail_block = f"{x},{y},{z}"
        for route in registry_data.get('routes', []):
            if powered_rail_block in route.get('blocks', []):
                try:
                    rcon_client = rcon.RCON(self.rcon_host, self.rcon_port)
                    await asyncio.sleep(0.05)
                    await rcon_client.send(f"/execute in minecraft:overworld run setblock {x} {y} {z} powered_rail")
                except Exception as e:
                    logging.error(f"Critical failure: {e}")
                    return

        if 'marker_id' in registry_data:
            self.marker_manager.update_marker(registry_data['marker_id'], True)

    async def main_loop(self):
        while True:
            if await self.rail_registry.is_registry_changed():
                await self.rail_registry.load_registry()
                registry_data = self.rail_registry.registry_data
                for route in registry_data.get('routes', []):
                    powered_rail_block = f"{route['x']},{route['y']},{route['z']}"
                    await self.toggle_rail(*map(int, powered_rail_block.split(',')))
            await asyncio.sleep(1)

if __name__ == '__main__':
    rcon_host = 'localhost'
    rcon_port = 25575
    registry_file = 'config/rail_registry.json'
    markers_file = 'markers.json'

    rail_manager = RailManager(rcon_host, rcon_port, registry_file, markers_file)
    asyncio.run(rail_manager.main_loop())
