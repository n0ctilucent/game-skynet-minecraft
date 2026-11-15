import sys
import os
from pathlib import Path

# Link to schematics builders
builders_dir = str(Path(__file__).resolve().parent.parent / "schematics" / "builders")
if builders_dir not in sys.path:
    sys.path.insert(0, builders_dir)
import urban_greebler


class T2BM_Expander:
    """Edge-T TPU / Terrain adaptation and street-level decoration generator."""

    @staticmethod
    def generate(intent: str, coords: list, **kwargs) -> dict:
        print(f"[EDGE-T] Expanding intent: {intent} at {coords}")
        x = coords[0] if len(coords) > 0 else 0
        y = coords[1] if len(coords) > 1 else 63
        z = coords[2] if len(coords) > 2 else 0

        commands = []
        if intent == "promenade":
            target = kwargs.get("target", [x + 20, y, z])
            width = kwargs.get("width", 3)
            commands = urban_greebler.build_promenade(x, z, target[0], target[2], y=y, width=width)
        elif intent == "lamp_post":
            style = kwargs.get("style", "warm")
            commands = urban_greebler.build_lamp_post(x, y, z, style=style)
        elif intent == "guardrail":
            target = kwargs.get("target", [x + 10, y, z])
            commands = urban_greebler.build_guardrail(x, z, target[0], target[2], y=y)
        elif intent == "market_stall":
            facing = kwargs.get("facing", "south")
            theme = kwargs.get("theme", "red_white")
            commands = urban_greebler.build_market_stall(x, y, z, facing=facing, theme=theme)
        elif intent == "gathering_nook":
            commands = urban_greebler.build_gathering_nook(x, y, z)
        elif intent == "pier":
            length = kwargs.get("length", 6)
            width = kwargs.get("width", 3)
            commands = urban_greebler.build_pier(x, y, z, length=length, width=width)
        elif intent == "snow_flora":
            commands = urban_greebler.build_snow_flora(x, y, z)
        elif intent == "rooftop_mechanicals":
            commands = urban_greebler.build_hvac_and_solar(x, y, z)
        elif intent == "chimney":
            height = kwargs.get("height", 4)
            commands = urban_greebler.build_chimney_vent(x, y, z, height=height)
        else:
            print(f"[EDGE-T] Unknown intent: {intent}, fallback empty")

        return {
            "name": intent,
            "coords": coords,
            "commands": commands,
            "block_count": len(commands)
        }
