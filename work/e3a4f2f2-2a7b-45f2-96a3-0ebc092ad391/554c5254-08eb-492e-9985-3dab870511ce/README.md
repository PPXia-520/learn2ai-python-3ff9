# 待办事项 API

一个使用 FastAPI 实现的内存版待办事项 API。数据仅保存在进程内，重启服务后会清空。

## 项目结构

```text
.
├── main.py
├── requirements.txt
├── README.md
└── tests
    ├── conftest.py
    └── test_todos.py
```

## 安装

建议使用 Python 3.10 或更高版本。

```bash
python -m venv .venv
pip install -r requirements.txt
```

PowerShell 激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

## 启动

在成果目录根路径执行：

```bash
uvicorn main:app --reload
```

启动后可访问：

- 接口文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

## 接口

| 方法 | 路径 | 说明 | 成功状态码 |
| --- | --- | --- | --- |
| `GET` | `/health` | 健康检查 | `200` |
| `GET` | `/todos` | 按 `id` 升序返回全部待办 | `200` |
| `POST` | `/todos` | 创建待办，请求体包含 `title`，可选 `completed` | `201` |
| `GET` | `/todos/{todo_id}` | 查询单条待办 | `200` |
| `PATCH` | `/todos/{todo_id}` | 部分更新 `title` 和/或 `completed` | `200` |
| `DELETE` | `/todos/{todo_id}` | 删除待办，响应体为空 | `204` |

`title` 会去除首尾空白，处理后长度必须为 1～200。字段类型错误、空标题或超长标题返回 `422`；访问不存在的资源返回 `404`。

创建示例：

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"完成接口测试"}'
```

## 测试

在成果目录根路径执行：

```bash
pytest -q
```

`tests/conftest.py` 会在每个测试前清空内存数据和自增计数器，因此测试可以单独运行，也可以任意顺序运行。

测试覆盖：

- `test_health`：健康检查状态码和响应体。
- `test_create_returns_201_and_can_be_read`：创建成功、标题去空白、默认状态、`Location` 头和后续读取。
- `test_create_accepts_completed_true`：创建时显式设置 `completed`。
- `test_list_returns_todos_sorted_by_id`：列表按 `id` 升序返回。
- `test_create_rejects_invalid_title`：空标题、纯空白标题和超长标题均返回 `422`。
- `test_create_requires_title`：缺少必填标题返回 `422`。
- `test_create_rejects_invalid_field_types`：标题和完成状态类型错误返回 `422`。
- `test_get_missing_todo_returns_404`：查询不存在的资源返回 `404`。
- `test_patch_updates_only_supplied_fields`：局部更新不会覆盖未提交字段。
- `test_patch_rejects_invalid_payload_without_changing_todo`：非法更新返回 `422` 且不修改原数据。
- `test_patch_missing_todo_returns_404`：修改不存在的资源返回 `404`。
- `test_delete_returns_204_and_todo_no_longer_exists`：删除返回 `204`、响应体为空，之后查询返回 `404`。
- `test_delete_missing_todo_returns_404`：删除不存在的资源返回 `404`。

## 测试结果

在 Python 3.13.2、FastAPI 0.141.1、pytest 8.4.2 环境下执行：

```text
19 passed, 1 warning in 0.78s
```

共 13 个测试函数，参数化后展开为 19 个测试用例，全部通过。警告来自当前 Starlette `TestClient` 对 HTTPX 的弃用提示，不影响测试结果。
