import main
import pytest


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_returns_201_and_can_be_read(client):
    response = client.post(
        "/todos",
        json={"title": "  Finish API tests  "},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["title"] == "Finish API tests"
    assert created["completed"] is False
    assert response.headers["location"] == f"/todos/{created['id']}"

    detail = client.get(f"/todos/{created['id']}")

    assert detail.status_code == 200
    assert detail.json() == created


def test_create_accepts_completed_true(client):
    response = client.post(
        "/todos",
        json={"title": "Already done", "completed": True},
    )

    assert response.status_code == 201
    assert response.json()["completed"] is True


def test_list_returns_todos_sorted_by_id(client):
    for todo_id, title in ((30, "Third"), (10, "First"), (20, "Second")):
        main.todos[todo_id] = main.Todo(
            id=todo_id,
            title=title,
            completed=False,
        )

    response = client.get("/todos")

    assert response.status_code == 200
    assert [todo["id"] for todo in response.json()] == [10, 20, 30]
    assert [todo["title"] for todo in response.json()] == [
        "First",
        "Second",
        "Third",
    ]


@pytest.mark.parametrize(
    "title",
    ["", "   ", "x" * 201],
)
def test_create_rejects_invalid_title(client, title):
    response = client.post("/todos", json={"title": title})

    assert response.status_code == 422
    assert client.get("/todos").json() == []


def test_create_requires_title(client):
    response = client.post("/todos", json={})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"title": 123},
        {"title": "Valid title", "completed": "yes"},
    ],
)
def test_create_rejects_invalid_field_types(client, payload):
    response = client.post("/todos", json=payload)

    assert response.status_code == 422


def test_get_missing_todo_returns_404(client):
    response = client.get("/todos/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


def test_patch_updates_only_supplied_fields(client):
    created = client.post(
        "/todos",
        json={"title": "Original title"},
    ).json()

    completed_update = client.patch(
        f"/todos/{created['id']}",
        json={"completed": True},
    )

    assert completed_update.status_code == 200
    assert completed_update.json() == {
        "id": created["id"],
        "title": "Original title",
        "completed": True,
    }

    title_update = client.patch(
        f"/todos/{created['id']}",
        json={"title": "  Updated title  "},
    )

    assert title_update.status_code == 200
    assert title_update.json() == {
        "id": created["id"],
        "title": "Updated title",
        "completed": True,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   "},
        {"title": "x" * 201},
        {"completed": "yes"},
        {"title": None},
    ],
)
def test_patch_rejects_invalid_payload_without_changing_todo(client, payload):
    created = client.post(
        "/todos",
        json={"title": "Keep this title"},
    ).json()

    response = client.patch(f"/todos/{created['id']}", json=payload)

    assert response.status_code == 422
    assert client.get(f"/todos/{created['id']}").json() == created


def test_patch_missing_todo_returns_404(client):
    response = client.patch("/todos/9999", json={"completed": True})

    assert response.status_code == 404


def test_delete_returns_204_and_todo_no_longer_exists(client):
    created = client.post(
        "/todos",
        json={"title": "Delete me"},
    ).json()

    deleted = client.delete(f"/todos/{created['id']}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/todos/{created['id']}").status_code == 404
    assert client.get("/todos").json() == []


def test_delete_missing_todo_returns_404(client):
    response = client.delete("/todos/9999")

    assert response.status_code == 404
