"""
数据库初始化模块

本模块提供了数据库和表的初始化功能。
在应用启动时调用，自动创建 mooda 数据库和用户表。
"""

from sqlalchemy import text

from app.mode.config.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
    MYSQL_CHARSET
)
from app.utils.mysql_utils import mysql_client
from app.models.user_model import User
from sqlalchemy.ext.asyncio import create_async_engine


async def create_database():
    """
    创建 mooda 数据库

    如果数据库不存在，则创建它。
    """
    database_url = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/?charset={MYSQL_CHARSET}"

    
    engine = create_async_engine(database_url)

    async with engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`"))

    await engine.dispose()


async def create_tables():
    """
    创建用户表

    使用 SQLAlchemy 的 metadata.create_all() 创建所有表。
    """
    database_url = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"

    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(lambda connection: User.metadata.create_all(bind=connection))

    await engine.dispose()


async def init_database():
    """
    初始化数据库和表

    创建 mooda 数据库和所有表结构。
    """
    print("正在初始化数据库...")
    await create_database()
    await create_tables()
    print("数据库初始化完成！")


async def init_database_with_client():
    """
    初始化数据库和表（带 MySQL 客户端初始化）

    创建 mooda 数据库和所有表结构。
    """
    print("正在初始化 MySQL 客户端...")
    await mysql_client.initialize()
    print("正在初始化数据库...")
    await create_database()
    await create_tables()
    print("数据库初始化完成！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_database_with_client())
