import logfire
from conf import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker


class AppState:
    def __init__(self):
        self.engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            echo=settings.db_pool_echo,
            query_cache_size=0,
        )
        self.pool = async_sessionmaker(self.engine)


state = AppState()
logfire.instrument_sqlalchemy(engine=state.engine.sync_engine)

def get_app_state() -> AppState:
    return state
