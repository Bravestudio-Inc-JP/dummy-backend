# Dummy Backend

FastAPI APIs for Todo Lists with SQLite storage.

The API now exposes richer task workflow features:

- paginated list responses with filter metadata
- search on list endpoints
- lifecycle endpoints to complete or reopen a task
- aggregate summary endpoint at `GET /todo-lists/summary`
