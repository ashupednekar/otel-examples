import uuid
from unittest import IsolatedAsyncioTestCase

from sqlalchemy.ext.asyncio.session import async_sessionmaker

from adaptors.models.orders import OrdersSchema
from adaptors.mutators.orders import OrderMutator
from adaptors.selectors.orders import OrderSelector
from utils.db import get_pool


class TestOrderSelector(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = async_sessionmaker(get_pool())
        return super().setUp()

    async def test_list(self):
        email = f"{uuid.uuid4().hex}@one.com"
        await OrderMutator.create(self.session, OrdersSchema(email=email))
        await OrderSelector.list(self.session, email)
