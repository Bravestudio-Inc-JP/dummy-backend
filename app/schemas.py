from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class TodoListCreate(SQLModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False


class TodoListUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class TodoListRead(SQLModel):
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
