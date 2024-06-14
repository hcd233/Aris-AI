import uvicorn

from src.api import create_app
from src.config import API_HOST, API_PORT


def main() -> None:
    app = create_app()
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="critical",
    )


if __name__ == "__main__":
    main()
