import uvicorn

from internal.config import API_PORT


def main() -> None:
    # same as from internal.api import create_app
    uvicorn.run(
        "internal.api:create_app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
