from pathlib import Path
import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine


DEFAULT_DATABASE_URL = "sqlite:///./data/todos.db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _sqlite_connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///") or database_url == "sqlite://":
        return

    sqlite_path = database_url.replace("sqlite:///", "", 1)
    if sqlite_path == ":memory:":
        return

    database_file = Path(sqlite_path)
    if database_file.parent != Path("."):
        database_file.parent.mkdir(parents=True, exist_ok=True)


DATABASE_URL = get_database_url()
_ensure_sqlite_directory(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args=_sqlite_connect_args(DATABASE_URL))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
