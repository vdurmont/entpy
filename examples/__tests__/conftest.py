import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session, init_db
from evc import ExampleViewerContext


@pytest.fixture
async def db_session() -> AsyncSession:
    await init_db()
    return get_session()


@pytest.fixture
def vc() -> ExampleViewerContext:
    return ExampleViewerContext()
