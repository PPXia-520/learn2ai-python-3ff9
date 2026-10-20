# HTTP 与 REST 接口设计

> 本节目标：看懂一次 HTTP 请求，能用资源、方法和状态码设计一组清晰的 CRUD 接口。

## 1. HTTP 请求与响应

一次 HTTP 交互可以理解为“请求做什么”，再返回“结果是什么”：

```http
POST /books HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"title": "Python Basics", "author": "Ada", "year": 2024}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /books/42

{"id": 42, "title": "Python Basics", "author": "Ada", "year": 2024}
```

重点字段：

- **方法**：`GET` 读取，`POST` 新建，`PUT` 整体替换，`PATCH` 局部修改，`DELETE` 删除。
- **路径**：接口定位的资源，例如 `/books`、`/books/42`。
- **请求头**：描述请求，例如 `Content-Type: application/json`。
- **请求体**：通常是 JSON，用于提交数据；`GET` 一般不使用请求体。
- **状态码**：说明结果类别，例如成功、参数错误或资源不存在。

## 2. REST 的核心：把接口看成资源

REST 风格常用“名词资源 + HTTP 方法”表达操作，而不是把动词写进路径：

```text
好：GET    /books
好：POST   /books
好：GET    /books/42
好：PATCH  /books/42
不好：GET  /getBooks
不好：POST /books/delete/42
```

资源通常使用复数名词。集合是 `/books`，单个资源是 `/books/{id}`。动作由 HTTP 方法表达。

| 操作 | 方法 | 典型路径 | 成功状态码 |
| --- | --- | --- | --- |
| 查询列表 | `GET` | `/books?limit=20` | `200` |
| 查询单个 | `GET` | `/books/42` | `200` 或 `404` |
| 新建 | `POST` | `/books` | `201` |
| 整体替换 | `PUT` | `/books/42` | `200` 或 `204` |
| 局部修改 | `PATCH` | `/books/42` | `200` |
| 删除 | `DELETE` | `/books/42` | `204` 或 `404` |

方法语义要稳定：

- `GET` 不修改数据，重复调用结果不变。
- `POST` 通常创建新资源，重复提交可能创建多条记录。
- `PUT` 和 `DELETE` 应当是幂等的：相同请求执行多次，最终资源状态相同。
- `PATCH` 用来只提交需要改变的部分，例如 `{"year": 2025}`。

## 3. 选择合适的状态码

不要所有结果都返回 `200`。客户端常根据状态码决定是否重试、提示错误或跳转。

| 状态码 | 含义 | 示例 |
| --- | --- | --- |
| `200 OK` | 请求成功并有响应体 | 查询成功 |
| `201 Created` | 已创建资源 | 新建图书成功 |
| `204 No Content` | 成功，但没有响应体 | 删除成功 |
| `400 Bad Request` | 请求格式或业务参数错误 | JSON 字段组合不合法 |
| `401 Unauthorized` | 尚未认证 | 没带登录凭证 |
| `403 Forbidden` | 已认证但无权限 | 普通用户删除他人资源 |
| `404 Not Found` | 资源不存在 | `/books/9999` |
| `409 Conflict` | 与现有状态冲突 | ISBN 已存在 |
| `422 Unprocessable Content` | 字段校验失败 | `year` 不是整数 |
| `500 Internal Server Error` | 服务端未处理异常 | 数据库连接失败 |

`422` 常用于请求能解析、但字段不符合规则；`400` 更适合请求本身或业务格式有误。团队内保持一致比死记边界更重要。

## 4. 设计 JSON 契约

接口字段应可预测，并保持命名一致。例如统一使用 `snake_case`：

```json
{
  "id": 42,
  "title": "Python Basics",
  "author": "Ada",
  "year": 2024,
  "created_at": "2026-10-20T08:30:00Z"
}
```

错误响应也应有固定结构，避免有时返回字符串、有时返回数组。下面是自定义约定；FastAPI 默认使用 `detail` 字段，后文会说明：

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "Book not found"
  }
}
```

列表接口需要分页，避免一次返回全部数据：

```http
GET /books?limit=20&offset=0
```

```json
{
  "items": [{"id": 42, "title": "Python Basics"}],
  "total": 125,
  "limit": 20,
  "offset": 0
}
```

`limit` 限制单页数量，`offset` 表示跳过多少条。数据量很大或频繁增删时，可以再改用游标分页。

## 5. 一个完整的接口清单

以“图书管理”为例：

```text
GET    /health             服务健康检查
GET    /books              支持 limit、offset、q 搜索
POST   /books              创建图书，返回 201 和 Location
GET    /books/{book_id}    查询单本图书
PATCH  /books/{book_id}    修改部分字段
DELETE /books/{book_id}    删除图书，成功返回 204
```

设计时先问三个问题：

1. 这里操作的核心资源是什么？
2. 客户端需要读取、创建、修改还是删除它？
3. 成功、参数错误、无权限、资源不存在分别应返回什么状态码？

## 6. 常见误区

- 在 URL 中堆动词，例如 `/books/create`、`/books/getById`。
- 业务失败也返回 `200`，把错误藏进 `{"success": false}`。
- 直接返回数据库异常、堆栈或内部表名。
- `PUT` 只传一个字段，却把它当作完整替换。
- 列表接口没有分页、排序规则或稳定字段。
- 为了“纯 REST”阻塞真实需求；REST 是设计工具，不是必须逐条遵守的法规。

## 小练习

1. 为“文章及其评论”设计 5 个接口，写出方法、路径和成功状态码。
2. 创建资源、删除成功、请求字段非法、重复用户名，分别应使用哪些状态码？
3. 把 `/getUserOrders?userId=7` 改成更符合资源风格的接口路径。

下一节将把这份接口清单实现为 FastAPI 服务。
