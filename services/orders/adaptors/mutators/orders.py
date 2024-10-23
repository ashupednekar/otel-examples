import json

from nats.aio.client import Client as NATS
from sqlalchemy import select
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

    @staticmethod
    async def mark_as_paid(
        async_session: async_sessionmaker[AsyncSession],
        nats_client: NATS,
        order_id: str,
    ) -> None:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Orders).where(Orders.order_id == order_id)
                )
                order = result.scalars().one()
                order.payment_status = "paid"
                nats_client.publish(
                    "events.complete", json.dumps({"order_id": order.order_id}).encode()
                )
                await session.commit()
