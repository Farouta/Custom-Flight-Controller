import json


CONFIG_FILE = "/config.json"


# Loaded once. Every module that imports settings shares this same dict.
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)


def save():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
