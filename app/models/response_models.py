"""
通用响应模型模块

本模块提供了统一的响应模型，用于 API 接口的响应。
"""

from typing import Optional, Any, Generic, TypeVar, List
from pydantic import BaseModel, Field


T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """
    成功响应模型

    属性:
        code: 响应码，0 表示成功
        message: 响应消息
        data: 响应数据
    """
    code: int = Field(0, description="响应码，0 表示成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """
    错误响应模型

    属性:
        error: 错误类型
        message: 错误详情
        status_code: HTTP 状态码
        path: 请求路径
    """
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")
    status_code: int = Field(..., description="HTTP 状态码")
    path: Optional[str] = Field(None, description="请求路径")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型

    属性:
        code: 响应码，0 表示成功
        message: 响应消息
        data: 响应数据
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
    """
    code: int = Field(0, description="响应码，0 表示成功")
    message: str = Field("success", description="响应消息")
    data: List[T] = Field(..., description="响应数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")


def success_response(data: Any = None, message: str = "success") -> dict:
    """
    创建成功响应

    参数:
        data: 响应数据
        message: 响应消息

    返回:
        dict: 成功响应字典
    """
    return {
        "code": 0,
        "message": message,
        "data": data
    }


def paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "success"
) -> dict:
    """
    创建分页响应

    参数:
        data: 响应数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
        message: 响应消息

    返回:
        dict: 分页响应字典
    """
    return {
        "code": 0,
        "message": message,
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size
    }
