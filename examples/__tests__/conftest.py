import pytest
from database import Base, engine
from evc import ExampleViewerContext


@pytest.fixture
def vc() -> ExampleViewerContext:
    return ExampleViewerContext()


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
