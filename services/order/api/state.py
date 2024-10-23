from sqlalchemy.ext.asyncio.session import async_sessionmaker

from utils.db import get_pool


class AppState:
    def __init__(self):
        self.pool = async_sessionmaker(get_pool())


state = AppState()


def get_app_state() -> AppState:
    return state
