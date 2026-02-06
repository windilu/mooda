"""
用户控制器模块

本模块提供了用户相关的 API 接口，包括：
- 用户注册（无需 token）
- 用户登录（无需 token）
- Token 刷新（需要 refresh token）
- 用户信息查询（需要 token，带数据隔离）
- 用户信息更新（需要 token，带数据隔离）
- 用户删除（需要 token，只有超级管理员）
- 微信授权登录（无需 token）

所有接口遵循 RESTful 风格，使用正确的 HTTP 状态码。
权限校验使用装饰器，响应处理在 controller 层。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr

from app.utils.auth_utils import (
    create_access_token,
    create_refresh_token,
    create_tokens,
    authenticate_user,
    get_current_user,
    get_current_user_from_refresh_token
)
from app.service.user.user_service import (
    create_user,
    get_user_by_id,
    list_users,
    count_users,
    update_user,
    delete_user
)
from app.utils.wechat_utils import wechat_login, get_wechat_auth_url
from app.models.user_model import User
from app.models.response_models import success_response, paginated_response


router = APIRouter()

refresh_token_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/refresh")


class UserRegisterRequest(BaseModel):
    """
    用户注册请求模型

    属性:
        username: 用户名
        password: 密码
        email: 邮箱
        phone: 手机号（可选）
        nickname: 昵称（可选）
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")


class UserLoginRequest(BaseModel):
    """
    用户登录请求模型

    属性:
        username: 用户名
        password: 密码
    """
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdateRequest(BaseModel):
    """
    用户更新请求模型

    属性:
        email: 邮箱（可选）
        phone: 手机号（可选）
        nickname: 昵称（可选）
        avatar: 头像URL（可选）
        account_status: 账号状态（可选）
    """
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    account_status: Optional[int] = Field(None, ge=0, le=1, description="账号状态：0-禁用，1-启用")


class WechatAuthRequest(BaseModel):
    """
    微信授权请求模型

    属性:
        state: 用于防止 CSRF 攻击的状态参数
    """
    state: Optional[str] = Field("STATE", description="状态参数")


class WechatCallbackRequest(BaseModel):
    """
    微信回调请求模型

    属性:
        code: 微信授权后返回的 code
        state: 状态参数
    """
    code: str = Field(..., description="微信授权 code")
    state: Optional[str] = Field(None, description="状态参数")


class WechatLoginRequest(BaseModel):
    """
    微信登录请求模型

    属性:
        code: 微信授权后返回的 code
    """
    code: str = Field(..., description="微信授权 code")


class UserResponse(BaseModel):
    """
    用户响应模型

    属性:
        id: 用户ID
        username: 用户名
        email: 邮箱
        phone: 手机号
        nickname: 昵称
        avatar: 头像URL
        status: 账号状态
        is_superuser: 是否超级管理员
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    username: str
    email: str
    phone: Optional[str]
    nickname: Optional[str]
    avatar: Optional[str]
    status: int
    is_superuser: bool
    created_at: Optional[str]
    updated_at: Optional[str]


def user_to_response(user: User) -> UserResponse:
    """
    将用户模型转换为响应模型

    参数:
        user: 用户模型对象

    返回:
        UserResponse: 用户响应对象
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar=user.avatar,
        status=user.status,
        is_superuser=user.is_superuser,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="用户注册", description="注册新用户")
async def register(request: UserRegisterRequest):
    """
    用户注册接口

    创建新用户账号，无需 token 认证。
    用户名和邮箱必须唯一，密码会自动哈希加密。

    参数:
        request: 注册请求信息

    返回:
        dict: 包含用户信息的响应

    HTTP 状态码:
        201 Created - 注册成功

    异常:
        HTTPException: 用户名或邮箱已存在时抛出（400 Bad Request）
    """
    result = await create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        phone=request.phone,
        nickname=request.nickname
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=user_to_response(result["data"]), message="注册成功")


@router.post("/auth/login", summary="用户登录", description="用户登录获取双token")
async def login(request: UserLoginRequest):
    """
    用户登录接口

    验证用户名和密码，返回 access token 和 refresh token。
    无需 token 认证。

    参数:
        request: 登录请求信息

    返回:
        dict: 包含 access_token 和 refresh_token

    HTTP 状态码:
        200 OK - 登录成功

    异常:
        HTTPException: 用户名或密码错误时抛出（401 Unauthorized）
        HTTPException: 账号被禁用时抛出（403 Forbidden）
    """
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if user.status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    tokens = create_tokens(data={"sub": user.username})
    return success_response(
        data={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user": user_to_response(user)
        },
        message="登录成功"
    )


@router.post("/auth/refresh", summary="刷新访问令牌", description="使用 refresh token 获取新的 access token")
async def refresh_token(current_user: User = Depends(get_current_user_from_refresh_token)):
    """
    刷新 access token 接口

    使用 refresh token 获取新的 access token。
    需要在请求头中携带有效的 refresh token。

    参数:
        current_user: 当前登录用户（从 refresh token 解析）

    返回:
        dict: 包含新的 access_token

    HTTP 状态码:
        200 OK - 刷新成功

    异常:
        HTTPException: refresh token 无效时抛出（401 Unauthorized）
    """
    new_access_token = create_access_token(data={"sub": current_user.username})
    return success_response(
        data={
            "access_token": new_access_token,
            "token_type": "bearer"
        },
        message="刷新成功"
    )


@router.get("/users/me", summary="获取当前用户信息", description="获取当前登录用户的信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息接口

    需要在请求头中携带有效的 JWT access token。
    返回当前登录用户的详细信息。

    参数:
        current_user: 当前登录用户（从 access token 解析）

    返回:
        dict: 包含用户信息的响应

    HTTP 状态码:
        200 OK - 查询成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
    """
    return success_response(data=user_to_response(current_user))


@router.get("/users/{user_id}", summary="查询用户信息", description="根据 ID 查询用户信息（带权限控制）")
async def get_user_by_id_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    查询用户信息接口（带权限控制）

    需要在请求头中携带有效的 JWT access token。
    普通用户只能查询自己的信息，超级管理员可以查询所有用户。

    参数:
        user_id: 要查询的用户 ID
        current_user: 当前登录用户（从 access token 解析）

    返回:
        dict: 包含用户信息的响应

    HTTP 状态码:
        200 OK - 查询成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
        HTTPException: 无权限时抛出（403 Forbidden）
        HTTPException: 用户不存在时抛出（404 Not Found）
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问其他用户信息"
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return success_response(data=user_to_response(user))


@router.get("/users", summary="查询用户列表", description="查询用户列表（仅超级管理员）")
async def get_users_list(
    skip: int = 0,
    limit: int = 100,
    account_status: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    查询用户列表接口（仅超级管理员）

    需要在请求头中携带有效的 JWT access token。
    只有超级管理员可以查询用户列表。
    支持分页和状态过滤。

    参数:
        skip: 跳过的记录数（分页）
        limit: 返回的最大记录数
        account_status: 账号状态过滤（0-禁用，1-启用）
        current_user: 当前登录用户（从 access token 解析）

    返回:
        dict: 包含用户列表的响应

    HTTP 状态码:
        200 OK - 查询成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
        HTTPException: 无权限时抛出（403 Forbidden）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以查询用户列表"
        )

    users = await list_users(skip=skip, limit=limit, status=account_status)
    total = await count_users(status=account_status)
    page = skip // limit + 1 if limit > 0 else 1

    return paginated_response(
        data=[user_to_response(user) for user in users],
        total=total,
        page=page,
        page_size=limit
    )


@router.put("/users/me", summary="更新当前用户信息", description="更新当前登录用户的信息")
async def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户信息接口

    需要在请求头中携带有效的 JWT access token。
    只能更新当前登录用户的信息。

    参数:
        request: 更新请求信息
        current_user: 当前登录用户（从 access token 解析）

    返回:
        dict: 包含更新后用户信息的响应

    HTTP 状态码:
        200 OK - 更新成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
        HTTPException: 用户不存在时抛出（404 Not Found）
    """
    result = await update_user(
        user_id=current_user.id,
        email=request.email,
        phone=request.phone,
        nickname=request.nickname,
        avatar=request.avatar,
        status=request.account_status
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=user_to_response(result["data"]), message="更新成功")


@router.put("/users/{user_id}", summary="更新指定用户信息", description="更新指定用户信息（仅超级管理员）")
async def update_user_by_id(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    更新指定用户信息接口（仅超级管理员）

    需要在请求头中携带有效的 JWT access token。
    只有超级管理员可以更新其他用户的信息。

    参数:
        user_id: 要更新的用户 ID
        request: 更新请求信息
        current_user: 当前登录用户（从 access token 解析）

    返回:
        dict: 包含更新后用户信息的响应

    HTTP 状态码:
        200 OK - 更新成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
        HTTPException: 无权限时抛出（403 Forbidden）
        HTTPException: 用户不存在时抛出（404 Not Found）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以更新其他用户信息"
        )

    result = await update_user(
        user_id=user_id,
        email=request.email,
        phone=request.phone,
        nickname=request.nickname,
        avatar=request.avatar,
        status=request.account_status
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=user_to_response(result["data"]), message="更新成功")


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除指定用户", description="删除指定用户（仅超级管理员）")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    删除指定用户接口（仅超级管理员）

    需要在请求头中携带有效的 JWT access token。
    只有超级管理员可以删除用户。

    参数:
        user_id: 要删除的用户 ID
        current_user: 当前登录用户（从 access token 解析）

    HTTP 状态码:
        204 No Content - 删除成功

    异常:
        HTTPException: token 无效时抛出（401 Unauthorized）
        HTTPException: 无权限时抛出（403 Forbidden）
        HTTPException: 用户不存在时抛出（404 Not Found）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除用户"
        )

    result = await delete_user(user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )


@router.get("/auth/wechat/auth", summary="获取微信授权 URL", description="获取微信授权页面 URL")
async def get_wechat_auth_endpoint(state: str = Query("STATE", description="状态参数")):
    """
    获取微信授权 URL 接口

    前端调用此接口获取微信授权 URL，然后跳转到该 URL。
    用户在微信页面点击"授权"后，微信会重定向到回调地址。

    参数:
        state: 用于防止 CSRF 攻击的状态参数

    返回:
        dict: 包含微信授权 URL 的响应

    HTTP 状态码:
        200 OK - 成功

    微信授权流程：
        1. 前端调用此接口获取微信授权 URL
        2. 前端跳转到微信授权页面
        3. 用户在微信页面点击"授权"
        4. 微信重定向到回调地址，带上 code 参数
        5. 前端调用 /auth/wechat/callback 处理回调
    """
    auth_url = get_wechat_auth_url(state)
    return success_response(data={"auth_url": auth_url}, message="获取微信授权 URL 成功")


@router.get("/auth/wechat/callback", summary="微信授权回调", description="处理微信授权回调")
async def wechat_callback(code: str = Query(..., description="微信授权 code")):
    """
    微信授权回调接口

    微信授权成功后会重定向到此接口，带上 code 参数。
    此接口处理授权回调，完成登录流程。

    参数:
        code: 微信授权后返回的 code

    返回:
        dict: 包含 access_token、refresh_token 和用户信息的响应

    HTTP 状态码:
        200 OK - 登录成功
        400 Bad Request - 微信授权失败
        403 Forbidden - 账号已被禁用

    微信授权流程：
        1. 用户在微信页面点击"授权"
        2. 微信重定向到此接口，带上 code 参数
        3. 后端使用 code 换取 access_token 和 openid
        4. 后端使用 access_token 获取用户信息
        5. 后端根据 openid 查找或创建用户
        6. 后端生成 JWT token
        7. 后端返回 token 和用户信息
    """
    result = await wechat_login(code)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=result["data"], message="微信登录成功")


@router.post("/auth/wechat/login", summary="微信登录", description="使用微信授权 code 登录")
async def wechat_login_endpoint(request: WechatLoginRequest):
    """
    微信登录接口

    前端调用此接口，使用微信授权 code 完成登录。
    此接口适用于前端直接处理微信授权后的 code 的情况。

    参数:
        request: 微信登录请求信息，包含 code

    返回:
        dict: 包含 access_token、refresh_token 和用户信息的响应

    HTTP 状态码:
        200 OK - 登录成功
        400 Bad Request - 微信授权失败
        403 Forbidden - 账号已被禁用

    微信授权流程：
        1. 前端获取微信授权 code
        2. 前端调用此接口，传入 code
        3. 后端使用 code 换取 access_token 和 openid
        4. 后端使用 access_token 获取用户信息
        5. 后端根据 openid 查找或创建用户
        6. 后端生成 JWT token
        7. 后端返回 token 和用户信息
    """
    result = await wechat_login(request.code)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=result["data"], message="微信登录成功")
