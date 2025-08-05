#agent/register.py
"""
Registration utility for agent. Registers the agent with the central server and saves credentials.

Functions:
    main: Registers the agent if not already registered, saves credentials to config, and prints status.

Constants:
    HUB_URL: URL for agent registration API.
"""
import requests, json
from config import load, save
import os
import sys
from secrets import REGISTRATION_TOKEN

HUB_URL = "https://services.iittp.ac.in/var/tunnel/api/register_or_get_id/"

def register():
    """
    Registers the agent with the central server if not already registered.
    Loads/saves credentials to config file.

    Returns:
        None
    """
    cfg = load()
    if cfg.get("house_id"):
        print("\u2705 Already registered:", cfg)
        return

    #token = os.getenv("REGISTRATION_TOKEN")
    token = cfg.get("REGISTRATION_TOKEN")
    if not token:
        print("\u274c REGISTRATION_TOKEN environment variable is missing. Aborting.")
        sys.exit(1)

    resp = requests.post(HUB_URL, json={"token": token})
    if resp.status_code != 200:
        print("\u274c Registration failed:", resp.json())
        return

    data = resp.json()  # { house_id, secret_key }
    save(data)
    print("\u2705 Registered successfully! Saved:", data)

if __name__ == "__main__":
    if not os.path.exists("arhouse.json"):
        register()
    else:
        print("\u2705 Found existing token file: arhouse.json")
