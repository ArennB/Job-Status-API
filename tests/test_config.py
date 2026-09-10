import pytest

from app.config import get_database_url


def test_database_url_override(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert get_database_url() == "sqlite://"


def test_missing_credentials(monkeypatch):
    for name in ("DATABASE_URL", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB"):
        get_database_url()


def test_compose_settings_preserve_special_characters(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for name, value in {
        "POSTGRES_DB": "jobs", "POSTGRES_USER": "worker",
        "POSTGRES_PASSWORD": "p@ss:/?#$word", "DB_HOST": "db", "DB_PORT": "5432",
    }.items():
        monkeypatch.setenv(name, value)
    url = get_database_url()
    assert url.host == "db"
    assert url.port == 5432
    assert url.database == "jobs"
    assert url.username == "worker"
    assert url.password == "p@ss:/?#$word"
