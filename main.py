import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator, Any
import traceback

from app.controller.api_v1.api_v1 import api_v1_router
from app.scheduler import scheduler
from app.utils.redis_utils import redis_client
from app.utils.tcb_utils.tcb_storages import TCBStorageClient
from app.utils.mysql_utils import mysql_client
from app.utils.init_db import init_database


# ---------------------- 定义 lifespan 生命周期处理器 ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 生命周期管理器（替代旧的 startup/shutdown 事件）
    - 启动时（yield 前）：初始化 Redis 单例
    - 关闭时（yield 后）：释放 Redis 资源
    """
    # ===== 应用启动时执行（替代 startup_event）=====


    try:
        print("应用启动中，初始化 Redis 全局单例...")
        await redis_client.initialize(host="127.0.0.1")
        print("应用启动中，初始化 MySQL 连接池...")
        await mysql_client.initialize()
        print("应用启动中，初始化数据库...")
        await init_database()
        """登陆腾讯云存储服务"""
        tcb_storage_client = TCBStorageClient.get_instance()
        await tcb_storage_client._signin()
        scheduler.start()

    except Exception as e:
        raise RuntimeError(f"❌ 应用启动失败：{str(e)}")
    # 交给应用运行（yield 是分界点）
    yield
    print("应用关闭中...")
    """关闭redis服务"""
    await redis_client.close()
    """关闭MySQL服务"""
    await mysql_client.close()
    """关闭腾讯云存储客户端"""
    tcb_storage_client = TCBStorageClient.get_instance()
    if tcb_storage_client:
        await tcb_storage_client.close()
    print("应用已关闭...")


app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix='/v1')


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器

    处理 HTTPException，返回统一的错误响应格式。
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器

    捕获所有未处理的异常，返回统一的错误响应格式。
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "status_code": 500,
            "path": request.url.path
        }
    )

# 基础启动（热重载+监听所有IP+指定端口）
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
