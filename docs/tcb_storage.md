# 腾讯云存储工具模块文档

## 功能概述

本模块提供了腾讯云存储服务的完整封装，包括：
- 自动认证管理（自动获取和刷新 token）
- 基础的增删改查接口
- Token 自动刷新机制
- 批量操作支持

所有接口都会自动处理 token 认证，确保有权限访问。

## 核心类：TCBStorageClient

### 初始化

```python
from app.utils.tcb_utils.tcb_storages import TCBStorageClient

client = TCBStorageClient()
```

### 自动认证机制

`TCBStorageClient` 类实现了自动认证机制：

1. **首次使用**：自动调用登录接口获取 token
2. **Token 缓存**：token 信息自动缓存到 Redis
3. **Token 刷新**：token 即将过期时自动刷新
4. **Redis 优先**：优先从 Redis 加载缓存的 token

### API 接口列表

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `upload_file()` | 上传文件 | cloud_path, file/local_path, on_progress | Dict |
| `download_file()` | 下载文件 | cloud_path, local_path, on_progress | Dict |
| `delete_file()` | 删除文件 | cloud_path | Dict |
| `list_files()` | 列出文件 | cloud_path, limit | Dict |
| `get_file_info()` | 获取文件信息 | cloud_path | Dict |
| `close()` | 关闭客户端 | 无 | None |

**上传文件参数说明：**
- `upload_file()` 支持 `file`（文件对象）和 `local_path`（本地文件路径）两种方式，二选一

### 核心方法

#### 1. 上传文件

```python
# 方式1：上传文件对象
from io import BytesIO

file_content = b"file content"
file_obj = BytesIO(file_content)

result = await client.upload_file(
    cloud_path="images/photo.jpg",
    file=file_obj
)

if result["success"]:
    print("上传成功", result["data"])
else:
    print("上传失败", result["error"])

# 方式2：上传本地文件
result = await client.upload_file(
    cloud_path="images/photo.jpg",
    local_path="/tmp/photo.jpg"
)

if result["success"]:
    print("上传成功", result["data"])
else:
    print("上传失败", result["error"])
```

**参数：**
- `cloud_path`: 云端文件路径（如：`images/photo.jpg`）
- `file`: 文件对象（如 BytesIO、文件对象），与 `local_path` 二选一
- `local_path`: 本地文件路径（绝对路径），与 `file` 二选一
- `on_progress`: 上传进度回调函数（可选）

**返回：**
```python
{
    "success": True,
    "data": {
        "url": "https://xxx.tcb.qcloud.com/xxx"
    }
}
```

#### 2. 下载文件

```python
result = await client.download_file(
    cloud_path="images/photo.jpg",
    local_path="/tmp/photo.jpg"
)

if result["success"]:
    print("下载成功", result["data"])
else:
    print("下载失败", result["error"])
```

**参数：**
- `cloud_path`: 云端文件路径（如：`images/photo.jpg`）
- `local_path`: 本地保存路径（绝对路径）
- `on_progress`: 下载进度回调函数（可选）

**返回：**
```python
{
    "success": True,
    "data": {
        "local_path": "/tmp/photo.jpg"
    }
}
```

#### 3. 删除文件

```python
result = await client.delete_file(cloud_path="images/photo.jpg")

if result["success"]:
    print("删除成功")
else:
    print("删除失败", result["error"])
```

**参数：**
- `cloud_path`: 云端文件路径（如：`images/photo.jpg`）

**返回：**
```python
{
    "success": True,
    "data": {}
}
```

#### 4. 列出文件

```python
result = await client.list_files(cloud_path="images/", limit=100)

if result["success"]:
    print("文件列表", result["data"])
else:
    print("列出文件失败", result["error"])
```

**参数：**
- `cloud_path`: 云端文件路径（默认为根目录）
- `limit`: 返回的最大文件数

**返回：**
```python
{
    "success": True,
    "data": {
        "files": [...]
    }
}
```

#### 5. 获取文件信息

```python
result = await client.get_file_info(cloud_path="images/photo.jpg")

if result["success"]:
    print("文件信息", result["data"])
else:
    print("获取文件信息失败", result["error"])
```

**参数：**
- `cloud_path`: 云端文件路径（如：`images/photo.jpg`）

**返回：**
```python
{
    "success": True,
    "data": {
        "name": "photo.jpg",
        "size": 1024,
        "url": "https://xxx.tcb.qcloud.com/xxx"
    }
}
```

#### 7. 关闭客户端

```python
await client.close()
```

**说明：** 关闭 HTTP 客户端，释放资源。

## 辅助函数

### 1. tcb_base_storages_signin()

腾讯云存储登录验证（兼容旧接口）。

```python
from app.utils.tcb_utils.tcb_storages import tcb_base_storages_signin

await tcb_base_storages_signin()
```

### 2. tcb_base_storages_refresh_token(refresh_token)

刷新腾讯云存储 token（兼容旧接口）。

```python
from app.utils.tcb_utils.tcb_storages import tcb_base_storages_refresh_token

await tcb_base_storages_refresh_token("your_refresh_token")
```

### 3. get_tcb_storage_client()

获取腾讯云存储客户端实例。

```python
from app.utils.tcb_utils.tcb_storages import get_tcb_storage_client

client = await get_tcb_storage_client()
result = await client.upload_file("images/photo.jpg", "/tmp/photo.jpg")
```

## 完整示例

### 示例 1：上传并下载文件

```python
from app.utils.tcb_utils.tcb_storages import TCBStorageClient
from io import BytesIO

async def upload_and_download():
    client = TCBStorageClient()
    
    try:
        # 方式1：上传文件对象
        file_content = b"file content"
        file_obj = BytesIO(file_content)
        
        upload_result = await client.upload_file(
            cloud_path="documents/report.pdf",
            file=file_obj
        )
        
        if not upload_result["success"]:
            print("上传失败", upload_result["error"])
            return
        
        print("上传成功", upload_result["data"])
        
        # 方式2：上传本地文件
        upload_result = await client.upload_file(
            cloud_path="documents/report.pdf",
            local_path="/tmp/report.pdf"
        )
        
        if not upload_result["success"]:
            print("上传失败", upload_result["error"])
            return
        
        print("上传成功", upload_result["data"])
        
        # 下载文件
        download_result = await client.download_file(
            cloud_path="documents/report.pdf",
            local_path="/tmp/downloaded_report.pdf"
        )
        
        if not download_result["success"]:
            print("下载失败", download_result["error"])
            return
        
        print("下载成功", download_result["data"])
        
    finally:
        await client.close()

# 运行
import asyncio
asyncio.run(upload_and_download())
```

### 示例 3：列出并删除文件

```python
from app.utils.tcb_utils.tcb_storages import TCBStorageClient

async def list_and_delete():
    client = TCBStorageClient()
    
    try:
        # 列出文件
        list_result = await client.list_files(cloud_path="images/", limit=100)
        
        if not list_result["success"]:
            print("列出文件失败", list_result["error"])
            return
        
        files = list_result["data"].get("files", [])
        print("文件列表", files)
        
        # 删除所有文件
        if files:
            for file in files:
                path = file["path"]
                delete_result = await client.delete_file(cloud_path=path)
                
                if delete_result["success"]:
                    print(f"删除成功：{path}")
                else:
                    print(f"删除失败：{path}", delete_result["error"])
        
    finally:
        await client.close()

# 运行
import asyncio
asyncio.run(list_and_delete())
```

## 环境变量配置

在项目根目录的 `.env` 文件中配置腾讯云存储相关参数：

```env
# 腾讯云存储配置
TCB_USER_NAME=your_tcb_username
TCB_USER_SECRET=your_tcb_password
```

### 获取用户名和密码

1. 访问 [腾讯云开发平台](https://console.cloud.tencent.com/tcb)
2. 登录并创建环境
3. 在环境详情页面获取用户名和密码

## 认证流程

### 1. 首次登录

```
客户端 → 腾讯云：发送登录请求
腾讯云 → 客户端：返回 access_token 和 refresh_token
客户端 → Redis：缓存 token 信息
```

### 2. 后续请求

```
客户端 → Redis：尝试加载缓存的 token
Redis → 客户端：返回 token 信息
客户端 → 腾讯云：使用 token 发送请求
```

### 3. Token 刷新

```
客户端 → 检查 token 是否过期
客户端 → 腾讯云：使用 refresh_token 刷新 token
腾讯云 → 客户端：返回新的 token
客户端 → Redis：更新缓存的 token
```

## 错误处理

所有接口都返回统一的错误格式：

```python
{
    "success": False,
    "error": "错误详情"
}
```

### 常见错误

1. **认证失败**
   - 检查 `TCB_USER_NAME` 和 `TCB_USER_SECRET` 是否正确
   - 检查网络连接是否正常

2. **Token 过期**
   - 客户端会自动刷新 token，无需手动处理

3. **文件不存在**
   - 检查 `cloud_path` 是否正确
   - 使用 `list_files()` 查看实际文件路径

4. **权限不足**
   - 检查用户是否有权限访问指定路径

## 性能优化

1. **HTTP 客户端复用**
   - 客户端会自动复用 HTTP 连接，减少连接开销

2. **Token 缓存**
   - token 信息缓存到 Redis，减少登录请求

3. **批量操作**
   - 使用批量上传和批量删除接口，提高效率

## 安全注意事项

1. **Token 安全**
   - Token 信息存储在 Redis 中，设置过期时间
   - 不要在代码中硬编码用户名和密码

2. **文件安全**
   - 不要上传敏感文件
   - 使用 HTTPS 协议访问文件

3. **网络安全**
   - 使用 HTTPS 协议访问腾讯云 API
   - 验证服务器证书

## 技术栈

- **HTTP 客户端：** httpx（异步）
- **缓存：** Redis
- **认证方式：** Bearer Token
- **API 版本：** v1

## 参考资料

- [腾讯云开发平台](https://console.cloud.tencent.com/tcb)
- [腾讯云存储文档](https://cloud.tencent.com/document/product/583)
- [httpx 官方文档](https://www.python-httpx.org/)
- [Redis 官方文档](https://redis.io/documentation)
