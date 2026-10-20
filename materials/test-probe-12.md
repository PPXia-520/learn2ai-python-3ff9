# HTTP 与 REST 接口设计

> 本节目标：看懂一次 HTTP 请求，能用资源、方法和状态码设计一组清晰的 CRUD 接口。

## 1. HTTP 请求与响应

一次 HTTP 交互可以理解为“请求做什么”，再返回“结果是什么”：

```http
POST /books HTTP/1.1
Host: api.example.com
Content-Type: application/json
