"""
用户数据模型模块

本模块定义了用户表的数据结构，继承自 BaseModel 基类。
包含用户的基本信息字段，如用户名、密码、邮箱、手机号、昵称、头像等。
支持密码登录和微信授权登录两种方式。
"""

from sqlalchemy import Column, String, Boolean, Integer
from app.utils.mysql_utils import BaseModel


class User(BaseModel):
    """
    用户表模型

    存储用户的基本信息，包括认证信息和个人资料。
    支持密码登录和微信授权登录两种方式。

    属性:
        id: 用户ID（主键，继承自 BaseModel）
        username: 用户名（唯一，不能为空）
        password: 密码（哈希存储，不能为空）
        email: 邮箱（唯一，不能为空）
        phone: 手机号
        nickname: 昵称
        avatar: 头像URL
        status: 账号状态（0-禁用，1-启用）
        is_active: 是否激活
        is_superuser: 是否超级管理员
        wechat_openid: 微信 OpenID（唯一）
        wechat_unionid: 微信 UnionID（跨应用唯一）
        wechat_nickname: 微信昵称
        wechat_avatar: 微信头像
        login_type: 登录类型（password/wechat）
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间（继承自 BaseModel）
    """

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码（哈希存储）")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    phone = Column(String(20), comment="手机号")
    nickname = Column(String(50), comment="昵称")
    avatar = Column(String(255), comment="头像URL")
    status = Column(Integer, default=1, comment="账号状态：0-禁用，1-启用")

    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")

    wechat_openid = Column(String(100), unique=True, index=True, comment="微信OpenID")
    wechat_unionid = Column(String(100), comment="微信UnionID")
    wechat_nickname = Column(String(100), comment="微信昵称")
    wechat_avatar = Column(String(255), comment="微信头像")
    login_type = Column(String(20), default='password', comment="登录类型：password/wechat")
