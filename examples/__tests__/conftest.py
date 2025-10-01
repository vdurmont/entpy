import pytest

from examples.database import get_session, init_db
from framework.viewer_context import ViewerContext


@pytest.fixture
async def db_session():
    await init_db()
    return get_session()


@pytest.fixture
def vc():
    return ViewerContext()
