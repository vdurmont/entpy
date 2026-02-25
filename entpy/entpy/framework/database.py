import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy import event, func
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.scoping import async_scoped_session
from sqlalchemy.orm import Session

from entpy.framework.descriptor import Descriptor

if TYPE_CHECKING:
    from asyncpg import Connection

JSONScalar = str | int | float | bool | None

locks: dict[tuple[type, str, Any], asyncio.Lock] = defaultdict(asyncio.Lock)

log = logging.getLogger(__name__)


class Database:
    _session: async_scoped_session | AsyncSession | None = None
    events: "DatabaseEvents"

    def init_entpy(
        self, engine: AsyncEngine, session: async_scoped_session | AsyncSession
    ) -> None:
        self._session = session
        if engine.dialect.name == "postgresql":
            self.events = PostgresEvents(engine)
        else:
            self.events = InProcessEvents(engine)

    @property
    def session(self) -> async_scoped_session | AsyncSession:
        if self._session is None:
            raise RuntimeError("EntPy not initialized, please call init_entpy() first")
        return self._session


db = Database()


@asynccontextmanager
async def emulate_for_update(
    model: type,
    field: str,
    value: Any,
    for_update: bool = False,
) -> AsyncGenerator[None]:
    if for_update and db.session.bind.engine.name == "sqlite":
        db.session.info.setdefault("for_update", set())
        lock = locks[(model, field, value)]
        if lock not in db.session.info["for_update"]:
            log.debug(
                "Acquiring lock %s for %s.%s = %s", lock, model.__name__, field, value
            )
            await lock.acquire()
            db.session.info["for_update"].add(lock)

    yield


def release_locks(session: Session) -> None:
    if "for_update" in session.info:
        log.debug("Releasing locks %s", session.info["for_update"])
        for lock in session.info["for_update"]:
            lock.release()
        del session.info["for_update"]


event.listen(Session, "after_commit", release_locks)
event.listen(Session, "after_rollback", release_locks)


class DatabaseEvents(ABC):
    queues: dict[
        str, dict[tuple[str, Any], list[asyncio.Queue[dict[str, JSONScalar]]]]
    ] = defaultdict(lambda: defaultdict(list))

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def listen(self, table: str) -> None:  # noqa: B027
        pass

    @abstractmethod
    async def notify(self, table: str, payload: str) -> None:
        pass

    async def notify_all(self, events: list[tuple[str, dict[str, Any]]]) -> None:
        for table, payload in events:
            await self.notify(table, json.dumps(payload, default=str))

    async def subscribe(
        self, descriptor: type[Descriptor], field: str, value: JSONScalar
    ) -> asyncio.Queue[dict[str, JSONScalar]]:
        table = descriptor.get_table_name()
        if table not in self.queues:
            await self.listen(table)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(32)
        self.queues[table][(field, value)].append(queue)
        return queue

    def unsubscribe(
        self,
        descriptor: type[Descriptor],
        field: str,
        value: JSONScalar,
        queue: asyncio.Queue[dict[str, JSONScalar]],
    ) -> None:
        self.queues[descriptor.get_table_name()][(field, value)].remove(queue)

    async def dispatch(self, table: str, payload: str) -> None:
        fields = json.loads(payload)
        for field, value in fields.items():
            if (field, value) in self.queues[table]:
                for queue in self.queues[table][(field, value)]:
                    try:
                        queue.put_nowait(fields)
                    except asyncio.QueueFull:
                        log.warning(
                            "Failed to dispatch event for %s: %s=%s",
                            table,
                            field,
                            value,
                        )


class PostgresEvents(DatabaseEvents):
    conn: AsyncConnection | None = None

    async def connect(self) -> AsyncConnection:
        conn = await self.engine.connect()
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        raw_conn = await conn.get_raw_connection()
        raw_conn.detach()
        return conn

    async def listen(self, table: str) -> None:
        if self.conn is None:
            self.conn = await self.connect()
        conn = await self.conn.get_raw_connection()
        await conn._connection.add_listener(table, self.callback)

    async def callback(
        self, _conn: "Connection", _pid: int, channel: str, payload: str
    ) -> None:
        await self.dispatch(channel, payload)

    async def notify(self, table: str, payload: str) -> None:
        if self.conn is None:
            self.conn = await self.connect()
        await self.conn.execute(func.pg_notify(table, payload))


class InProcessEvents(DatabaseEvents):
    async def notify(self, table: str, payload: str) -> None:
        await self.dispatch(table, payload)


@event.listens_for(Session, "after_commit")
def notify_events(session: Session) -> None:
    asyncio.create_task(db.events.notify_all(session.info.pop("events", [])))


@asynccontextmanager
async def event_subscription(
    descriptor: type[Descriptor], field: str, value: JSONScalar
) -> AsyncGenerator[asyncio.Queue[dict[str, Any]], None]:
    queue = await db.events.subscribe(descriptor, field, value)
    try:
        yield queue
    finally:
        db.events.unsubscribe(descriptor, field, value, queue)
