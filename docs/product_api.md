# 商品管理接口文档

## 功能概述

本模块提供了商品管理的完整功能，包括：
- 创建商品（支持多张图片上传）
- 查询商品信息
- 查询商品列表
- 更新商品信息
- 删除商品

所有接口支持事务管理和回滚机制，确保数据一致性。

## 权限说明

### 角色定义

系统支持两种用户角色：

1. **超级管理员（is_superuser = True）：**
   - 拥有所有权限
   - 可以创建、修改、删除商品
   - 可以查询商品

2. **普通用户（is_superuser = False）：**
   - 仅拥有查询权限
   - 可以查询商品信息
   - 不可以创建、修改、删除商品

### 权限矩阵

| 操作 | 超级管理员 | 普通用户 |
|------|----------|----------|
| 创建商品 | ✅ | ❌ |
| 查询商品信息 | ✅ | ✅ |
| 查询商品列表 | ✅ | ✅ |
| 更新商品信息 | ✅ | ❌ |
| 删除商品 | ✅ | ❌ |

### 认证要求

所有接口都需要用户认证（通过 JWT Token）。

- **需要认证的接口：** 所有接口
- **认证方式：** Bearer Token（JWT）
- **Token 获取：** 登录接口返回 `access_token`

### 权限错误响应

当用户权限不足时，返回以下错误响应：

```json
{
  "error": "只有超级管理员才能执行此操作",
  "status_code": 403,
  "path": "/v1/product/products"
}
```

## 数据库设计

### products 表（商品表）

| 字段名 | 类型 | 说明 |
|---------|------|------|
| `id` | INT | 商品ID（主键）|
| `product_id` | VARCHAR(100) | 商品唯一标识（UUID）|
| `name` | VARCHAR(200) | 商品名称 |
| `description` | TEXT | 商品描述 |
| `price` | FLOAT | 商品价格 |
| `stock` | INT | 库存数量 |
| `cover_image` | VARCHAR(500) | 封面图片URL |
| `rental_status` | INT | 租赁状态（0-不可租赁，1-可租赁）|
| `rental_price_single` | FLOAT | 单次租赁价格 |
| `rental_price_week` | FLOAT | 一周租赁价格 |
| `rental_price_month` | FLOAT | 一个月租赁价格 |
| `status` | INT | 商品状态（0-下架，1-上架）|
| `is_active` | BOOLEAN | 是否激活 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

### product_images 表（商品图片表）

| 字段名 | 类型 | 说明 |
|---------|------|------|
| `id` | INT | 图片ID（主键）|
| `product_id` | VARCHAR(100) | 商品唯一标识（外键）|
| `image_url` | VARCHAR(500) | 图片URL |
| `is_cover` | BOOLEAN | 是否封面图 |
| `sort_order` | INT | 排序 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

## API 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|--------|
| POST | `/v1/product/products` | 创建商品 | 超级管理员 |
| GET | `/v1/product/products/{product_id}` | 查询商品信息 | 所有角色 |
| GET | `/v1/product/products` | 查询商品列表 | 所有角色 |
| PUT | `/v1/product/products/{product_id}` | 更新商品信息 | 超级管理员 |
| DELETE | `/v1/product/products/{product_id}` | 删除商品 | 超级管理员 |

## 创建商品接口

### 接口信息

- **方法：** POST
- **路径：** `/v1/product/products`
- **说明：** 创建新商品，支持上传多张图片

### 请求参数

**Content-Type：** `multipart/form-data`

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|--------|------|
| `name` | string | 是 | 商品名称（1-200字符）|
| `description` | string | 否 | 商品描述 |
| `price` | float | 是 | 商品价格（> 0）|
| `stock` | int | 是 | 库存数量（>= 0）|
| `rental_status` | int | 否 | 租赁状态（0-不可租赁，1-可租赁）|
| `rental_price_single` | float | 否 | 单次租赁价格（> 0）|
| `rental_price_week` | float | 否 | 一周租赁价格（> 0）|
| `rental_price_month` | float | 否 | 一个月租赁价格（> 0）|
| `cover_image` | file | 是 | 封面图片文件（必填）|
| `other_images` | file[] | 否 | 其他图片文件列表 |

### 请求示例

```bash
curl -X POST "http://localhost:8003/v1/product/products" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "name=测试商品" \
  -F "description=这是一个测试商品" \
  -F "price=99.99" \
  -F "stock=100" \
  -F "rental_status=1" \
  -F "rental_price_single=10.00" \
  -F "rental_price_week=50.00" \
  -F "rental_price_month=150.00" \
  -F "cover_image=@/tmp/cover.jpg" \
  -F "other_images=@/tmp/image1.jpg" \
  -F "other_images=@/tmp/image2.jpg"
```

### 响应示例

**成功响应（201 Created）：**
```json
{
  "code": 0,
  "message": "创建商品成功",
  "data": {
    "product": {
      "id": 1,
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "测试商品",
      "description": "这是一个测试商品",
      "price": 99.99,
      "stock": 100,
      "cover_image": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
      "rental_status": 1,
      "rental_price_single": 10.00,
      "rental_price_week": 50.00,
      "rental_price_month": 150.00,
      "status": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    "images": [
      {
        "url": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
        "is_cover": true,
        "sort_order": 0
      },
      {
        "url": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/image_0.jpg",
        "is_cover": false,
        "sort_order": 0
      },
      {
        "url": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/image_1.jpg",
        "is_cover": false,
        "sort_order": 1
      }
    ]
  }
}
```

**失败响应（400 Bad Request）：**
```json
{
  "error": "上传封面图片失败：文件大小超过限制",
  "status_code": 400,
  "path": "/v1/product/products"
}
```

### 事务说明

创建商品接口支持事务管理和回滚机制：

1. **事务流程：**
   - 生成商品唯一标识（UUID）
   - 上传封面图片到云存储
   - 上传其他图片到云存储
   - 保存商品信息到数据库
   - 保存图片信息到数据库

2. **回滚机制：**
   - 如果任何步骤失败，自动回滚所有操作
   - 已上传的图片会自动从云存储删除
   - 数据库事务自动回滚

3. **数据一致性：**
   - 云存储和数据库数据必须一起成功或一起失败
   - 确保不会出现图片已上传但数据库未保存的情况

## 查询商品信息接口

### 接口信息

- **方法：** GET
- **路径：** `/v1/product/products/{product_id}`
- **说明：** 根据商品ID查询商品详情

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|--------|------|
| `product_id` | string | 是 | 商品唯一标识 |

### 响应示例

**成功响应（200 OK）：**
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "product": {
      "id": 1,
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "测试商品",
      "description": "这是一个测试商品",
      "price": 99.99,
      "stock": 100,
      "cover_image": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
      "rental_status": 1,
      "rental_price_single": 10.00,
      "rental_price_week": 50.00,
      "rental_price_month": 150.00,
      "status": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    "images": [
      {
        "id": 1,
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "image_url": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
        "is_cover": true,
        "sort_order": 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
      }
    ]
  }
}
```

**失败响应（404 Not Found）：**
```json
{
  "error": "商品不存在",
  "status_code": 404,
  "path": "/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
}
```

## 查询商品列表接口

### 接口信息

- **方法：** GET
- **路径：** `/v1/product/products`
- **说明：** 查询商品列表，支持分页和状态过滤

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|--------|------|
| `skip` | int | 否 | 跳过的记录数（分页），默认 0 |
| `limit` | int | 否 | 返回的最大记录数，默认 100 |
| `product_status` | int | 否 | 商品状态过滤（0-下架，1-上架）|

### 响应示例

**成功响应（200 OK）：**
```json
{
  "code": 0,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "测试商品",
      "description": "这是一个测试商品",
      "price": 99.99,
      "stock": 100,
      "cover_image": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
      "status": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 100
}
```

## 更新商品信息接口

### 接口信息

- **方法：** PUT
- **路径：** `/v1/product/products/{product_id}`
- **说明：** 更新指定商品的基本信息

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|--------|------|
| `product_id` | string | 是 | 商品唯一标识 |

### 请求体

```json
{
  "name": "更新后的商品名称",
  "description": "更新后的商品描述",
  "price": 199.99,
  "stock": 50,
  "rental_status": 1,
  "rental_price_single": 15.00,
  "rental_price_week": 75.00,
  "rental_price_month": 200.00,
  "status": 1
}
```

### 请求示例

```bash
curl -X PUT "http://localhost:8003/v1/product/products/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "更新后的商品名称",
    "description": "更新后的商品描述",
    "price": 199.99,
    "stock": 50,
    "rental_status": 1,
    "rental_price_single": 15.00,
    "rental_price_week": 75.00,
    "rental_price_month": 200.00,
    "status": 1
  }'
```

### 响应示例

**成功响应（200 OK）：**
```json
{
  "code": 0,
  "message": "更新成功",
  "data": {
    "id": 1,
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "更新后的商品名称",
    "description": "更新后的商品描述",
    "price": 199.99,
    "stock": 50,
    "cover_image": "https://xxx.tcb.qcloud.com/product/550e8400-e29b-41d4-a716-446655440000/images/cover.jpg",
    "rental_status": 1,
    "rental_price_single": 15.00,
    "rental_price_week": 75.00,
    "rental_price_month": 200.00,
    "status": 1,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

**失败响应（404 Not Found）：**
```json
{
  "error": "商品不存在",
  "status_code": 404,
  "path": "/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
}
```

## 删除商品接口

### 接口信息

- **方法：** DELETE
- **路径：** `/v1/product/products/{product_id}`
- **说明：** 删除指定商品及其所有图片

**权限要求：**
- 仅超级管理员可以删除商品

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|--------|------|
| `product_id` | string | 是 | 商品唯一标识 |

### 请求示例

```bash
curl -X DELETE "http://localhost:8003/v1/product/products/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 响应示例

**成功响应（204 No Content）：**
```
(无响应体)
```

**失败响应（404 Not Found）：**
```json
{
  "error": "商品不存在",
  "status_code": 404,
  "path": "/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
}
```

**失败响应（403 Forbidden）：**
```json
{
  "error": "只有超级管理员才能执行此操作",
  "status_code": 403,
  "path": "/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
}
```

## 图片上传说明

### 云存储路径

所有商品图片都会上传到腾讯云存储，路径格式为：

```
product/{商品唯一标识}/images/
```

### 图片命名规则

- **封面图片：** `cover.jpg`
- **其他图片：** `image_0.jpg`, `image_1.jpg`, `image_2.jpg`, ...

### 图片类型支持

- **封面图片：** 单张，可选
- **其他图片：** 多张，可选

### 图片大小限制

- 单张图片大小建议不超过 10MB
- 支持的图片格式：JPG、PNG、GIF、WEBP

## 租赁功能说明

### 租赁状态

商品支持租赁功能，通过 `rental_status` 字段控制：

- **0 - 不可租赁：** 商品不支持租赁
- **1 - 可租赁：** 商品支持租赁

### 租赁价格

支持三种租赁方式，每种方式对应不同的价格：

1. **单次租赁（rental_price_single）：**
   - 适合短期使用
   - 价格单位：元/次

2. **一周租赁（rental_price_week）：**
   - 适合中期使用
   - 价格单位：元/周

3. **一个月租赁（rental_price_month）：**
   - 适合长期使用
   - 价格单位：元/月

### 租赁规则

- 只有 `rental_status = 1` 的商品才支持租赁
- 租赁价格必须大于 0
- 三种租赁价格可以单独设置，也可以同时设置
- 如果商品不支持租赁，所有租赁价格应为 null

## 错误处理

### 常见错误

1. **云存储认证失败**
   ```json
   {
     "error": "云存储认证失败：用户名或密码错误",
     "status_code": 400,
     "path": "/v1/product/products"
   }
   ```

2. **上传图片失败**
   ```json
   {
     "error": "上传封面图片失败：文件大小超过限制",
     "status_code": 400,
     "path": "/v1/product/products"
   }
   ```

3. **数据库保存失败**
   ```json
   {
     "error": "创建商品失败：数据库连接失败",
     "status_code": 400,
     "path": "/v1/product/products"
   }
   ```

## 事务回滚机制

### 回滚触发条件

以下情况会触发事务回滚：

1. 云存储认证失败
2. 上传图片失败
3. 数据库保存失败
4. 任何未捕获的异常

### 回滚操作

1. **数据库回滚：**
   - 自动回滚所有数据库操作
   - 不会保存任何商品或图片信息

2. **云存储回滚：**
   - 自动删除已上传的图片
   - 清理临时文件

### 数据一致性保证

- 云存储和数据库数据必须一起成功或一起失败
- 不会出现图片已上传但数据库未保存的情况
- 不会出现数据库已保存但图片未上传的情况

## 完整示例

### 示例 1：创建商品（带图片）

```bash
curl -X POST "http://localhost:8003/v1/product/products" \
  -H "Content-Type: multipart/form-data" \
  -F "name=时尚连衣裙" \
  -F "description=2024新款连衣裙，舒适透气" \
  -F "price=299.99" \
  -F "stock=50" \
  -F "cover_image=@/tmp/cover.jpg" \
  -F "other_images=@/tmp/image1.jpg" \
  -F "other_images=@/tmp/image2.jpg"
```

### 示例 2：查询商品信息

```bash
curl -X GET "http://localhost:8003/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
```

### 示例 3：查询商品列表

```bash
curl -X GET "http://localhost:8003/v1/product/products?skip=0&limit=10&product_status=1"
```

### 示例 4：更新商品信息

```bash
curl -X PUT "http://localhost:8003/v1/product/products/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的商品名称",
    "price": 199.99,
    "stock": 30
  }'
```

### 示例 5：删除商品

```bash
curl -X DELETE "http://localhost:8003/v1/product/products/550e8400-e29b-41d4-a716-446655440000"
```

## 技术栈

- **后端框架：** FastAPI
- **数据库：** MySQL + SQLAlchemy
- **云存储：** 腾讯云存储
- **事务管理：** SQLAlchemy 事务
- **图片上传：** FastAPI UploadFile

## 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [腾讯云存储文档](https://cloud.tencent.com/document/product/583)
