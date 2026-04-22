from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TodoListBase(SQLModel):
    title: str = Field(index=True, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_completed: bool = False


class TodoList(TodoListBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
