from sqlalchemy.ext.asyncio.session import async_sessionmaker
from utils.db import get_pool
from api.handlers.orders import router as order_router
import uvicorn


from fastapi import FastAPI


class AppState:
    def __init__(self):
        self.pool = async_sessionmaker(get_pool())


state = AppState()


def get_app_state() -> AppState:
    return state


app = FastAPI()
app.include_router(order_router)

if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
