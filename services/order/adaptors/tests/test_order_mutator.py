from unittest import IsolatedAsyncioTestCase

from sqlalchemy.ext.asyncio import create_async_engine

from adaptors.models.orders import OrdersSchema
from adaptors.mutators.orders import OrderMutator
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from conf import settings

class TestOrderMutator(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = async_sessionmaker(create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            echo=settings.db_pool_echo,
            query_cache_size=0,
            ))
        return super().setUp()

    async def test_create(self):
        await OrderMutator.create(
            self.session, OrdersSchema(email="one@one.com", order_id="OR0001")
        )
