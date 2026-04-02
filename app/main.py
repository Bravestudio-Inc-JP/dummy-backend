from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import create_db_and_tables
from app.routers.todo_lists import router as todo_lists_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Todo List API", lifespan=lifespan)
app.include_router(todo_lists_router)


@app.get("/")
def read_root() -> dict:
    return {"message": "Todo List API is running"}
