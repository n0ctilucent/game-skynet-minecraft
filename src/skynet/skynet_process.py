"""
Skynet Process: Spatial logic and RCON dispatch routines.
Reconstructed from legacy Phase 2 NPU orchestration protocols.
"""

import logging
import os
import random
import sys
from pathlib import Path

# Ensure src root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config_utils import Config, SkynetRCON, setup_logging

logger = setup_logging("skynet_process")
_rcon = SkynetRCON()

NODE_PROMPTS = {
    "node_hailo": [
        "void_rail_v2.json",
        "crafter_hub_v2.json",
        "void_uplink_v2.json",
    ],
    "node_edgetpu": [
        "growth_chamber_v2.json",
        "sentry_prism_v2.json",
    ],
    "node_vision": [
        "crafter_hub_master_control_v5.json",
    ],
    "node_stargate": [
        "void_uplink_v2.json",
    ],
}


def is_within_bounds(x, z, width=5, depth=5):
    bounds = Config.FIELD_BOUNDS
    return (bounds["min_x"] <= x and (x + width) <= bounds["max_x"]) and (
        bounds["min_z"] <= z and (z + depth) <= bounds["max_z"]
    )


def push_build_to_chonk(commands):
    """
    Sends a list of commands to the Minecraft server via RCON.
    Includes centralized logging for build deployment.
    """
    try:
        _rcon.send(commands)
        logger.info("✅ Deployed AI-generated structure logic to chonk.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to push build to chonk: {e}")
        return False


def get_hailo_structure_logic(sector="default zone", metadata=None):
    """
    Simulates AI structure generation using the Hailo NPU.
    Returns a list of RCON commands.
    """
    bounds = Config.FIELD_BOUNDS
    tx = random.randint(bounds["min_x"], bounds["max_x"] - 6)
    tz = random.randint(bounds["min_z"], bounds["max_z"] - 6)
    ty = bounds["y_base"]
    build_name = f"Void-Tech {random.randint(100, 999)}"

    cmds = [
        f"fill {tx} {ty} {tz} {tx+5} {ty+10} {tz+5} minecraft:polished_tuff",
        f"fill {tx+1} {ty+1} {tz+1} {tx+4} {ty+9} {tz+4} minecraft:air",
        f"say [Skynet] Void-Tech '{build_name}' deployed at {tx} {ty} {tz} in {sector}.",
    ]
    return cmds


def get_node_logic(node="node_hailo", sector="Shroomville", metadata=None):
    """
    Generates node-specific spatial deployment commands based on cluster prompts.
    """
    prompts = NODE_PROMPTS.get(node, ["void_rail_v2.json"])
    selected_prompt = random.choice(prompts)
    logger.info(f"🧠 Selecting spatial inference logic for {node} using prompt: {selected_prompt}")

    cmds = [
        f"say §b[Skynet]§f Node {node} deploying {selected_prompt} to {sector}",
        f"say §d[Inference]§f Spatial Sync complete for {sector}",
    ]
    return cmds
