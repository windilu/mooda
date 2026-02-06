"""
微信授权登录工具模块

本模块提供了微信授权登录相关的工具函数，包括：
- 生成微信授权 URL
- 使用 code 换取 access_token
- 获取微信用户信息
- 创建或更新微信用户

微信授权登录流程：
1. 前端调用后端获取微信授权 URL
2. 前端跳转到微信授权页面
3. 用户在微信页面点击"授权"
4. 微信重定向到回调地址，带上 code 参数
5. 后端使用 code 换取 access_token 和 openid
6. 后端使用 access_token 获取用户信息
7. 后端根据 openid 查找或创建用户
8. 后端生成 JWT token
9. 后端返回 token 和用户信息
"""

import httpx
from typing import Optional, Dict, Any
from sqlalchemy import select

from app.mode.config.config import (
    WECHAT_APP_ID,
    WECHAT_APP_SECRET,
    WECHAT_REDIRECT_URI
)
from app.utils.mysql_utils import mysql_client
from app.models.user_model import User
from app.utils.auth_utils import create_tokens


WECHAT_AUTH_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
WECHAT_USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"


def get_wechat_auth_url(state: str = "STATE") -> str:
    """
    生成微信授权 URL

    参数:
        state: 用于防止 CSRF 攻击的状态参数

    返回:
        str: 微信授权 URL

    示例:
        >>> url = get_wechat_auth_url()
        >>> print(url)
        https://open.weixin.qq.com/connect/oauth2/authorize?appid=xxx&redirect_uri=xxx&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect
    """
    params = {
        "appid": WECHAT_APP_ID,
        "redirect_uri": WECHAT_REDIRECT_URI,
        "response_type": "code",
        "scope": "snsapi_userinfo",
        "state": state
    }
    
    from urllib.parse import urlencode
    return f"{WECHAT_AUTH_URL}?{urlencode(params)}#wechat_redirect"


async def get_wechat_access_token(code: str) -> Dict[str, Any]:
    """
    使用 code 换取微信 access_token

    参数:
        code: 微信授权后返回的 code

    返回:
        Dict[str, Any]: 包含 access_token, openid, unionid 等信息

    异常:
        Exception: 微信 API 调用失败时抛出

    示例:
        >>> result = await get_wechat_access_token("CODE")
        >>> print(result)
        {
            "access_token": "ACCESS_TOKEN",
            "expires_in": 7200,
            "refresh_token": "REFRESH_TOKEN",
            "openid": "OPENID",
            "scope": "snsapi_userinfo",
            "unionid": "UNIONID"
        }
    """
    params = {
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(WECHAT_TOKEN_URL, params=params)
        response.raise_for_status()
        return response.json()


async def get_wechat_user_info(access_token: str, openid: str) -> Dict[str, Any]:
    """
    获取微信用户信息

    参数:
        access_token: 微信 access_token
        openid: 微信 openid

    返回:
        Dict[str, Any]: 包含用户昵称、头像等信息

    异常:
        Exception: 微信 API 调用失败时抛出

    示例:
        >>> result = await get_wechat_user_info("ACCESS_TOKEN", "OPENID")
        >>> print(result)
        {
            "openid": "OPENID",
            "nickname": "NICKNAME",
            "sex": 1,
            "province": "PROVINCE",
            "city": "CITY",
            "country": "COUNTRY",
            "headimgurl": "HEADIMGURL",
            "privilege": [],
            "unionid": "UNIONID"
        }
    """
    params = {
        "access_token": access_token,
        "openid": openid,
        "lang": "zh_CN"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(WECHAT_USERINFO_URL, params=params)
        response.raise_for_status()
        return response.json()


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


async def wechat_login(code: str) -> Dict[str, Any]:
    """
    微信登录

    使用微信授权 code 完成登录流程。

    参数:
        code: 微信授权后返回的 code

    返回:
        Dict[str, Any]: 包含 success 和 data/error 的字典

    流程:
        1. 使用 code 换取 access_token 和 openid
        2. 使用 access_token 获取用户信息
        3. 根据 openid 查找或创建用户
        4. 生成 JWT token
        5. 返回 token 和用户信息
    """
    try:
        token_info = await get_wechat_access_token(code)
        
        if "errcode" in token_info:
            return {
                "success": False,
                "error": f"微信授权失败：{token_info.get('errmsg', '未知错误')}"
            }
        
        access_token = token_info.get("access_token")
        openid = token_info.get("openid")
        unionid = token_info.get("unionid")
        
        if not access_token or not openid:
            return {
                "success": False,
                "error": "微信授权失败：无法获取 access_token 或 openid"
            }
        
        user_info = await get_wechat_user_info(access_token, openid)
        
        if "errcode" in user_info:
            return {
                "success": False,
                "error": f"获取用户信息失败：{user_info.get('errmsg', '未知错误')}"
            }
        
        nickname = user_info.get("nickname")
        avatar = user_info.get("headimgurl")
        
        user = await create_or_update_wechat_user(
            openid=openid,
            unionid=unionid,
            nickname=nickname,
            avatar=avatar
        )
        
        if not user.is_active:
            return {
                "success": False,
                "error": "账号已被禁用"
            }
        
        tokens = create_tokens(data={"sub": user.username})
        
        return {
            "success": True,
            "data": {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "user": user
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"微信登录失败：{str(e)}"
        }
