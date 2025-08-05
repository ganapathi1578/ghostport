#agent/tunnel_agent.py
"""
Tunnel Agent Script

This script connects to a central WebSocket server and proxies incoming HTTP requests
to a local API server. It handles media streaming support, authentication, error handling,
and header injection for routing based on a unique `house_id`.

Used in edge deployments where multiple local instances are exposed via a central server.

Author: YourName
"""

import asyncio
import base64
import hashlib
import json
import traceback
import aiohttp
import websockets
import socket
import os
from config import load  # Loads `house_id` and `secret_key` from local config

# URL of the central WebSocket server (must be reachable by this agent)
CENTRAL_WS = "ws://10.23.8.207:5090/ws/tunnel/"

def get_local_api() -> str:
    """
    Returns the local API base URL using internal networking (e.g., Docker).

    Returns:
        str: Local API base URL (usually nginx or reverse proxy).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Trick to get local IP address
    ip = s.getsockname()[0]
    s.close()
    return f"http://nginx_server:80"

# Local API base URL
LOCAL_API = get_local_api()
print(f"🌐 Local API base: {LOCAL_API}")

async def handle_request(frame: dict, ws: websockets.WebSocketClientProtocol, house_id: str) -> None:
    """
    Handles a single HTTP request forwarded from the central server,
    proxies it to the local API, and sends back the response.

    Args:
        frame (dict): The HTTP request frame from the central server.
        ws (websockets.WebSocketClientProtocol): Active WebSocket connection.
        house_id (str): Unique identifier for the house/site (used in routing).
    """
    if frame.get("action") != "proxy_request":
        return

    req_id  = frame["id"]
    method  = frame["method"]
    path    = frame["path"]

    # Inject per-request header for script name-based routing
    headers = frame.get("headers", {}).copy()
    headers["X-Script-Name"] = f"/var/homes/{house_id}"

    body = frame.get("body", "")
    url = f"{LOCAL_API}/{path.lstrip('/')}"

    # Check if the request is for media (for CORS handling)
    is_media = path.endswith(('.m3u8', '.ts', '.mp4', '.webm'))

    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.request(method, url, headers=headers, data=body) as resp:
                raw_body = await resp.read()
                content_type = resp.headers.get("Content-Type", "")
                is_text = "text" in content_type or "json" in content_type

                if is_media:
                    print(f"🎬 Media request → {method} {path} [{resp.status}]")

                # Log error responses (non-media only)
                if resp.status >= 400 and not is_media:
                    print(f"⚠️ Local error {resp.status} → {url}")
                    snippet = raw_body[:200].decode('utf-8', 'ignore')
                    print("⚠️ Body snippet:", snippet)

                # Prepare body based on content type
                if is_text:
                    out_body = raw_body.decode('utf-8', 'ignore')
                    is_base64 = False
                else:
                    out_body = base64.b64encode(raw_body).decode('ascii')
                    is_base64 = True

                # Prepare response headers
                resp_headers = dict(resp.headers)
                if is_media:
                    resp_headers["Access-Control-Allow-Origin"] = "*"
                    resp_headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                    resp_headers["Access-Control-Allow-Headers"] = "*"

                # Final response payload to central server
                out = {
                    "action":    "http_response",
                    "id":        req_id,
                    "status":    resp.status,
                    "headers":   resp_headers,
                    "body":      out_body,
                    "is_base64": is_base64
                }

    except Exception:
        print("🚨 Exception in handle_request:")
        traceback.print_exc()
        out = {
            "action":    "http_response",
            "id":        req_id,
            "status":    502,
            "headers":   {"Content-Type": "application/json"},
            "body":      json.dumps({"error": "proxy agent error"}),
            "is_base64": False
        }

    # Send the response frame back over WebSocket
    await ws.send(json.dumps(out))


async def run() -> None:
    """
    Main loop: Connects to the central WebSocket, authenticates,
    listens for incoming HTTP request frames, and proxies them locally.
    """
    cfg = load()
    if not cfg.get("house_id"):
        print("❌ Please run `agent/register.py` first to register.")
        return

    hid, sk = cfg["house_id"], cfg["secret_key"]
    auth_hash = hashlib.sha256((hid + sk).encode()).hexdigest()

    while True:
        try:
            async with websockets.connect(CENTRAL_WS) as ws:
                # Send authentication frame
                await ws.send(json.dumps({
                    "action":    "authenticate",
                    "house_id":  hid,
                    "auth_hash": auth_hash
                }))
                print("🔌 Tunnel connected as", hid)

                # Set environment variable for Django routing
                os.environ["DJANGO_SCRIPT_NAME"] = f"/var/homes/{hid}"
                print(f"🌐 Set DJANGO_SCRIPT_NAME = /var/homes/{hid}")

                # Main loop to receive and process messages
                async for msg in ws:
                    print("📥 Received from central:", msg)
                    frame = json.loads(msg)

                    # Flatten nested frame if wrapped in 'type: forward.http'
                    if "type" in frame and frame["type"] == "forward.http" and "frame" in frame:
                        frame = frame["frame"]

                    await handle_request(frame, ws, hid)

        except Exception as exc:
            print("❗ Tunnel error:", exc, "→ retrying in 5s…")
            await asyncio.sleep(5)

# Entrypoint
if __name__ == "__main__":
    asyncio.run(run())
