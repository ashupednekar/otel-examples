from unittest import IsolatedAsyncioTestCase

from sqlalchemy.ext.asyncio.session import async_sessionmaker
from adaptors.models.orders import OrdersSchema
from adaptors.mutators.orders import OrderMutator
from utils.db import get_pool


class TestOrderMutator(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = async_sessionmaker(get_pool())
        return super().setUp()

    async def test_create(self):
        await OrderMutator.create(
            self.session, OrdersSchema(email="one@one.com", order_id="OR0001")
        )
