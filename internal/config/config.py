import os

DEBUG_MODE = os.environ.get("DEBUG_MODE", "0") == "1"

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_ROOT = os.environ.get("LOG_ROOT", "./log")

API_PORT = int(os.environ.get("API_PORT", "8000"))

MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER")
