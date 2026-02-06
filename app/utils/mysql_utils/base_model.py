"""
SQLAlchemy 基础模型模块

本模块提供了所有 ORM 模型的基类，包含通用的字段定义。
所有数据库表模型都应该继承自 BaseModel，自动获得 id、created_at、updated_at 等字段。

使用示例:
    from sqlalchemy import Column, String
    from app.utils.mysql_utils import Base

    class User(Base):
        __tablename__ = "users"

        name = Column(String(50), nullable=False, comment="用户名")
        email = Column(String(100), unique=True, nullable=False, comment="邮箱")
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    ORM 模型基类

    所有数据库表模型都应该继承此类，自动获得以下字段：
    - id: 自增主键
    - created_at: 创建时间（自动设置）
    - updated_at: 更新时间（自动更新）

    使用示例:
        class User(BaseModel):
            __tablename__ = "users"

            name = Column(String(50), nullable=False, comment="用户名")
            email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
