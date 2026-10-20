# 用 pytest 测试接口

> 本节目标：用 `TestClient` 调用 FastAPI 接口，验证状态码、响应体和错误路径，并用 fixture 隔离测试。

## 1. 安装与测试目录

安装测试依赖：

```bash
pip install -U pytest httpx
```

FastAPI 的 `TestClient` 基于 HTTPX，因此测试时需要 HTTPX。推荐结构：

```text
main.py
tests/
  conftest.py
  test_books.py
```

测试文件命名为 `test_*.py`，测试函数命名为 `test_*`，pytest 才能自动发现。

## 2. 创建客户端 fixture

`tests/conftest.py`：

```python
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def reset_store():
    main.books.clear()
    main.next_id = 1
    yield


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client
```

这里做了两件事：

- 每个测试前清空内存数据，避免测试互相影响。
- 创建 `TestClient`，测试函数可以直接用它发请求。

如果应用使用数据库，应改用独立测试库、事务回滚或应用工厂来隔离数据；不能共享开发数据库。

## 3. 第一条接口测试

`tests/test_books.py`：

```python
def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

一条测试通常遵循三段式：

1. **准备**：构造请求数据或测试依赖。
2. **执行**：调用接口。
3. **断言**：检查状态码和响应内容，必要时检查后续读取结果。

## 4. 验证完整业务流程

```python
def test_create_then_get_book(client):
    payload = {
        "title": "Python Basics",
        "author": "Ada",
        "year": 2024,
    }

    created = client.post("/books", json=payload)

    assert created.status_code == 201
    saved = created.json()
    assert saved["id"] == 1
    assert saved["title"] == payload["title"]
    assert created.headers["location"] == "/books/1"

    detail = client.get(f"/books/{saved['id']}")

    assert detail.status_code == 200
    assert detail.json() == saved
```

使用 `json=` 发送 JSON 请求体。`data=` 发送的是表单或原始内容，两者不能混用。

断言响应时优先检查可观察行为：

- 状态码是否符合接口契约。
- 关键字段是否正确，不必把所有数据库字段都写死。
- 创建后能否查询到，删除后是否确实不存在。
- 错误响应的结构是否稳定。

## 5. 测试参数校验与 404

```python
import pytest


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("year", 999),
        ("year", 2101),
    ],
)
def test_reject_invalid_book(client, field, value):
    payload = {
        "title": "Python Basics",
        "author": "Ada",
        "year": 2024,
    }
    payload[field] = value

    response = client.post("/books", json=payload)

    assert response.status_code == 422


def test_missing_book_returns_404(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"
```

`pytest.mark.parametrize` 用同一段逻辑覆盖多组输入，失败时会分别报告具体参数。

还可以检查分页参数边界：

```python
@pytest.mark.parametrize("limit", [0, 101])
def test_reject_invalid_limit(client, limit):
    response = client.get("/books", params={"limit": limit})

    assert response.status_code == 422
```

## 6. 替换数据库依赖

真实项目通常通过 `Depends` 注入数据库会话或仓储对象。测试时可以用依赖覆盖，把真实数据库换成内存实现：

```python
@pytest.fixture
def client_with_fake_repo():
    # app、get_book_repository 和 FakeBookRepository 需从应用与测试代码中导入或定义
    app.dependency_overrides[get_book_repository] = lambda: FakeBookRepository()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
```

前提是 `FakeBookRepository` 与真实仓储遵循相同的接口。这里测试的仍然是 HTTP 接口，而不是把路由函数直接当普通函数调用。

## 7. 常用命令

```bash
pytest -q                              # 安静模式运行全部测试
pytest -q tests/test_books.py          # 只运行一个文件
pytest -q tests/test_books.py::test_health   # 只运行一个测试
pytest -q -k "create or delete"        # 按名称筛选
pytest -x                              # 遇到第一个失败就停止
```

提交代码前至少运行一次完整测试集，确认没有依赖执行顺序的“偶然通过”。

## 8. 常见误区

- 只测试 `200`，不测试校验失败、资源不存在和权限错误。
- 测试之间共享数据库或全局状态，导致单独运行通过、一起运行失败。
- 断言依赖自增 ID、列表顺序或当前时间，结果不稳定。
- 直接修改请求字典后复用，导致后续参数化用例被污染。
- 只检查状态码，不检查关键响应字段和副作用。
- 把所有内部函数都 mock 掉，最后没有验证真实接口行为。
- 测试连接开发数据库，运行测试时破坏真实数据。

## 小练习

1. 为 `DELETE /books/{book_id}` 写成功和重复删除两条测试。
2. 为列表分页写测试：创建 3 本书，验证 `limit=2&offset=2` 的结果。
3. 为“重复标题返回 409”写测试，并确认错误信息符合约定。

完成这组练习后，你应能独立完成“设计接口、实现接口、验证接口”的基本闭环。
