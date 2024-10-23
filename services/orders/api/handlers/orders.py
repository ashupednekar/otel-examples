from typing import List

from fastapi import APIRouter, Depends, HTTPException

from adaptors.models.orders import OrdersSchema
from adaptors.mutators.orders import OrderMutator
from adaptors.selectors.orders import OrderSelector
from api.state import AppState, get_app_state

router = APIRouter()


@router.post("/orders/")
async def create_order(
    order: OrdersSchema,
    state: AppState = Depends(get_app_state),
) -> OrdersSchema:
    await OrderMutator.create(state.pool, order)
    return order


@router.get("/orders/", response_model=List[OrdersSchema])
async def list_orders(
    email: str,  # Keep this required if you want it to be mandatory
    state: AppState = Depends(get_app_state),
) -> List[OrdersSchema]:
    orders = await OrderSelector.list(state.pool, email)
    return orders
