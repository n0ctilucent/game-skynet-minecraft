# Modular builder functions for different structure types
from .bank import build_bank
from .bridge import build_bridge
from .castle import build_castle
from .cyberdyne import build_cyberdyne
from .decoration import build_decoration
from .house import build_house
from .primitives import *
from .quantum_foundry import build_quantum_foundry
from .signal_siphon import build_signal_siphon
from .station2 import build as build_station
from .t2bm_expander import build_t2bm
from .terrain import build_terrain
from .tower import build_tower
from .urban_greebler import (
    build_promenade,
    build_lamp_post,
    build_guardrail,
    build_market_stall,
    build_gathering_nook,
    build_pier,
    build_chimney_vent,
    build_hvac_and_solar,
    build_window_flower_box,
    build_snow_flora,
    DISTRICT_PALETTE
)
from .wall import build_wall

BUILDERS = {
    "house": build_house,
    "wall": build_wall,
    "tower": build_tower,
    "bridge": build_bridge,
    "terrain": build_terrain,
    "decoration": build_decoration,
    "castle": build_castle,
    "bank": build_bank,
    "cyberdyne": build_cyberdyne,
    "station": build_station,
    "t2bm": build_t2bm,
    "signal_siphon": build_signal_siphon,
    "quantum_foundry": build_quantum_foundry,
    "urban_greebler": urban_greebler,
}
