# agent/config.py
"""
Configuration utilities for agent package.

Functions:
    load: Loads configuration from arhouse.json.
    save: Saves configuration to arhouse.json.
    get_house_id: Retrieves the house_id from configuration.
    get_secret_key: Retrieves the secret_key from configuration.
"""
import os, json

CONF_PATH = os.path.join(os.path.dirname(__file__), "arhouse.json")

def load():
    """
    Loads the agent configuration from arhouse.json.

    Returns:
        dict: Configuration dictionary, or empty dict if file does not exist.
    """
    if not os.path.exists(CONF_PATH):
        return {}
    with open(CONF_PATH) as f:
        return json.load(f)

def save(cfg):
    """
    Saves the given configuration dictionary to arhouse.json.

    Args:
        cfg (dict): Configuration dictionary to save.

    Returns:
        None
    """
    os.makedirs(os.path.dirname(CONF_PATH), exist_ok=True)
    with open(CONF_PATH, "w") as f:
        json.dump(cfg, f)

def get_house_id():
    """
    Retrieves the house_id from the configuration.

    Returns:
        str: The house_id value.
    Raises:
        KeyError: If 'house_id' is missing in configuration.
    """
    config = load()
    if 'house_id' not in config:
        raise KeyError("Missing 'house_id' in configuration")
    return config['house_id']

def get_secret_key():
    """
    Retrieves the secret_key from the configuration.

    Returns:
        str: The secret_key value.
    Raises:
        KeyError: If 'secret_key' is missing in configuration.
    """
    config = load()
    if 'secret_key' not in config:
        raise KeyError("Missing 'secret_key' in configuration")
    return config['secret_key']