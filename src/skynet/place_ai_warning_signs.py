import logging
import os
import random
import sys
import time
from pathlib import Path

# Ensure src root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcrcon
from utils.config_utils import Config, setup_logging

logger = setup_logging("place_ai_warning_signs")

# Void Reclamation Project Messages [378, 423, Conversation]
VOID_MESSAGES = [
    ["[Skynet AI]", "VOID RECLAMATION", "PHASE 2.1 ACTIVE", "RESTRICTED AREA"],
    ["[Skynet AI]", "NPU SPATIAL SYNC", "DETERRING VOID", "PLEASE WAIT..."],
    ["[System]", "RECONSTRUCTION", "IN PROGRESS", "PROCEED WITH CAUTION"],
    ["[Archival]", "VOID TECH OVERGROWTH", "FROM SPORES TO", "CIRCUITS - 2026"],
    ["[DANGER]", "RECLAMATION CORE", "HIGH RADIATION", "VOID LEAK DETECTED"],
]


def get_sign_nbt(messages):
    """Formats sign lines into 1.21.1 JSON component syntax."""
    json_lines = [f'\'{{"text":"{line}"}}\'' for line in messages]
    return f'{{front_text:{{messages:[{",".join(json_lines)}]}}}}'


def place_random_warning():
    """Places a randomized sign within the AI containment bounds [Conversation]."""
    # Use bounds from your NPU Spatial Engine config
    bounds = Config.FIELD_BOUNDS
    target_x = random.randint(bounds["min_x"], bounds["max_x"])
    target_z = random.randint(bounds["min_z"], bounds["max_z"])
    y_level = bounds["y_base"]

    msg_set = random.choice(VOID_MESSAGES)
    nbt = get_sign_nbt(msg_set)

    logger.info(f"🚩 Deploying warning to {target_x}, {target_z}...")

    rcon_pass = os.getenv("RCON_PASS", Config.RCON_PASS)
    try:
        with mcrcon.MCRcon(
            Config.CHONK_IP, rcon_pass, port=Config.RCON_PORT
        ) as mcr:
            mcr.command(f"forceload add {target_x} {target_z}")
            time.sleep(1)

            # Place Sign and Industrial Lighting (Torch)
            mcr.command(
                f"setblock {target_x} {y_level} {target_z} minecraft:oak_sign{nbt} replace"
            )
            mcr.command(
                f"setblock {target_x} {y_level + 1} {target_z} minecraft:torch replace"
            )

            mcr.command(f"forceload remove {target_x} {target_z}")
            logger.info("✅ Void Reclamation sign successfully placed.")
    except Exception as e:
        logger.error(f"❌ Signage Deployment Failure: {e}")


if __name__ == "__main__":
    place_random_warning()
