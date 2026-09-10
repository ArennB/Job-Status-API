"""Database settings supplied by the process environment."""

import os

from sqlalchemy.engine import URL


def get_database_url() -> str | URL:
    """Allow a full URL override, or build a URL without escaping credentials."""
    if url := os.getenv("DATABASE_URL"):
        return url

    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(
            "Set DATABASE_URL or the required environment variables: "
            + ", ".join(missing)
        )
    return URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
    )
