"""
MySQL 客户端管理模块

本模块提供了一个全局的 MySQL 异步客户端管理器，基于 SQLAlchemy 2.0 和 aiomysql 驱动实现。
支持连接池管理、原生 SQL 操作、ORM 操作以及事务处理。

主要功能：
- 异步连接池管理
- 原生 SQL CRUD 操作
- ORM 会话管理
- 事务支持
- 连接测试
"""

from typing import Optional, AsyncGenerator, Any, Dict, List
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.mode.config.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
    MYSQL_CHARSET
)


class MySQLClient:
    """
    MySQL 全局客户端管理器

    采用单例模式管理 MySQL 异步连接池，提供统一的数据库操作接口。
    所有方法都是类方法，通过类名直接调用，无需实例化。

    属性:
        engine: SQLAlchemy 异步引擎实例
        async_session_factory: 异步会话工厂
    """

    engine: Optional[Any] = None
    async_session_factory: Optional[async_sessionmaker] = None

    @classmethod
    async def initialize(
        cls,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        charset: str = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        echo: bool = False
    ):
        """
        初始化 MySQL 连接池

        在应用启动时调用此方法，创建数据库连接池和会话工厂。
        如果未提供参数，则使用配置文件中的默认值。

        参数:
            host: 数据库主机地址，默认从配置读取
            port: 数据库端口，默认从配置读取
            user: 数据库用户名，默认从配置读取
            password: 数据库密码，默认从配置读取
            database: 数据库名称，默认从配置读取
            charset: 字符集，默认从配置读取
            pool_size: 连接池大小，默认 10
            max_overflow: 连接池最大溢出数，默认 20
            pool_pre_ping: 是否在获取连接时测试连接，默认 True
            echo: 是否打印 SQL 语句，默认 False（调试时可设为 True）

        示例:
            await mysql_client.initialize()
            # 或自定义参数
            await mysql_client.initialize(
                host="192.168.1.100",
                port=3307,
                pool_size=20
            )
        """
        host = host or MYSQL_HOST
        port = port or MYSQL_PORT
        user = user or MYSQL_USER
        password = password or MYSQL_PASSWORD
        database = database or MYSQL_DATABASE
        charset = charset or MYSQL_CHARSET

        database_url = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"

        cls.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            echo=echo
        )

        cls.async_session_factory = async_sessionmaker(
            cls.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    @classmethod
    async def close(cls):
        """
        关闭 MySQL 连接池

        在应用关闭时调用此方法，释放所有数据库连接资源。
        调用后需要重新调用 initialize() 才能再次使用数据库。

        示例:
            await mysql_client.close()
        """
        if cls.engine:
            await cls.engine.dispose()
            cls.engine = None
            cls.async_session_factory = None

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话（上下文管理器）

        返回一个异步会话，用于 ORM 操作。
        使用上下文管理器自动处理事务的提交和回滚。

        返回:
            AsyncSession: SQLAlchemy 异步会话对象

        异常:
            RuntimeError: 如果 MySQL 未初始化

        示例:
            async with mysql_client.get_session() as session:
                result = await session.execute(select(User).where(User.id == 1))
                user = result.scalar_one_or_none()
        """
        if cls.async_session_factory is None:
            raise RuntimeError("MySQL 未初始化，请先调用 initialize()")
        async with cls.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def execute_query(
        cls,
        sql: str,
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行原生 SQL 查询（返回多条记录）

        执行 SELECT 查询，返回所有匹配的记录。
        支持参数化查询，防止 SQL 注入。

        参数:
            sql: SQL 查询语句，使用命名参数（如 :name）
            params: 参数字典，键名与 SQL 中的命名参数对应

        返回:
            List[Dict[str, Any]]: 查询结果列表，每个元素是一个字典

        示例:
            users = await mysql_client.execute_query(
                "SELECT * FROM users WHERE age > :age",
                {"age": 20}
            )
        """
        async with cls.get_session() as session:
            result = await session.execute(text(sql), params or {})
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    @classmethod
    async def execute_query_one(
        cls,
        sql: str,
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        执行原生 SQL 查询（返回单条记录）

        执行 SELECT 查询，返回第一条匹配的记录。
        如果没有匹配的记录，返回 None。

        参数:
            sql: SQL 查询语句，使用命名参数（如 :name）
            params: 参数字典，键名与 SQL 中的命名参数对应

        返回:
            Optional[Dict[str, Any]]: 查询结果字典，如果没有匹配则返回 None

        示例:
            user = await mysql_client.execute_query_one(
                "SELECT * FROM users WHERE id = :id",
                {"id": 1}
            )
        """
        rows = await cls.execute_query(sql, params)
        return rows[0] if rows else None

    @classmethod
    async def execute_update(
        cls,
        sql: str,
        params: Dict[str, Any] = None
    ) -> int:
        """
        执行原生 SQL 更新操作

        执行 UPDATE、INSERT、DELETE 等 SQL 语句。
        返回受影响的行数。

        参数:
            sql: SQL 语句，使用命名参数（如 :name）
            params: 参数字典，键名与 SQL 中的命名参数对应

        返回:
            int: 受影响的行数

        示例:
            affected = await mysql_client.execute_update(
                "UPDATE users SET age = :age WHERE id = :id",
                {"age": 26, "id": 1}
            )
        """
        async with cls.get_session() as session:
            result = await session.execute(text(sql), params or {})
            return result.rowcount

    @classmethod
    async def execute_insert(
        cls,
        sql: str,
        params: Dict[str, Any] = None
    ) -> int:
        """
        执行原生 SQL 插入操作

        执行 INSERT 语句，返回新插入记录的自增 ID。
        如果表没有自增主键，返回 0。

        参数:
            sql: INSERT 语句，使用命名参数（如 :name）
            params: 参数字典，键名与 SQL 中的命名参数对应

        返回:
            int: 新插入记录的自增 ID

        示例:
            new_id = await mysql_client.execute_insert(
                "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)",
                {"name": "张三", "email": "zhangsan@example.com", "age": 25}
            )
        """
        async with cls.get_session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result.lastrowid

    @classmethod
    async def execute_delete(
        cls,
        sql: str,
        params: Dict[str, Any] = None
    ) -> int:
        """
        执行原生 SQL 删除操作

        执行 DELETE 语句，返回受影响的行数。
        实际上是对 execute_update 的封装，提供更清晰的语义。

        参数:
            sql: DELETE 语句，使用命名参数（如 :name）
            params: 参数字典，键名与 SQL 中的命名参数对应

        返回:
            int: 受影响的行数

        示例:
            deleted = await mysql_client.execute_delete(
                "DELETE FROM users WHERE id = :id",
                {"id": 1}
            )
        """
        return await cls.execute_update(sql, params)

    @classmethod
    @asynccontextmanager
    async def transaction(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        事务上下文管理器

        返回一个异步会话，用于执行事务操作。
        如果事务中发生异常，会自动回滚；否则自动提交。

        返回:
            AsyncSession: SQLAlchemy 异步会话对象

        异常:
            RuntimeError: 如果 MySQL 未初始化

        示例:
            async with mysql_client.transaction() as session:
                await session.execute(text("INSERT INTO users (name) VALUES ('张三')"))
                await session.execute(text("INSERT INTO logs (action) VALUES ('create_user')"))
        """
        if cls.async_session_factory is None:
            raise RuntimeError("MySQL 未初始化，请先调用 initialize()")
        async with cls.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def test_connection(cls) -> bool:
        """
        测试 MySQL 连接是否正常

        执行一个简单的查询来测试数据库连接是否可用。

        返回:
            bool: 连接成功返回 True，失败返回 False

        示例:
            if await mysql_client.test_connection():
                print("MySQL 连接正常")
            else:
                print("MySQL 连接失败")
        """
        try:
            await cls.execute_query("SELECT 1")
            return True
        except Exception:
            return False


mysql_client = MySQLClient()
