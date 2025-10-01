import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from examples.database import get_session, init_db
from framework.viewer_context import ViewerContext


@pytest.fixture
async def db_session() -> AsyncSession:
    await init_db()
    return get_session()


@pytest.fixture
def vc() -> ViewerContext:
    return ViewerContext()
