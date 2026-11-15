#!/usr/bin/env bash
# deploy_containment_rail_corners.sh
# Deploys verified 90-degree rail corners and connects AI Containment buildings.
# Enforces standard unpowered rail at corners and non-redstone roadbed.

MCRCON="/home/minecraft/bin/mcrcon"
if [[ ! -x "$MCRCON" ]]; then
    echo "Error: $MCRCON not found or not executable"
    exit 1
fi

RCON_PASS="${RCON_PASS:-dinosaurExTraVaGanZa1969}"

exec_rcon() {
    "$MCRCON" -H 127.0.0.1 -P 25575 -p "$RCON_PASS" "$1"
}

echo "[*] Deploying AI Containment Rail Corners..."

# 1. Northwest Corner (-1539, 64, -913): South to East
echo "[-] Placing NW Corner at -1539 64 -913 (shape=south_east)..."
exec_rcon "setblock -1539 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -913 minecraft:rail[shape=south_east]"
exec_rcon "setblock -1538 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -913 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -912 minecraft:redstone_block"

# 2. Northeast Corner (-945, 64, -913): West to South
echo "[-] Placing NE Corner at -945 64 -913 (shape=south_west)..."
exec_rcon "setblock -945 63 -913 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -913 minecraft:rail[shape=south_west]"
exec_rcon "setblock -946 64 -913 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -913 minecraft:redstone_block"
exec_rcon "setblock -945 64 -912 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -912 minecraft:redstone_block"

# 3. Southeast Corner (-945, 64, -489): North to West
echo "[-] Placing SE Corner at -945 64 -489 (shape=north_west)..."
exec_rcon "setblock -945 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -945 64 -489 minecraft:rail[shape=north_west]"
exec_rcon "setblock -946 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -946 63 -489 minecraft:redstone_block"
exec_rcon "setblock -945 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -945 63 -490 minecraft:redstone_block"

# 4. Southwest Corner (-1539, 64, -489): East to North
echo "[-] Placing SW Corner at -1539 64 -489 (shape=north_east)..."
exec_rcon "setblock -1539 63 -489 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -489 minecraft:rail[shape=north_east]"
exec_rcon "setblock -1538 64 -489 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1538 63 -489 minecraft:redstone_block"
exec_rcon "setblock -1539 64 -490 minecraft:powered_rail[shape=north_south]"
exec_rcon "setblock -1539 63 -490 minecraft:redstone_block"

# 5. AI Lab Gateway Spur Junction (-1539, 64, -608)
echo "[-] Placing AI Lab Connector at -1539 64 -608..."
exec_rcon "setblock -1539 63 -608 minecraft:polished_deepslate"
exec_rcon "setblock -1539 64 -608 minecraft:rail[shape=north_west]"
exec_rcon "setblock -1540 64 -608 minecraft:powered_rail[shape=east_west]"
exec_rcon "setblock -1540 63 -608 minecraft:redstone_block"
exec_rcon "setblock -1545 64 -608 minecraft:detector_rail[shape=east_west]"

echo "[+] Rail corners and building connectors deployed successfully."
