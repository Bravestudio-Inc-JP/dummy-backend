from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import TodoList
from app.schemas import TodoListCreate, TodoListRead, TodoListUpdate


router = APIRouter(prefix="/todo-lists", tags=["todo-lists"])


@router.post("", response_model=TodoListRead, status_code=status.HTTP_201_CREATED)
def create_todo_list(
    todo_list: TodoListCreate,
    session: Session = Depends(get_session),
) -> TodoList:
    db_todo_list = TodoList.model_validate(todo_list)
    session.add(db_todo_list)
    session.commit()
    session.refresh(db_todo_list)
    return db_todo_list


@router.get("", response_model=list[TodoListRead])
def read_todo_lists(
    offset: int = 0,
    limit: int = Query(default=100, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[TodoList]:
    todo_lists = session.exec(select(TodoList).offset(offset).limit(limit)).all()
    return list(todo_lists)


@router.get("/{todo_list_id}", response_model=TodoListRead)
def read_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> TodoList:
    todo_list = session.get(TodoList, todo_list_id)
    if todo_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo list not found")
    return todo_list


@router.patch("/{todo_list_id}", response_model=TodoListRead)
def update_todo_list(
    todo_list_id: int,
    todo_list_update: TodoListUpdate,
    session: Session = Depends(get_session),
) -> TodoList:
    todo_list = session.get(TodoList, todo_list_id)
    if todo_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo list not found")

    update_data = todo_list_update.model_dump(exclude_unset=True)
    todo_list.sqlmodel_update(update_data)
    todo_list.updated_at = datetime.now(timezone.utc)
    session.add(todo_list)
    session.commit()
    session.refresh(todo_list)
    return todo_list


@router.delete("/{todo_list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_list(todo_list_id: int, session: Session = Depends(get_session)) -> Response:
    todo_list = session.get(TodoList, todo_list_id)
    if todo_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo list not found")

    session.delete(todo_list)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
