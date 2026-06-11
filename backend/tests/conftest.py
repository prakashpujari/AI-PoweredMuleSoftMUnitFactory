"""Shared test fixtures — DB mock so API tests don't require a live database."""
import pytest
from unittest.mock import AsyncMock


class _MockRow:
    """Mimics a SQLAlchemy Row for scalar aggregate queries."""

    def __init__(self, *values):
        self._values = values

    def __getitem__(self, idx):
        return self._values[idx] if idx < len(self._values) else None

    # Named attribute access (used by labeled columns)
    def __getattr__(self, name):
        return None


class _MockResult:
    """Mimics a SQLAlchemy async result object."""

    def scalars(self):
        return self

    def all(self):
        return []

    def one(self):
        return _MockRow(None, None, None, None, None)

    def __iter__(self):
        return iter([])


class _MockAsyncSession:
    """Thin mock of SQLAlchemy AsyncSession for route-level tests."""

    async def execute(self, *args, **kwargs):
        return _MockResult()

    async def scalar(self, *args, **kwargs):
        return None

    def add(self, obj):
        pass

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass


async def _mock_get_db():
    yield _MockAsyncSession()


@pytest.fixture(autouse=True)
def override_db():
    """Override the DB dependency for all API tests so no live DB is needed."""
    try:
        from app.main import app
        from app.database import get_db
        app.dependency_overrides[get_db] = _mock_get_db
        yield
        app.dependency_overrides.pop(get_db, None)
    except Exception:
        yield
