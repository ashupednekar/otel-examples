import uuid

from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker
from ..models.orders import Orders, OrdersSchema


class OrderMutator:
    @staticmethod
    async def create(
        async_session: async_sessionmaker[AsyncSession], order: OrdersSchema
    ) -> OrdersSchema:
        order_entry: Orders = Orders(
            order_id=order.order_id,
            email=order.email,
            payment_status=order.payment_status,
        )
        async with async_session() as session:
            async with session.begin():
                session.add_all([order_entry])
                return order
