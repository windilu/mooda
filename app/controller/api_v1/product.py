"""
商品控制器模块

本模块提供了商品相关的 API 接口，包括：
- 创建商品
- 查询商品信息
- 查询商品列表
- 更新商品信息
- 删除商品

所有接口遵循 RESTful 风格，使用正确的 HTTP 状态码。
权限说明：
- 创建、更新、删除商品：仅超级管理员
- 查询商品：所有角色
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.service.product.product_service import (
    create_product,
    get_product_by_id,
    get_product_images,
    list_products,
    count_products,
    update_product,
    delete_product
)
from app.models.product_model import Product, ProductImage
from app.models.response_models import success_response, paginated_response
from app.utils.auth_utils import get_current_user
from app.models.user_model import User


router = APIRouter()


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    要求超级管理员权限

    检查当前用户是否为超级管理员，如果不是则抛出异常。

    参数:
        current_user: 当前登录用户

    返回:
        User: 当前登录用户

    异常:
        HTTPException: 用户不是超级管理员时抛出（403 Forbidden）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员才能执行此操作"
        )
    return current_user


class ProductCreateRequest(BaseModel):
    """
    商品创建请求模型

    属性:
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        rental_status: 租赁状态
        rental_price_single: 单次租赁价格
        rental_price_week: 一周租赁价格
        rental_price_month: 一个月租赁价格
    """
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    price: float = Field(..., gt=0, description="商品价格")
    stock: int = Field(..., ge=0, description="库存数量")
    rental_status: Optional[int] = Field(0, ge=0, le=1, description="租赁状态：0-不可租赁，1-可租赁")
    rental_price_single: Optional[float] = Field(None, gt=0, description="单次租赁价格")
    rental_price_week: Optional[float] = Field(None, gt=0, description="一周租赁价格")
    rental_price_month: Optional[float] = Field(None, gt=0, description="一个月租赁价格")


class ProductUpdateRequest(BaseModel):
    """
    商品更新请求模型

    属性:
        name: 商品名称（可选）
        description: 商品描述（可选）
        price: 商品价格（可选）
        stock: 库存数量（可选）
        rental_status: 租赁状态（可选）
        rental_price_single: 单次租赁价格（可选）
        rental_price_week: 一周租赁价格（可选）
        rental_price_month: 一个月租赁价格（可选）
        status: 商品状态（可选）
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    price: Optional[float] = Field(None, gt=0, description="商品价格")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    rental_status: Optional[int] = Field(None, ge=0, le=1, description="租赁状态：0-不可租赁，1-可租赁")
    rental_price_single: Optional[float] = Field(None, gt=0, description="单次租赁价格")
    rental_price_week: Optional[float] = Field(None, gt=0, description="一周租赁价格")
    rental_price_month: Optional[float] = Field(None, gt=0, description="一个月租赁价格")
    status: Optional[int] = Field(None, ge=0, le=1, description="商品状态：0-下架，1-上架")


class ProductResponse(BaseModel):
    """
    商品响应模型

    属性:
        id: 商品ID
        product_id: 商品唯一标识
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        cover_image: 封面图片URL
        rental_status: 租赁状态
        rental_price_single: 单次租赁价格
        rental_price_week: 一周租赁价格
        rental_price_month: 一个月租赁价格
        status: 商品状态
        is_active: 是否激活
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    product_id: str
    name: str
    description: Optional[str]
    price: float
    stock: int
    cover_image: Optional[str]
    rental_status: int
    rental_price_single: Optional[float]
    rental_price_week: Optional[float]
    rental_price_month: Optional[float]
    status: int
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class ProductImageResponse(BaseModel):
    """
    商品图片响应模型

    属性:
        id: 图片ID
        product_id: 商品唯一标识
        image_url: 图片URL
        is_cover: 是否封面图
        sort_order: 排序
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    product_id: str
    image_url: str
    is_cover: bool
    sort_order: int
    created_at: Optional[str]
    updated_at: Optional[str]


class ProductDetailResponse(BaseModel):
    """
    商品详情响应模型

    属性:
        product: 商品信息
        images: 商品图片列表
    """
    product: ProductResponse
    images: List[ProductImageResponse]


def product_to_response(product: Product) -> ProductResponse:
    """
    将商品模型转换为响应模型

    参数:
        product: 商品模型对象

    返回:
        ProductResponse: 商品响应对象
    """
    return ProductResponse(
        id=product.id,
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        cover_image=product.cover_image,
        rental_status=product.rental_status,
        rental_price_single=product.rental_price_single,
        rental_price_week=product.rental_price_week,
        rental_price_month=product.rental_price_month,
        status=product.status,
        is_active=product.is_active,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None
    )


def product_image_to_response(image: ProductImage) -> ProductImageResponse:
    """
    将商品图片模型转换为响应模型

    参数:
        image: 商品图片模型对象

    返回:
        ProductImageResponse: 商品图片响应对象
    """
    return ProductImageResponse(
        id=image.id,
        product_id=image.product_id,
        image_url=image.image_url,
        is_cover=image.is_cover,
        sort_order=image.sort_order,
        created_at=image.created_at.isoformat() if image.created_at else None,
        updated_at=image.updated_at.isoformat() if image.updated_at else None
    )


@router.post("/products", status_code=status.HTTP_201_CREATED, summary="创建商品", description="创建新商品")
async def create_product_endpoint(
    current_user: User = Depends(require_superuser),
    name: str = Form(..., description="商品名称"),
    description: Optional[str] = Form(None, description="商品描述"),
    price: float = Form(..., description="商品价格"),
    stock: int = Form(..., description="库存数量"),
    rental_status: Optional[int] = Form(0, description="租赁状态：0-不可租赁，1-可租赁"),
    rental_price_single: Optional[float] = Form(None, description="单次租赁价格"),
    rental_price_week: Optional[float] = Form(None, description="一周租赁价格"),
    rental_price_month: Optional[float] = Form(None, description="一个月租赁价格"),
    cover_image: UploadFile = File(..., description="封面图片"),
    other_images: List[UploadFile] = File([], description="其他图片")
):
    """
    创建商品接口

    创建新商品，支持上传多张图片（包括封面图和其他图片）。
    图片会自动上传到云存储，路径为 `product/{商品唯一标识}/images`。
    支持事务管理和回滚机制，确保数据一致性。

    权限要求：
        - 仅超级管理员可以创建商品

    参数:
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        rental_status: 租赁状态
        rental_price_single: 单次租赁价格
        rental_price_week: 一周租赁价格
        rental_price_month: 一个月租赁价格
        cover_image: 封面图片文件（必填）
        other_images: 其他图片文件列表

    返回:
        dict: 包含商品信息和图片列表的响应

    HTTP 状态码:
        201 Created - 创建成功

    异常:
        HTTPException: 创建失败时抛出（400 Bad Request）
        HTTPException: 权限不足时抛出（403 Forbidden）

    事务说明:
        - 云存储上传和数据库操作在同一个事务中
        - 如果任何步骤失败，会自动回滚所有操作
        - 已上传的图片会自动删除
    """
    result = await create_product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        rental_status=rental_status,
        rental_price_single=rental_price_single,
        rental_price_week=rental_price_week,
        rental_price_month=rental_price_month,
        cover_image_file=cover_image,
        other_image_files=other_images
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    product = result["data"]["product"]
    images = result["data"]["images"]

    return success_response(
        data={
            "product": product_to_response(product),
            "images": [
                {
                    "url": img["url"],
                    "is_cover": img["is_cover"],
                    "sort_order": img.get("sort_order", 0)
                }
                for img in images
            ]
        },
        message="创建商品成功"
    )


@router.get("/products/{product_id}", summary="查询商品信息", description="根据商品ID查询商品信息")
async def get_product_by_id_endpoint(product_id: str):
    """
    查询商品信息接口

    根据商品唯一标识查询商品详情，包括商品信息和图片列表。

    权限要求：
        - 所有角色都可以查询商品

    参数:
        product_id: 商品唯一标识

    返回:
        dict: 包含商品信息和图片列表的响应

    HTTP 状态码:
        200 OK - 查询成功

    异常:
        HTTPException: 商品不存在时抛出（404 Not Found）
    """
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )

    images = await get_product_images(product_id)

    return success_response(
        data={
            "product": product_to_response(product),
            "images": [product_image_to_response(img) for img in images]
        }
    )


@router.get("/products", summary="查询商品列表", description="查询商品列表")
async def get_products_list(
    skip: int = 0,
    limit: int = 100,
    product_status: Optional[int] = None
):
    """
    查询商品列表接口

    查询商品列表，支持分页和状态过滤。

    权限要求：
        - 所有角色都可以查询商品列表

    参数:
        skip: 跳过的记录数（分页）
        limit: 返回的最大记录数
        product_status: 商品状态过滤（0-下架，1-上架）

    返回:
        dict: 包含商品列表的响应

    HTTP 状态码:
        200 OK - 查询成功
    """
    products = await list_products(skip=skip, limit=limit, status=product_status)
    total = await count_products(status=product_status)
    page = skip // limit + 1 if limit > 0 else 1

    return paginated_response(
        data=[product_to_response(product) for product in products],
        total=total,
        page=page,
        page_size=limit
    )


@router.put("/products/{product_id}", summary="更新商品信息", description="更新指定商品信息")
async def update_product_by_id(
    product_id: str,
    request: ProductUpdateRequest,
    current_user: User = Depends(require_superuser)
):
    """
    更新商品信息接口

    更新指定商品的基本信息。

    权限要求：
        - 仅超级管理员可以更新商品

    参数:
        product_id: 商品唯一标识
        request: 更新请求信息

    返回:
        dict: 包含更新后商品信息的响应

    HTTP 状态码:
        200 OK - 更新成功

    异常:
        HTTPException: 商品不存在时抛出（404 Not Found）
        HTTPException: 权限不足时抛出（403 Forbidden）
    """
    result = await update_product(
        product_id=product_id,
        name=request.name,
        description=request.description,
        price=request.price,
        stock=request.stock,
        rental_status=request.rental_status,
        rental_price_single=request.rental_price_single,
        rental_price_week=request.rental_price_week,
        rental_price_month=request.rental_price_month,
        status=request.status
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return success_response(data=product_to_response(result["data"]), message="更新成功")


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品", description="删除指定商品")
async def delete_product_by_id(
    product_id: str,
    current_user: User = Depends(require_superuser)
):
    """
    删除商品接口

    删除指定商品及其所有图片。

    权限要求：
        - 仅超级管理员可以删除商品

    参数:
        product_id: 商品唯一标识

    HTTP 状态码:
        204 No Content - 删除成功

    异常:
        HTTPException: 商品不存在时抛出（404 Not Found）
        HTTPException: 权限不足时抛出（403 Forbidden）
    """
    result = await delete_product(product_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
