"""
用户服务层模块

本模块提供了用户相关的业务逻辑，包括：
- 用户注册
- 用户信息查询
- 用户信息更新
- 用户删除
- 微信授权登录

服务层只处理业务逻辑，不处理 HTTP 相关和权限检查。
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.mysql_utils import mysql_client
from app.models.user_model import User
from app.utils.auth_utils import get_password_hash


async def create_user(
    username: str,
    password: str,
    email: str,
    phone: Optional[str] = None,
    nickname: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建新用户

    将用户信息保存到数据库，密码会自动哈希加密。

    参数:
        username: 用户名
        password: 明文密码
        email: 邮箱
        phone: 手机号（可选）
        nickname: 昵称（可选）

    返回:
        Dict[str, Any]: 包含 success 和 data/error 的字典
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            return {
                "success": False,
                "error": "用户名已存在"
            }

        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            return {
                "success": False,
                "error": "邮箱已被注册"
            }

        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            email=email,
            phone=phone,
            nickname=nickname or username
        )

        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        return {
            "success": True,
            "data": new_user
        }


async def get_user_by_id(user_id: int) -> Optional[User]:
    """
    根据 ID 查询用户

    参数:
        user_id: 用户 ID

    返回:
        Optional[User]: 用户对象，如果不存在返回 None
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


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


async def get_user_by_email(email: str) -> Optional[User]:
    """
    根据邮箱查询用户

    参数:
        email: 邮箱

    返回:
        Optional[User]: 用户对象，如果不存在返回 None
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


async def list_users(
    skip: int = 0,
    limit: int = 100,
    status: Optional[int] = None
) -> List[User]:
    """
    查询用户列表

    参数:
        skip: 跳过的记录数（分页）
        limit: 返回的最大记录数
        status: 账号状态过滤（0-禁用，1-启用）

    返回:
        List[User]: 用户列表
    """
    async with mysql_client.get_session() as session:
        query = select(User)
        if status is not None:
            query = query.where(User.status == status)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())


async def count_users(status: Optional[int] = None) -> int:
    """
    统计用户数量

    参数:
        status: 账号状态过滤（0-禁用，1-启用）

    返回:
        int: 用户数量
    """
    async with mysql_client.get_session() as session:
        from sqlalchemy import func
        query = select(func.count(User.id))
        if status is not None:
            query = query.where(User.status == status)
        result = await session.execute(query)
        return result.scalar() or 0


async def update_user(
    user_id: int,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None,
    status: Optional[int] = None
) -> Dict[str, Any]:
    """
    更新用户信息

    参数:
        user_id: 用户 ID
        email: 新邮箱（可选）
        phone: 新手机号（可选）
        nickname: 新昵称（可选）
        avatar: 新头像URL（可选）
        status: 新账号状态（可选）

    返回:
        Dict[str, Any]: 包含 success 和 data/error 的字典
    """
    async with mysql_client.get_session() as session:
        user = await session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not user:
            return {
                "success": False,
                "error": "用户不存在"
            }

        if email and email != user.email:
            result = await session.execute(
                select(User).where(
                    (User.email == email) & (User.id != user_id)
                )
            )
            if result.scalar_one_or_none():
                return {
                    "success": False,
                    "error": "邮箱已被其他用户使用"
                }

        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if nickname is not None:
            user.nickname = nickname
        if avatar is not None:
            user.avatar = avatar
        if status is not None:
            user.status = status

        await session.flush()
        await session.refresh(user)
        return {
            "success": True,
            "data": user
        }


async def delete_user(user_id: int) -> Dict[str, Any]:
    """
    删除用户

    参数:
        user_id: 用户 ID

    返回:
        Dict[str, Any]: 包含 success 和 error 的字典
    """
    async with mysql_client.get_session() as session:
        user = await session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not user:
            return {
                "success": False,
                "error": "用户不存在"
            }

        await session.delete(user)
        return {
            "success": True
        }


async def get_user_by_wechat_openid(openid: str) -> Optional[User]:
    """
    根据 OpenID 查询用户

    参数:
        openid: 微信 OpenID

    返回:
        Optional[User]: 用户对象，如果不存在返回 None
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(User).where(User.wechat_openid == openid)
        )
        return result.scalar_one_or_none()


async def create_wechat_user(
    openid: str,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None
) -> User:
    """
    创建微信用户

    参数:
        openid: 微信 OpenID
        unionid: 微信 UnionID
        nickname: 微信昵称
        avatar: 微信头像

    返回:
        User: 创建的用户对象

    异常:
        Exception: 创建失败时抛出
    """
    async with mysql_client.get_session() as session:
        new_user = User(
            username=f"wx_{openid[:20]}",
            password="",  # 微信登录不需要密码
            email=f"{openid}@wechat.local",
            wechat_openid=openid,
            wechat_unionid=unionid,
            wechat_nickname=nickname,
            wechat_avatar=avatar,
            nickname=nickname,
            avatar=avatar,
            login_type="wechat",
            status=1,
            is_active=True
        )

        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        return new_user


async def update_wechat_user_info(
    user: User,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None
) -> User:
    """
    更新微信用户信息

    参数:
        user: 用户对象
        unionid: 微信 UnionID
        nickname: 微信昵称
        avatar: 微信头像

    返回:
        User: 更新后的用户对象
    """
    async with mysql_client.get_session() as session:
        if unionid:
            user.wechat_unionid = unionid
        if nickname:
            user.wechat_nickname = nickname
            user.nickname = nickname
        if avatar:
            user.wechat_avatar = avatar
            user.avatar = avatar

        await session.flush()
        await session.refresh(user)
        return user


async def create_or_update_wechat_user(
    openid: str,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None
) -> User:
    """
    创建或更新微信用户

    如果用户不存在则创建，如果存在则更新信息。

    参数:
        openid: 微信 OpenID
        unionid: 微信 UnionID
        nickname: 微信昵称
        avatar: 微信头像

    返回:
        User: 用户对象
    """
    user = await get_user_by_wechat_openid(openid)
    
    if user:
        return await update_wechat_user_info(user, unionid, nickname, avatar)
    else:
        return await create_wechat_user(openid, unionid, nickname, avatar)
