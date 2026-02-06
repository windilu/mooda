"""
MySQL 使用示例模块

本模块提供了 MySQL 客户端的各种使用示例，包括：
- 原生 SQL CRUD 操作
- ORM 模型定义和使用
- 事务处理
- 连接测试

所有示例函数都可以直接调用，用于学习和参考。
"""

from sqlalchemy import Column, String, Integer
from app.utils.mysql_utils import Base, mysql_client


class User(Base):
    """
    用户表模型示例

    这是一个示例 ORM 模型，展示了如何定义数据库表结构。
    继承自 Base（实际上是 BaseModel），自动获得 id、created_at、updated_at 字段。

    属性:
        id: 用户ID（主键，继承自 BaseModel）
        name: 用户名
        email: 邮箱（唯一）
        age: 年龄
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间（继承自 BaseModel）
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    name = Column(String(50), nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    age = Column(Integer, comment="年龄")


async def example_create_table():
    """
    示例：创建数据库表

    使用 ORM 模型创建数据库表结构。
    这个函数会创建所有继承自 Base 的模型对应的表。

    使用方法:
        await example_create_table()
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    async with mysql_client.get_session() as session:
        await session.run_sync(lambda conn: Base.metadata.create_all(bind=conn))


async def example_insert_user():
    """
    示例：插入用户数据（原生 SQL）

    使用原生 SQL 语句插入一条用户记录。

    使用方法:
        await example_insert_user()

    输出示例:
        插入成功，ID: 1
    """
    sql = "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)"
    params = {"name": "张三", "email": "zhangsan@example.com", "age": 25}
    last_id = await mysql_client.execute_insert(sql, params)
    print(f"插入成功，ID: {last_id}")


async def example_query_users():
    """
    示例：查询多条用户数据（原生 SQL）

    使用原生 SQL 查询年龄大于 20 的所有用户。

    使用方法:
        await example_query_users()

    输出示例:
        查询到 2 条记录:
        {'id': 1, 'name': '张三', 'email': 'zhangsan@example.com', 'age': 25, 'created_at': datetime(...), 'updated_at': datetime(...)}
        {'id': 2, 'name': '李四', 'email': 'lisi@example.com', 'age': 30, 'created_at': datetime(...), 'updated_at': datetime(...)}
    """
    sql = "SELECT * FROM users WHERE age > :age"
    params = {"age": 20}
    users = await mysql_client.execute_query(sql, params)
    print(f"查询到 {len(users)} 条记录:")
    for user in users:
        print(user)


async def example_query_one_user():
    """
    示例：查询单条用户数据（原生 SQL）

    使用原生 SQL 根据 ID 查询单个用户。

    使用方法:
        await example_query_one_user()

    输出示例:
        查询到用户: {'id': 1, 'name': '张三', 'email': 'zhangsan@example.com', 'age': 25, ...}
        或
        未找到用户
    """
    sql = "SELECT * FROM users WHERE id = :id"
    params = {"id": 1}
    user = await mysql_client.execute_query_one(sql, params)
    if user:
        print(f"查询到用户: {user}")
    else:
        print("未找到用户")


async def example_update_user():
    """
    示例：更新用户数据（原生 SQL）

    使用原生 SQL 更新指定用户的年龄。

    使用方法:
        await example_update_user()

    输出示例:
        更新了 1 条记录
    """
    sql = "UPDATE users SET age = :age WHERE id = :id"
    params = {"age": 26, "id": 1}
    affected_rows = await mysql_client.execute_update(sql, params)
    print(f"更新了 {affected_rows} 条记录")


async def example_delete_user():
    """
    示例：删除用户数据（原生 SQL）

    使用原生 SQL 删除指定用户。

    使用方法:
        await example_delete_user()

    输出示例:
        删除了 1 条记录
    """
    sql = "DELETE FROM users WHERE id = :id"
    params = {"id": 1}
    affected_rows = await mysql_client.execute_delete(sql, params)
    print(f"删除了 {affected_rows} 条记录")


async def example_transaction():
    """
    示例：事务处理

    使用事务上下文管理器执行多个 SQL 操作。
    如果其中任何一个操作失败，所有操作都会回滚。

    使用方法:
        await example_transaction()

    说明:
        这个示例展示了如何在事务中插入多条记录。
        如果第二条插入失败，第一条也会被回滚。
    """
    async with mysql_client.transaction() as session:
        from sqlalchemy import text

        await session.execute(text("INSERT INTO users (name, email, age) VALUES ('李四', 'lisi@example.com', 30)"))
        await session.execute(text("INSERT INTO users (name, email, age) VALUES ('王五', 'wangwu@example.com', 28)"))


async def example_with_orm():
    """
    示例：使用 ORM 查询数据

    使用 SQLAlchemy ORM 查询年龄大于 20 的所有用户。
    ORM 方式比原生 SQL 更类型安全，代码更易维护。

    使用方法:
        await example_with_orm()

    输出示例:
        ORM查询 - ID: 1, 姓名: 张三, 邮箱: zhangsan@example.com, 年龄: 25
        ORM查询 - ID: 2, 姓名: 李四, 邮箱: lisi@example.com, 年龄: 30
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    async with mysql_client.get_session() as session:
        result = await session.execute(select(User).where(User.age > 20))
        users = result.scalars().all()
        for user in users:
            print(f"ORM查询 - ID: {user.id}, 姓名: {user.name}, 邮箱: {user.email}, 年龄: {user.age}")


async def example_test_connection():
    """
    示例：测试数据库连接

    测试 MySQL 连接是否正常。

    使用方法:
        await example_test_connection()

    输出示例:
        MySQL 连接成功
        或
        MySQL 连接失败
    """
    is_connected = await mysql_client.test_connection()
    if is_connected:
        print("MySQL 连接成功")
    else:
        print("MySQL 连接失败")
