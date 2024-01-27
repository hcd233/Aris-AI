import os

DEBUG_MODE = os.environ.get("DEBUG_MODE", "0") == "1"

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_ROOT = os.environ.get("LOG_ROOT", "./log")

API_PORT = int(os.environ.get("API_PORT", "8000"))