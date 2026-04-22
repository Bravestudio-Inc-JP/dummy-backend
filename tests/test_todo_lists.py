from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_todo_list(client: TestClient) -> None:
    response = client.post("/todo-lists", json={"title": "Ship API"})

    assert response.status_code == 201
    assert response.headers["location"].endswith("/todo-lists/1")
    body = response.json()
    assert body["title"] == "Ship API"
    assert body["description"] is None
    assert body["is_completed"] is False
    assert body["id"] == 1
    assert body["created_at"]
    assert body["updated_at"]


def test_list_todo_lists_with_pagination(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "First"})
    client.post("/todo-lists", json={"title": "Second"})

    response = client.get("/todo-lists", params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {
        "offset": 1,
        "limit": 1,
        "total": 2,
        "has_more": False,
    }
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "First"


def test_list_todo_lists_can_filter_by_completion(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Open", "is_completed": False})
    client.post("/todo-lists", json={"title": "Closed", "is_completed": True})

    response = client.get("/todo-lists", params={"is_completed": "true"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Closed"
    assert body["items"][0]["is_completed"] is True


def test_list_todo_lists_can_order_by_title_desc(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Alpha"})
    client.post("/todo-lists", json={"title": "Zulu"})

    response = client.get("/todo-lists", params={"order_by": "title_desc"})

    assert response.status_code == 200
    body = response.json()
    assert [item["title"] for item in body["items"]] == ["Zulu", "Alpha"]


def test_list_todo_lists_can_search(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Ship backend"})
    client.post("/todo-lists", json={"title": "Buy groceries"})

    response = client.get("/todo-lists", params={"q": "Ship"})

    assert response.status_code == 200
    body = response.json()
    assert body["filters"]["q"] == "Ship"
    assert [item["title"] for item in body["items"]] == ["Ship backend"]


def test_summary_endpoint_returns_aggregates(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Plan sprint", "is_completed": False})
    client.post("/todo-lists", json={"title": "Deploy", "is_completed": True})

    response = client.get("/todo-lists/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total": 2,
        "completed": 1,
        "pending": 1,
    }


def test_read_single_todo_list(client: TestClient) -> None:
    create_response = client.post("/todo-lists", json={"title": "Read me"})

    response = client.get("/todo-lists/1")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["title"] == "Read me"


def test_update_todo_list_partial(client: TestClient) -> None:
    create_response = client.post("/todo-lists", json={"title": "Before"})
    original = create_response.json()

    response = client.patch(
        "/todo-lists/1",
        json={"description": "After", "is_completed": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Before"
    assert body["description"] == "After"
    assert body["is_completed"] is True
    assert body["updated_at"] >= original["updated_at"]


def test_delete_todo_list(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Delete me"})

    delete_response = client.delete("/todo-lists/1")
    get_response = client.get("/todo-lists/1")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


def test_replace_todo_list(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Legacy"})

    response = client.put(
        "/todo-lists/1",
        json={
            "title": "Replacement",
            "description": "Rewritten payload",
            "is_completed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Replacement"
    assert body["description"] == "Rewritten payload"
    assert body["is_completed"] is True


def test_complete_and_reopen_todo_list(client: TestClient) -> None:
    client.post("/todo-lists", json={"title": "Lifecycle"})

    complete_response = client.post("/todo-lists/1/complete")
    reopen_response = client.post("/todo-lists/1/reopen")

    assert complete_response.status_code == 200
    assert complete_response.json()["is_completed"] is True
    assert reopen_response.status_code == 200
    assert reopen_response.json()["is_completed"] is False


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_missing_todo_list_returns_404(client: TestClient, method: str) -> None:
    request_method = getattr(client, method)
    if method == "patch":
        kwargs = {"json": {"title": "ignored"}}
    elif method == "put":
        kwargs = {"json": {"title": "ignored"}}
    else:
        kwargs = {}

    response = request_method("/todo-lists/999", **kwargs)

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo list not found"}


def test_create_todo_list_requires_title(client: TestClient) -> None:
    response = client.post("/todo-lists", json={"description": "Missing title"})

    assert response.status_code == 422
