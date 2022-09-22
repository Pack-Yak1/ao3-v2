"""Module for loading config file for project"""
import json
import os


def load_config():
    # Load config file
    with open(
        os.path.join(os.getcwd(), "config", "default.json"),
        "r",
        encoding="utf-8",
    ) as js_fp:
        try:
            output = json.load(js_fp)
            return output
        except json.decoder.JSONDecodeError:
            return {}


config = load_config()
