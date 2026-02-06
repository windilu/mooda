"""
认证配置模块

本模块提供了认证相关的配置和工具函数，包括：
- JWT token 配置
- 密码加密和验证
- Token 生成和验证（双Token机制：access token + refresh token）
- FastAPI 依赖项（获取当前用户）
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.mode.config.config import MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_CHARSET, MYSQL_USER
from app.utils.mysql_utils import mysql_client
from app.models.user_model import User


JWT_SECRET_KEY = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30天

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=8
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    使用 Argon2 算法验证明文密码和哈希密码是否匹配。
    Argon2 是现代、安全的密码哈希算法，没有长度限制。

    参数:
        plain_password: 明文密码
        hashed_password: 哈希密码

    返回:
        bool: 密码匹配返回 True，否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    使用 Argon2 算法对密码进行哈希加密。
    Argon2 是现代、安全的密码哈希算法，没有长度限制。

    参数:
        password: 明文密码

    返回:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT 访问令牌

    将用户数据编码为 JWT token。
    在 payload 中包含角色信息（is_superuser）。

    参数:
        data: 要编码的数据（通常包含用户名和角色）
        expires_delta: 过期时间增量，默认使用配置的过期时间

    返回:
        str: JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    生成 JWT 刷新令牌

    将用户数据编码为 refresh token。
    Refresh token 的过期时间比 access token 长。

    参数:
        data: 要编码的数据（通常包含用户名）

    返回:
        str: JWT token 字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_tokens(data: dict) -> dict:
    """
    同时生成 access token 和 refresh token

    参数:
        data: 要编码的数据（通常包含用户名和角色）

    返回:
        dict: 包含 access_token 和 refresh_token
    """
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data)
    }


async def get_user_by_username(username: str) -> Optional[User]:
    """
    根据用户名查询用户

    参数:
        username: 用户名

    返回:
        Optional[User]: 用户对象，如果不存在返回 None
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    获取当前登录用户

    FastAPI 依赖项，从 JWT token 中解析用户信息。
    如果 token 无效或用户不存在，抛出 HTTPException。

    参数:
        token: JWT token（从 Authorization header 自动获取）

    返回:
        User: 当前登录的用户对象

    异常:
        HTTPException: token 无效或用户不存在时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
     
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None:
            raise credentials_exception
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无权访问"
            )
            
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


async def get_current_user_from_refresh_token(token: str) -> User:
    """
    从 refresh token 获取用户

    验证 refresh token 并返回用户对象。

    参数:
        token: refresh token

    返回:
        User: 用户对象

    异常:
        HTTPException: token 无效或用户不存在时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的 refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None:
            raise credentials_exception
            
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的 token 类型"
            )
            
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    用户认证

    验证用户名和密码是否正确。

    参数:
        username: 用户名
        password: 明文密码

    返回:
        Optional[User]: 认证成功返回用户对象，失败返回 None
    """
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
