import json

import logfire
from nats.aio.client import Client as NATS
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker

from ..models.orders import Orders, OrdersSchema


class OrderMutator:
    @staticmethod
    async def create(
        async_session: async_sessionmaker[AsyncSession], order: OrdersSchema
    ) -> OrdersSchema:
        with logfire.span("creating entry from deserialized input"):
            order_entry: Orders = Orders(
                order_id=order.order_id,
                email=order.email,
                payment_status=order.payment_status,
            )
        async with async_session() as session:
            async with session.begin():
                # note: atomicity not needed here, just for illustration
                with logfire.span("creating order entry"):
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
                with logfire.span("retrieving order entry"):
                    result = await session.execute(
                        select(Orders).where(Orders.order_id == order_id)
                    )
                    order = (
                        result.scalars().one()
                    )  # note: not handled error for illustration
                with logfire.span("updating payment status and publishing event"):
                    order.payment_status = "paid"
                    await nats_client.publish(
                        "events.complete",
                        json.dumps(
                            {"order_id": order.order_id, "email": order.email}
                        ).encode(),
                    )
                    await session.commit()
