# FastAPI 快速上手

> 本节目标：启动一个 FastAPI 服务，完成带参数校验、错误处理和自动文档的图书 CRUD 接口。

## 1. 安装与启动

建议使用 Python 3.10 或更高版本，并在虚拟环境中安装：

```bash
python -m venv .venv
pip install fastapi "uvicorn[standard]"
```

在 PowerShell 中激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

最小应用 `main.py`：

```python
from fastapi import FastAPI

app = FastAPI(title="Book API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

启动开发服务器：

```bash
uvicorn main:app --reload
```

- `main` 是文件名，`app` 是 `FastAPI` 实例。
- `--reload` 会在代码变化后重启，仅适合开发环境。
- 打开 `http://127.0.0.1:8000/docs` 可查看并试用自动生成的接口文档。

## 2. 用 Pydantic 描述输入

FastAPI 会把类型注解用于参数解析和校验。请求体用 Pydantic 模型描述：

```python
from pydantic import BaseModel, Field


class BookInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1000, le=2100)


class Book(BookInput):
    id: int
```

字段不合规时，FastAPI 会自动返回 `422`，并在响应中说明哪个字段出错，不需要手写大量 `if`。

## 3. 一个可运行的 CRUD 示例

下面的代码可以替换 `main.py` 的内容，使用内存字典保存数据：

```python
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI(title="Book API", version="1.0.0")


class BookInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1000, le=2100)


class Book(BookInput):
    id: int


books: dict[int, Book] = {}
next_id = 1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/books", response_model=list[Book])
def list_books(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Book]:
    return list(books.values())[offset : offset + limit]


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int) -> Book:
    book = books.get(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookInput, response: Response) -> Book:
    global next_id
    book = Book(id=next_id, **payload.model_dump())
    books[book.id] = book
    next_id += 1
    response.headers["Location"] = f"/books/{book.id}"
    return book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int) -> None:
    if book_id not in books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    del books[book_id]
```

运行后可以直接在 `/docs` 里调用接口。也可以使用命令行：

```bash
curl -X POST http://127.0.0.1:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Python Basics","author":"Ada","year":2024}'
```

Windows PowerShell 可使用：

```powershell
$body = '{"title":"Python Basics","author":"Ada","year":2024}'
Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:8000/books' `
  -ContentType 'application/json; charset=utf-8' `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

## 4. 路径、查询和请求体

FastAPI 根据位置和类型决定参数来源：

```python
@app.get("/books/{book_id}")
def get_book(book_id: int): ...
```

`book_id` 来自路径。下面的 `limit` 和 `q` 来自查询字符串：

```python
@app.get("/books")
def list_books(
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
): ...
```

请求示例：`GET /books?limit=10&q=python`。

带 Pydantic 模型参数的 `POST` 或 `PATCH` 函数，模型来自 JSON 请求体。

## 5. 状态码与错误

- 返回对象时，FastAPI 会自动序列化为 JSON。
- 新建成功用 `status_code=status.HTTP_201_CREATED`。
- 删除成功且无响应体用 `204`。
- 业务错误用 `HTTPException` 抛出，而不是返回 `{"ok": False}` 加 `200`。
- FastAPI 默认把 `HTTPException` 的 `detail` 包装为 `{"detail": "..."}`；需要统一错误码时，可在应用层添加异常处理器。
- 未捕获异常会变成 `500`；不要把数据库连接串、堆栈等细节返回给客户端。

可以统一错误结构，例如：

```python
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Book already exists",
)
```

## 6. 代码变多后拆路由

项目变大时，不要把所有接口堆在一个文件。可将图书接口放入 `routers/books.py`：

```python
from fastapi import APIRouter

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
def list_books(): ...
```

在 `main.py` 中注册：

```python
from routers import books

app.include_router(books.router)
```

常见结构：

```text
app/
  main.py
  models.py
  routers/
    books.py
  tests/
    test_books.py
```

此时启动命令通常是 `uvicorn app.main:app --reload`，具体取决于包结构。

## 7. 常见问题

- **改了代码但没生效**：确认启动时加了 `--reload`，并检查运行的文件和端口。
- **请求体一直被当成查询参数**：请求体必须是 Pydantic 模型或 `Body(...)`，同时设置 JSON 请求头。
- **测试数据串在一起**：示例用全局内存字典，仅适合入门；真实项目应使用数据库并隔离测试数据。
- **滥用 `async def`**：只有调用异步库时才需要；普通同步数据库操作可以先用普通 `def`。
- **把 `/docs` 当生产安全措施**：文档会暴露接口结构，生产环境应按需求限制访问。

## 小练习

1. 增加 `PATCH /books/{book_id}`，只修改请求中出现的字段。
2. 增加按 `q` 模糊搜索标题的查询参数。
3. 给 `POST /books` 增加“标题不能重复”的 `409` 检查。

实现后，下一节将用 pytest 验证这些接口的成功与失败路径。
