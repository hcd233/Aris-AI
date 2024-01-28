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

JWT_TOKEN_SECRET = os.environ.get("JWT_TOKEN_SECRET")
JWT_TOKEN_EXPIRE_TIME = int(os.environ.get("JWT_TOKEN_EXPIRE_TIME", 3600))
JWT_TOKEN_ALGORITHM = os.environ.get("JWT_TOKEN_ALGORITHM", "HS256")

API_KEY_EXPIRE_TIME = eval(os.environ.get("API_KEY_EXPIRE_TIME", "3600 * 24 * 30"))
