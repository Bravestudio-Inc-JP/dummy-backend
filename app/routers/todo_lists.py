from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlmodel import Session, col, func, select

from app.db import get_session
from app.models import TodoList
from app.schemas import (
    TodoListCreate,
    TodoListListFilters,
    TodoListListMeta,
    TodoListListResponse,
    TodoListRead,
    TodoListReplace,
    TodoListSummary,
    TodoListUpdate,
)


router = APIRouter(prefix="/todo-lists", tags=["todo-lists"])


def _save_and_refresh(session: Session, todo_list: TodoList) -> TodoList:
    todo_list.updated_at = datetime.now(timezone.utc)
    session.add(todo_list)
    session.commit()
    session.refresh(todo_list)
    return todo_list


def _get_todo_list_or_404(todo_list_id: int, session: Session) -> TodoList:
    todo_list = session.get(TodoList, todo_list_id)
    if todo_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo list not found")
    return todo_list


@router.post("", response_model=TodoListRead, status_code=status.HTTP_201_CREATED)
def create_todo_list(
    todo_list: TodoListCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    db_todo_list = TodoList.model_validate(todo_list)
    session.add(db_todo_list)
    session.commit()
    session.refresh(db_todo_list)
    location = request.url_for("read_todo_list", todo_list_id=db_todo_list.id)
    response = JSONResponse(
        content=TodoListRead.model_validate(db_todo_list).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
        headers={"Location": str(location)},
    )
    return response


@router.get("", response_model=TodoListListResponse)
def read_todo_lists(
    offset: int = 0,
    limit: int = Query(default=100, ge=1, le=100),
    q: str | None = Query(default=None, min_length=1, max_length=255),
    is_completed: bool | None = None,
    order_by: Literal[
        "created_at_desc",
        "created_at_asc",
        "title_asc",
        "title_desc",
        "updated_at_desc",
        "updated_at_asc",
    ] = "created_at_desc",
    session: Session = Depends(get_session),
) -> TodoListListResponse:
    statement = select(TodoList)
    count_statement = select(func.count()).select_from(TodoList)

    filters = []

    if q is not None:
        search_pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                col(TodoList.title).ilike(search_pattern),
                col(TodoList.description).ilike(search_pattern),
            )
        )

    if is_completed is not None:
        filters.append(TodoList.is_completed == is_completed)

    for predicate in filters:
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    order_expressions = {
        "created_at_desc": col(TodoList.created_at).desc(),
        "created_at_asc": col(TodoList.created_at).asc(),
        "title_asc": col(TodoList.title).asc(),
        "title_desc": col(TodoList.title).desc(),
        "updated_at_desc": col(TodoList.updated_at).desc(),
        "updated_at_asc": col(TodoList.updated_at).asc(),
    }
    statement = statement.order_by(order_expressions[order_by]).offset(offset).limit(limit)

    todo_lists = session.exec(statement).all()
    total = session.exec(count_statement).one()

    return TodoListListResponse(
        items=[TodoListRead.model_validate(item) for item in todo_lists],
        pagination=TodoListListMeta(
            offset=offset,
            limit=limit,
            total=total,
            has_more=offset + len(todo_lists) < total,
        ),
        filters=TodoListListFilters(
            q=q,
            is_completed=is_completed,
        ),
    )


@router.get("/summary", response_model=TodoListSummary)
def read_todo_list_summary(session: Session = Depends(get_session)) -> TodoListSummary:
    total = session.exec(select(func.count()).select_from(TodoList)).one()
    completed = session.exec(select(func.count()).select_from(TodoList).where(TodoList.is_completed.is_(True))).one()
    pending = session.exec(select(func.count()).select_from(TodoList).where(TodoList.is_completed.is_(False))).one()

    return TodoListSummary(
        total=total,
        completed=completed,
        pending=pending,
    )


@router.get("/{todo_list_id}", response_model=TodoListRead)
def read_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> TodoList:
    return _get_todo_list_or_404(todo_list_id, session)


@router.put("/{todo_list_id}", response_model=TodoListRead)
def replace_todo_list(
    todo_list_id: int,
    todo_list_replace: TodoListReplace,
    session: Session = Depends(get_session),
) -> TodoList:
    todo_list = _get_todo_list_or_404(todo_list_id, session)
    replacement = todo_list_replace.model_dump()
    todo_list.sqlmodel_update(replacement)
    return _save_and_refresh(session, todo_list)


@router.patch("/{todo_list_id}", response_model=TodoListRead)
def update_todo_list(
    todo_list_id: int,
    todo_list_update: TodoListUpdate,
    session: Session = Depends(get_session),
) -> TodoList:
    todo_list = _get_todo_list_or_404(todo_list_id, session)
    update_data = todo_list_update.model_dump(exclude_unset=True)
    todo_list.sqlmodel_update(update_data)
    return _save_and_refresh(session, todo_list)


@router.post("/{todo_list_id}/complete", response_model=TodoListRead)
def complete_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> TodoList:
    todo_list = _get_todo_list_or_404(todo_list_id, session)
    todo_list.is_completed = True
    return _save_and_refresh(session, todo_list)


@router.post("/{todo_list_id}/reopen", response_model=TodoListRead)
def reopen_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> TodoList:
    todo_list = _get_todo_list_or_404(todo_list_id, session)
    todo_list.is_completed = False
    return _save_and_refresh(session, todo_list)


@router.delete("/{todo_list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> Response:
    todo_list = _get_todo_list_or_404(todo_list_id, session)
    session.delete(todo_list)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
