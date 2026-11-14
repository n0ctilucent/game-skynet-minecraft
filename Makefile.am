VENV ?= @VENV_DIR@
PYTHON = $(VENV)/bin/python3
HUB01_NODE = skynet
HUB06_NODE = edge-t
NODE901_NODE ?= node901

PYTHONPATH_ENV = PYTHONPATH=.:./src:./src/skynet:./src/schematics:./src/schematics/builders:./src/rail:./src/vision:./src/utils

.PHONY: python test remote-audit backup clean lint stargate edge-t \
        deploy-containment deploy-transit check-rail node901-status \
        node901-synthesis regenerate-greebles server-tps

# Project: game-skynet-minecraft (bitsmasher.net)
# Environment: Paper 1.21.1 / build 26.2
# Infrastructure: The Bit-Stream Flux-Rail (BSFR) & AI Containment Zone

lint: python
	@echo "==> Formatting BSFR Python Modules..."
	$(VENV)/bin/isort .
	$(VENV)/bin/black .

python:
	@echo "==> Synchronizing Skynet Python Environment..."
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/python3 -m pip install -r requirements.txt pytest pytest-asyncio

stargate: python
	@echo "==> Deploying Stargate MCP Services..."
	$(PYTHON) -m pip install -r src/stargate/requirements-stargate.txt

edge-t: python
	@echo "==> Deploying Edge-T Vision Services..."
	$(PYTHON) -m pip install -r src/edge-t/requirements-edge-t.txt

test:
	@echo "==> Initiating BSFR Distributed Test Suite..."
	$(PYTHONPATH_ENV) $(PYTHON) -m pytest test/test_schematic_boundary_safety.py \
		test/test_schematic_metadata_integrity.py \
		test/test_builders.py \
		test/test_rail_logic.py \
		test/test_rcon_bridge.py

	@echo "==> Auditing Hub 00 (Inference Nexus) NPU & Thermal State..."
	ssh $(HUB01_NODE) "hailortcli fw-control identify && vcgencmd measure_temp" 2>/dev/null || echo "Hub 00 SSH unreachable (skipping live probe)"

remote-audit:
	@echo "==> Auditing Hub 00 Logic Logs & Hub 06 Vision Daemon..."
	ssh $(HUB01_NODE) "tail -n 50 /home/minecraft/logs/skynet_daemon.log" 2>/dev/null || echo "Hub 00 offline"
	ssh mendel@$(HUB06_NODE) "systemctl status edge-t-daemon.service --no-pager" 2>/dev/null || echo "Hub 06 offline"

node901-status:
	@echo "==> Querying Node901 NVIDIA Jetson Status..."
	ssh $(NODE901_NODE) "uptime && tegrastats --interval 1000 | head -n 2 2>/dev/null || nvidia-smi 2>/dev/null || true"

node901-synthesis:
	@echo "==> Triggering Remote NVIDIA Jetson Architectural Synthesis..."
	ssh $(NODE901_NODE) "python3 -c 'import mcschematic, numpy; print(\"Node901 Jetson Synthesis Stack: OK\")'"

deploy-containment:
	@echo "==> Executing Throttled RCON Batch Placer for AI Containment Area..."
	$(PYTHONPATH_ENV) $(PYTHON) src/schematics/batch_containment_deploy.py

deploy-transit:
	@echo "==> Deploying Grand Orbital Transit Loop Viaduct..."
	$(PYTHONPATH_ENV) $(PYTHON) src/rail/containment_transit_loop.py --deploy

check-rail:
	@echo "==> Checking Orbital Transit Loop Collision-Free Routing..."
	$(PYTHONPATH_ENV) $(PYTHON) src/rail/containment_transit_loop.py --dry-run

regenerate-greebles:
	@echo "==> Regenerating Procedural Schematics with Froglights & Signage..."
	$(PYTHONPATH_ENV) $(PYTHON) src/schematics/regenerate_greebled_schematics.py

server-tps:
	@echo "==> Querying Paper Minecraft TPS..."
	/home/minecraft/bin/mcrcon -H 10.10.8.60 -P 25575 -p dinosaurExTraVaGanZa1969 "tps"

backup:
	@echo "==> Synchronizing BSFR Technical Ledger to GitHub..."
	./bin/backup_to_git.sh

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
