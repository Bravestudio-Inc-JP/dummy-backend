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


class TodoListReplace(SQLModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False


class TodoListRead(SQLModel):
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime


class TodoListListMeta(SQLModel):
    offset: int
    limit: int
    total: int
    has_more: bool


class TodoListListFilters(SQLModel):
    q: Optional[str] = None
    is_completed: Optional[bool] = None


class TodoListListResponse(SQLModel):
    items: list[TodoListRead]
    pagination: TodoListListMeta
    filters: TodoListListFilters


class TodoListSummary(SQLModel):
    total: int
    completed: int
    pending: int
