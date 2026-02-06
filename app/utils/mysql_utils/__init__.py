"""
MySQL 工具包模块

本模块导出了 MySQL 工具包的核心组件，包括：
- mysql_client: MySQL 全局客户端管理器，提供数据库操作接口
- Base: SQLAlchemy ORM 基础模型类，用于定义数据库表结构
- BaseModel: ORM 模型基类，包含 id、created_at、updated_at 等通用字段

使用示例:
    # 导入 MySQL 客户端
    from app.utils.mysql_utils import mysql_client

    # 导入 ORM 基础模型
    from app.utils.mysql_utils import Base

    # 定义模型
    from sqlalchemy import Column, String
    from app.utils.mysql_utils import Base

    class User(Base):
        __tablename__ = "users"
        name = Column(String(50), nullable=False, comment="用户名")

    # 使用客户端
    users = await mysql_client.execute_query("SELECT * FROM users")
"""

from app.utils.mysql_utils.mysql_client import mysql_client
from app.utils.mysql_utils.base_model import BaseModel

__all__ = ["mysql_client", "Base", "BaseModel"]
