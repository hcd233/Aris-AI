import uvicorn

from internal.api import create_app
from internal.config import API_PORT


def main() -> None:
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="critical",
    )


if __name__ == "__main__":
    main()
