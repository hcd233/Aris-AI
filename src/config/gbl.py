from .env import API_HOST, API_PORT

SUPPORT_URL_TYPE = ["arxiv", "git", "render", "recursive"]

SUPPORT_UPLOAD_FILE = [
    "txt",
    "pdf",
    "ipynb",
    "cpp",
    "h",
    "hpp",
    "go",
    "java",
    "kt",
    "js",
    "ts",
    "php",
    "proto",
    "py",
    "rst",
    "rb",
    "rs",
    "scala",
    "swift",
    "md",
    "tex",
    "html",
    "htm",
    "sol",
    "cs",
    "cbl",
    "cob",
]

OAUTH2_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
OAUTH2_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
OAUTH2_GITHUB_USER_API = "https://api.github.com/user"

OAUTH2_GITHUB_REDIRECT_URL = f"http://{API_HOST}:{API_PORT}/v1/oauth2/github/callback"
