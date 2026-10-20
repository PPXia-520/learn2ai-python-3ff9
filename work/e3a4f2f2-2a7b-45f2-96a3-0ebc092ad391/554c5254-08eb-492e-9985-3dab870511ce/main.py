from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

app = FastAPI(title="Todo API", version="1.0.0")


class TodoCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str
    completed: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not 1 <= len(title) <= 200:
            raise ValueError("title must contain between 1 and 200 characters")
        return title


class TodoUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        title = value.strip()
        if not 1 <= len(title) <= 200:
            raise ValueError("title must contain between 1 and 200 characters")
        return title

    @model_validator(mode="after")
    def reject_explicit_null(self) -> "TodoUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class Todo(BaseModel):
    id: int = Field(gt=0)
    title: str
    completed: bool


todos: dict[int, Todo] = {}
next_id = 1


def reset_store() -> None:
    global next_id
    todos.clear()
    next_id = 1


def find_todo_or_404(todo_id: int) -> Todo:
    todo = todos.get(todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return todo


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    return sorted(todos.values(), key=lambda todo: todo.id)


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, response: Response) -> Todo:
    global next_id

    todo = Todo(
        id=next_id,
        title=payload.title,
        completed=payload.completed,
    )
    todos[todo.id] = todo
    next_id += 1
    response.headers["Location"] = f"/todos/{todo.id}"
    return todo


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    return find_todo_or_404(todo_id)


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoUpdate) -> Todo:
    todo = find_todo_or_404(todo_id)
    changes = payload.model_dump(exclude_unset=True)
    updated = todo.model_copy(update=changes)
    todos[todo_id] = updated
    return updated


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> Response:
    find_todo_or_404(todo_id)
    del todos[todo_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
