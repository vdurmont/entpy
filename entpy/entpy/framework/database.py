import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.scoping import async_scoped_session
from sqlalchemy.orm import Session

locks: dict[tuple[type, str, Any], asyncio.Lock] = defaultdict(asyncio.Lock)

log = logging.getLogger(__name__)


class Database:
    _session: async_scoped_session | AsyncSession | None = None

    def init_entpy(self, session: async_scoped_session | AsyncSession) -> None:
        self._session = session

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
