# 实现双Token机制和数据隔离

## 1. 修改认证工具模块 (app/utils/auth\_utils.py)

* 添加 `REFRESH_TOKEN_EXPIRE_MINUTES` 配置（30天）

* 添加 `create_refresh_token()` 函数生成 refresh token

* 添加 `create_tokens()` 函数同时生成 access token 和 refresh token

* 修改 `create_access_token()` 在 payload 中加入角色信息（is\_superuser）

* 添加 `get_current_user_from_refresh_token()` 依赖项验证 refresh token

* 添加 `verify_refresh_token()` 函数

## 2. 修改用户服务层 (app/service/user/user\_service.py)

* 修改 `list_users()` 添加超级管理员权限检查

* 添加 `get_user_by_id_with_permission()` 检查用户是否有权限访问其他用户数据

## 3. 修改用户控制器 (app/controller/api\_v1/user.py)

* 修改 `login` 接口返回 access\_token 和 refresh\_token

* 添加 `refresh_token` 接口（POST /auth/refresh）

* 修改 `get_users_list` 接口，只有超级管理员可以访问

* 修改 `get_user_by_id_endpoint` 接口，普通用户只能查询自己

* 修改 `update_current_user` 接口，普通用户只能更新自己

* `delete``currentuser 改为delete`\_`user` 接口，只有超级管理员可以删除用户

## 4. 修改主应用 (main.py)

* 改进全局异常处理器，添加更详细的错误信息

* 添加 HTTPException 的专门处理器

## 5. 更新依赖 (pyproject.toml)

* 确保包含所有必要的依赖包

## 核心功能

✅ 双Token机制（access token + refresh token）
✅ Token中包含角色信息（is\_superuser）
✅ 数据隔离（普通用户只能访问自己的数据）
✅ 权限控制（只有超级管理员可以获取用户列表）
✅ 统一错误处理和响应格式
