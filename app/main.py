"""Application-level entry point for the backend host."""

from app.host.bootstrapper import run


def main() -> None:
    """Start the configured backend host."""
    run()


if __name__ == "__main__":
    main()
