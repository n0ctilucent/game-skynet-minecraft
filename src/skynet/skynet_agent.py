import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure src root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skynet.skynet_process import get_hailo_structure_logic, get_node_logic
from utils.config_utils import setup_logging

logger = setup_logging("skynet_agent")


class SkynetAgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/infer":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode("utf-8")) if post_data else {}

            logger.info(f"🧠 Received inference request: {params}")

            # Identify which logic to run
            node_type = params.get("node", "node_hailo")
            sector = params.get("sector", "Shroomville")

            if node_type == "void_tech":
                commands = get_hailo_structure_logic(sector=sector)
            else:
                commands = get_node_logic(node=node_type, sector=sector)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"commands": commands}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.info(f"HTTP {format % args}")


def run_agent(port=5000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SkynetAgentHandler)
    logger.info(f"📡 Skynet Agent listening on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.info("📡 Skynet Agent shut down.")


if __name__ == "__main__":
    run_agent()
