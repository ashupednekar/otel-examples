import uuid
from unittest import IsolatedAsyncioTestCase

from adaptors.models.orders import OrdersSchema
from adaptors.mutators.orders import OrderMutator
from adaptors.selectors.orders import OrderSelector
from conf import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker


class TestOrderSelector(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = async_sessionmaker(
            create_async_engine(
                settings.database_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_pool_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
                echo=settings.db_pool_echo,
                query_cache_size=0,
            )
        )
        return super().setUp()

    async def test_list(self):
        email = f"{uuid.uuid4().hex}@one.com"
        await OrderMutator.create(self.session, OrdersSchema(email=email))
        await OrderSelector.list(self.session, email)
