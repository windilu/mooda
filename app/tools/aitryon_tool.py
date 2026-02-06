"""
阿里百炼试穿工具模块

本模块提供了阿里百炼 aitryon-plus 模型的试穿功能。
使用 httpx 异步 HTTP 客户端进行网络请求，与 FastAPI 异步架构完美契合。
"""

import asyncio
import httpx
from langchain.tools import tool, ToolException
from pydantic import BaseModel, Field
from typing import Optional, Type, Dict, Any

from app.mode.config.config import ALI_LLM_KEY


class TryOnImageInput(BaseModel):
    """
    试穿图片输入参数模型

    属性:
        person_image_url: 人物图片 URL（穿衣模特）
        top_garment_url: 上衣图片 URL
        bottom_garment_url: 下装图片 URL（可选）
        resolution: 生成图片分辨率，-1 表示使用原图分辨率
        restore_face: 是否恢复人脸
    """
    person_image_url: str = Field(
        description="人物图片,穿衣模特"
    )
    top_garment_url: str = Field(
        description="上衣图片"
    )
    bottom_garment_url: Optional[str] = Field(
        default=None,
        description="下装图片"
    )
    resolution: int = Field(
        default=-1,
        description="生成图片分辨率，-1表示使用原图分辨率，其他值需为正整数"
    )
    restore_face: bool = Field(
        default=False
    )


async def _query_task_status_async(task_id: str) -> Dict[str, Any]:
    """
    异步查询异步任务状态

    参数:
        task_id: 任务 ID

    返回:
        任务状态信息的字典

    异常:
        httpx.HTTPError: 网络请求错误
    """
    api_url = f"https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis/{task_id}"
    headers = {
        "Authorization": f"Bearer {ALI_LLM_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()


@tool(
    args_schema=TryOnImageInput,
    description="""
    调用阿里百炼aitryon-plus模型实现人物试穿服装功能，
    输入人物图片URL、上衣URL（可选下装URL），返回试穿后的图片URL。
    """
)
async def use_aitryon(args_schema=TryOnImageInput):
    """
    使用阿里百炼试穿功能

    调用阿里百炼 aitryon-plus 模型实现人物试穿服装功能。
    支持异步任务提交和轮询查询结果。

    参数:
        args_schema: 试穿图片输入参数

    返回:
        试穿成功后的图片 URL

    异常:
        ToolException: 参数不足、任务失败或超时

    使用方法:
        result = await use_aitryon(TryOnImageInput(
            person_image_url="https://...",
            top_garment_url="https://..."
        ))
    """
    max_retries: int = 20  # 异步任务最大轮询次数
    retry_interval: int = 3  # 轮询间隔（秒）
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis/"
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {ALI_LLM_KEY}",
        "Content-Type": "application/json"
    }
    input_data = {}
    if args_schema.person_image_url:
        input_data["person_image_url"] = args_schema.person_image_url
    if args_schema.top_garment_url:
        input_data["top_garment_url"] = args_schema.top_garment_url
    if args_schema.bottom_garment_url:
        input_data["bottom_garment_url"] = args_schema.bottom_garment_url

    if not input_data:
        raise ToolException("参数不足")

    data = {
        "model": "aitryon",
        "input": input_data,
        "parameters": {
            "resolution": -1,
            "restore_face": False
        }
    }

    try:
        # 发起异步请求
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

        # 获取任务ID
        if "output" not in result or "task_id" not in result["output"]:
            raise ToolException(f"未获取到任务ID，响应：{result}")
        task_id = result["output"]["task_id"]

        retry_count = 0
        while retry_count < max_retries:
            await asyncio.sleep(retry_interval)
            task_result = await _query_task_status_async(task_id)
            task_status = task_result.get("output", {}).get("task_status")

            if task_status == "SUCCEEDED":
                image_url = task_result["output"]["results"][0]["image_url"]
                return f"试穿成功！生成的图片URL：{image_url}"
            elif task_status == "FAILED":
                error_msg = task_result.get("output", {}).get("task_error", {}).get("message", "未知错误")
                raise ToolException(f"试穿任务失败：{error_msg}")
            else:
                retry_count += 1

        raise ToolException(f"试穿任务超时（最大重试{max_retries}次）")

    except httpx.HTTPError as e:
        raise ToolException(f"网络请求错误：{str(e)}")
    except Exception as e:
        raise ToolException(f"试穿工具执行失败：{str(e)}")