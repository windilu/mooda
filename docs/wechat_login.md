# 微信授权登录功能文档

## 功能概述

本系统支持两种登录方式：
1. **密码登录** - 用户名 + 密码
2. **微信授权登录** - 微信 OpenID + 授权

## 微信授权登录流程

### 流程图

```
前端 → 后端：获取微信授权 URL
后端 → 前端：返回授权 URL
前端 → 微信：跳转到授权页面
微信 → 用户：点击"授权"
微信 → 后端：重定向到回调地址（带 code）
后端 → 微信 API：使用 code 换取 access_token 和 openid
后端 → 微信 API：使用 access_token 获取用户信息
后端 → 数据库：根据 openid 查找或创建用户
后端 → 前端：返回 JWT token 和用户信息
```

### 详细步骤

#### 1. 前端获取微信授权 URL

**接口：** `GET /api/v1/auth/wechat/auth`

**请求参数：**
- `state`（可选）：用于防止 CSRF 攻击的状态参数，默认为 "STATE"

**响应示例：**
```json
{
  "code": 0,
  "message": "获取微信授权 URL 成功",
  "data": {
    "auth_url": "https://open.weixin.qq.com/connect/oauth2/authorize?appid=xxx&redirect_uri=xxx&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect"
  }
}
```

**前端处理：**
```javascript
// 前端调用后端获取授权 URL
const response = await fetch('/api/v1/auth/wechat/auth?state=STATE');
const { auth_url } = await response.json();

// 跳转到微信授权页面
window.location.href = auth_url;
```

#### 2. 用户在微信页面授权

用户在微信页面点击"授权"按钮。

#### 3. 微信重定向到回调地址

微信授权成功后，会重定向到回调地址，带上 `code` 参数。

**回调地址：** `http://your-domain.com/api/v1/auth/wechat/callback?code=CODE`

#### 4. 后端处理授权回调

**接口：** `GET /api/v1/auth/wechat/callback`

**请求参数：**
- `code`（必填）：微信授权后返回的 code

**后端处理流程：**
1. 使用 code 调用微信 API 获取 access_token 和 openid
2. 使用 access_token 调用微信 API 获取用户信息
3. 根据 openid 查找数据库中的用户
4. 如果用户不存在，则创建新用户
5. 如果用户存在，则更新用户信息
6. 生成 JWT token（access_token + refresh_token）
7. 返回 token 和用户信息

**响应示例：**
```json
{
  "code": 0,
  "message": "微信登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "wx_abc123...",
      "email": "abc123...@wechat.local",
      "nickname": "微信昵称",
      "avatar": "微信头像URL",
      "status": 1,
      "is_superuser": false,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  }
}
```

#### 5. 前端存储 token 并跳转

**前端处理：**
```javascript
// 前端接收 token 和用户信息
const { access_token, refresh_token, user } = data;

// 存储 token 到 localStorage
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// 存储用户信息
localStorage.setItem('user', JSON.stringify(user));

// 跳转到首页
window.location.href = '/';
```

## 前端直接处理微信授权 code

如果前端已经获取了微信授权的 code，可以直接调用登录接口。

**接口：** `POST /api/v1/auth/wechat/login`

**请求参数：**
```json
{
  "code": "WECHAT_AUTH_CODE"
}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "微信登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "wx_abc123...",
      "email": "abc123...@wechat.local",
      "nickname": "微信昵称",
      "avatar": "微信头像URL",
      "status": 1,
      "is_superuser": false,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  }
}
```

## 数据库设计

### users 表新增字段

| 字段名 | 类型 | 说明 |
|---------|------|------|
| `wechat_openid` | VARCHAR(100) | 微信 OpenID（唯一） |
| `wechat_unionid` | VARCHAR(100) | 微信 UnionID（跨应用唯一） |
| `wechat_nickname` | VARCHAR(100) | 微信昵称 |
| `wechat_avatar` | VARCHAR(255) | 微信头像 |
| `login_type` | VARCHAR(20) | 登录类型（password/wechat） |

### 数据库迁移 SQL

```sql
-- 添加微信相关字段
ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(100) UNIQUE COMMENT '微信OpenID';
ALTER TABLE users ADD COLUMN wechat_unionid VARCHAR(100) COMMENT '微信UnionID';
ALTER TABLE users ADD COLUMN wechat_nickname VARCHAR(100) COMMENT '微信昵称';
ALTER TABLE users ADD COLUMN wechat_avatar VARCHAR(255) COMMENT '微信头像';
ALTER TABLE users ADD COLUMN login_type VARCHAR(20) DEFAULT 'password' COMMENT '登录类型：password/wechat';

-- 添加索引
CREATE INDEX idx_wechat_openid ON users(wechat_openid);
```

## 环境变量配置

在项目根目录创建 `.env` 文件，配置微信相关参数：

```env
# 微信开放平台配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_REDIRECT_URI=http://localhost:8003/api/v1/auth/wechat/callback
```

### 获取微信 AppID 和 AppSecret

1. 访问 [微信开放平台](https://open.weixin.qq.com/)
2. 登录并创建应用
3. 在应用详情页面获取 `AppID` 和 `AppSecret`
4. 配置授权回调域名

### 配置授权回调域名

1. 在微信开放平台的"网页授权"页面
2. 配置授权回调域名（如：`your-domain.com`）
3. 授权回调地址必须与 `WECHAT_REDIRECT_URI` 一致

## API 接口列表

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|--------|
| GET | `/api/v1/auth/wechat/auth` | 获取微信授权 URL | 无 |
| GET | `/api/v1/auth/wechat/callback` | 微信授权回调 | 无 |
| POST | `/api/v1/auth/wechat/login` | 微信登录（前端调用） | 无 |
| POST | `/api/v1/auth/register` | 用户注册 | 无 |
| POST | `/api/v1/auth/login` | 用户登录 | 无 |
| POST | `/api/v1/auth/refresh` | 刷新 token | refresh token |
| GET | `/api/v1/users/me` | 获取当前用户 | access token |
| GET | `/api/v1/users/{user_id}` | 查询用户信息 | access token |
| GET | `/api/v1/users` | 查询用户列表 | access token + 超级管理员 |
| PUT | `/api/v1/users/me` | 更新当前用户 | access token |
| PUT | `/api/v1/users/{user_id}` | 更新指定用户 | access token + 超级管理员 |
| DELETE | `/api/v1/users/{user_id}` | 删除用户 | access token + 超级管理员 |

## 错误处理

### 微信授权失败

**错误码：** 400 Bad Request

**错误示例：**
```json
{
  "error": "微信授权失败：invalid code",
  "message": "微信授权失败：invalid code",
  "status_code": 400,
  "path": "/api/v1/auth/wechat/callback"
}
```

### 账号被禁用

**错误码：** 403 Forbidden

**错误示例：**
```json
{
  "error": "账号已被禁用",
  "message": "账号已被禁用",
  "status_code": 403,
  "path": "/api/v1/auth/wechat/callback"
}
```

## 安全注意事项

1. **CSRF 防护**
   - 使用 `state` 参数防止 CSRF 攻击
   - 前端生成随机 state，后端验证

2. **Token 安全**
   - Access token 有效期：7 天
   - Refresh token 有效期：30 天
   - Token 存储在 localStorage 中

3. **用户隐私**
   - 微信 OpenID 是用户在当前应用下的唯一标识
   - 微信 UnionID 是用户在同一开放平台下的唯一标识
   - 不存储微信敏感信息

## 测试流程

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入微信 AppID 和 AppSecret
vim .env
```

### 2. 启动服务

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### 3. 测试微信授权登录

```bash
# 1. 获取微信授权 URL
curl http://localhost:8003/api/v1/auth/wechat/auth?state=TEST_STATE

# 2. 在浏览器中打开返回的 auth_url
# 3. 在微信页面点击"授权"
# 4. 微信会重定向到回调地址，完成登录
```

## 常见问题

### Q1: 微信授权回调地址配置错误？

**A:** 确保在微信开放平台配置的授权回调域名与 `WECHAT_REDIRECT_URI` 一致。

### Q2: 微信授权 code 无效？

**A:** code 有效期为 10 分钟，且只能使用一次。请重新获取授权 URL。

### Q3: 如何区分密码登录和微信登录？

**A:** 通过 `login_type` 字段区分：
- `password` - 密码登录
- `wechat` - 微信登录

### Q4: 微信用户首次登录如何处理？

**A:** 系统会自动创建新用户：
- 用户名：`wx_{openid[:20]}`
- 邮箱：`{openid}@wechat.local`
- 密码：空（微信登录不需要密码）
- 登录类型：`wechat`

## 技术栈

- **后端框架：** FastAPI
- **数据库：** MySQL + SQLAlchemy
- **认证：** JWT (access token + refresh token)
- **密码加密：** Argon2
- **HTTP 客户端：** httpx
- **微信 API：** OAuth2.0 授权

## 参考资料

- [微信开放平台文档](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
- [微信网页授权文档](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
