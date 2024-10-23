import logging

import logfire
import uvicorn
from api.handlers.orders import router as order_router
from fastapi import FastAPI

logfire.configure(service_name="order", send_to_logfire=False)

logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])

app = FastAPI()
logfire.instrument_fastapi(app)

app.include_router(order_router)

if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
