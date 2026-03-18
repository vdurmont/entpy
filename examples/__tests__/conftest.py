import pytest
from database import Base, engine
from evc import ExampleViewerContext
import generated.all_models  # noqa: F401
from entpy.framework.database import db


@pytest.fixture
def vc() -> ExampleViewerContext:
    return ExampleViewerContext()


@pytest.fixture(autouse=True)
async def setup_database():
    await db.session.close()
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
