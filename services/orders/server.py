from conf import settings
from utils.db import get_pool
import uvicorn


from fastapi import FastAPI

app: FastAPI = FastAPI()



if __name__ == '__main__':
	uvicorn.run(app, port=8080, host="0.0.0.0")
