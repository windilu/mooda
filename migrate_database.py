"""
数据库迁移脚本 - 添加微信相关字段到 users 表

本脚本用于向 users 表添加缺失的微信相关字段：
- wechat_openid
- wechat_unionid
- wechat_nickname
- wechat_avatar
- login_type
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
from sqlalchemy.ext.asyncio import create_async_engine


async def migrate_users_table():
    """
    迁移 users 表，添加微信相关字段

    添加以下字段：
    - wechat_openid: 微信 OpenID（唯一）
    - wechat_unionid: 微信 UnionID（跨应用唯一）
    - wechat_nickname: 微信昵称
    - wechat_avatar: 微信头像
    - login_type: 登录类型（password/wechat）
    """
    database_url = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        print("正在检查并添加微信相关字段...")

        try:
            await conn.execute(text(
                "ALTER TABLE users "
                "ADD COLUMN wechat_openid VARCHAR(100) UNIQUE COMMENT '微信OpenID'"
            ))
            print("✓ 添加 wechat_openid 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ wechat_openid 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE users "
                "ADD COLUMN wechat_unionid VARCHAR(100) COMMENT '微信UnionID'"
            ))
            print("✓ 添加 wechat_unionid 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ wechat_unionid 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE users "
                "ADD COLUMN wechat_nickname VARCHAR(100) COMMENT '微信昵称'"
            ))
            print("✓ 添加 wechat_nickname 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ wechat_nickname 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE users "
                "ADD COLUMN wechat_avatar VARCHAR(255) COMMENT '微信头像'"
            ))
            print("✓ 添加 wechat_avatar 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ wechat_avatar 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE users "
                "ADD COLUMN login_type VARCHAR(20) DEFAULT 'password' COMMENT '登录类型：password/wechat'"
            ))
            print("✓ 添加 login_type 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ login_type 字段已存在，跳过")
            else:
                raise

        print("微信相关字段添加完成！")

    await engine.dispose()


async def migrate_products_table():
    """
    迁移 products 表，添加租赁相关字段

    添加以下字段：
    - rental_status: 租赁状态（0-不可租赁，1-可租赁）
    - rental_price_single: 单次租赁价格
    - rental_price_week: 一周租赁价格
    - rental_price_month: 一个月租赁价格
    """
    database_url = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        print("正在检查并添加租赁相关字段...")

        try:
            await conn.execute(text(
                "ALTER TABLE products "
                "ADD COLUMN rental_status INT DEFAULT 0 COMMENT '租赁状态：0-不可租赁，1-可租赁'"
            ))
            print("✓ 添加 rental_status 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ rental_status 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE products "
                "ADD COLUMN rental_price_single FLOAT COMMENT '单次租赁价格'"
            ))
            print("✓ 添加 rental_price_single 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ rental_price_single 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE products "
                "ADD COLUMN rental_price_week FLOAT COMMENT '一周租赁价格'"
            ))
            print("✓ 添加 rental_price_week 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ rental_price_week 字段已存在，跳过")
            else:
                raise

        try:
            await conn.execute(text(
                "ALTER TABLE products "
                "ADD COLUMN rental_price_month FLOAT COMMENT '一个月租赁价格'"
            ))
            print("✓ 添加 rental_price_month 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ rental_price_month 字段已存在，跳过")
            else:
                raise

        print("租赁相关字段添加完成！")

    await engine.dispose()


async def migrate_all():
    """
    执行所有数据库迁移
    """
    print("=" * 50)
    print("开始数据库迁移")
    print("=" * 50)

    await migrate_users_table()
    print()
    await migrate_products_table()

    print()
    print("=" * 50)
    print("数据库迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_all())
