"""Shared test setup: every test gets its own throw-away database.

Without this, tests wrote into the real data/campusverse.db and left fake
memories behind in the application's real data.
"""
import pytest
import campusverse.db as db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test_campusverse.db")
    yield
