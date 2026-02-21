from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from config import settings

_pool: AsyncConnectionPool | None = None


async def init_connection_pool() -> None:
    global _pool
    if _pool is not None:
        return

    _pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        timeout=settings.db_pool_timeout,
        open=False,
    )
    await _pool.open(wait=True)


async def close_connection_pool() -> None:
    global _pool
    if _pool is None:
        return

    await _pool.close()
    _pool = None


@asynccontextmanager
async def get_connection():
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")

    async with _pool.connection() as conn:
        yield conn
