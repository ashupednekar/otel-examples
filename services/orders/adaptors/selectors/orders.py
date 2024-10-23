from typing import List

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker
from ..models.orders import Orders, OrdersSchema


class OrderSelector:
    @staticmethod
    async def list(async_session: async_sessionmaker[AsyncSession], email: str):
        async with async_session() as session:
            result = await session.execute(select(Orders).where(Orders.email == email))
            return result.scalars().all()
