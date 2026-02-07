"""
商品服务层模块

本模块提供了商品相关的业务逻辑，包括：
- 创建商品
- 上传商品图片
- 事务管理和回滚机制

服务层只处理业务逻辑，不处理 HTTP 相关和权限检查。
"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.mysql_utils import mysql_client
from app.models.product_model import Product, ProductImage
from app.utils.tcb_utils.tcb_storages import TCBStorageClient


async def create_product(
    name: str,
    description: Optional[str],
    price: float,
    stock: int,
    rental_status: Optional[int] = 0,
    rental_price_single: Optional[float] = None,
    rental_price_week: Optional[float] = None,
    rental_price_month: Optional[float] = None,
    cover_image_file: Any = None,
    other_image_files: List[Any] = None
) -> Dict[str, Any]:
    """
    创建商品

    创建新商品并上传相关图片。

    参数:
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        rental_status: 租赁状态（0=不可租赁，1=可租赁）
        rental_price_single: 单次租赁价格
        rental_price_week: 周租价格
        rental_price_month: 月租价格
        cover_image_file: 封面图片文件对象
        other_image_files: 其他图片文件对象列表

    返回:
        Dict[str, Any]: 包含 success 和 data/error 的字典

    流程:
        1. 生成商品唯一标识（UUID）
        2. 上传封面图片到云存储
        3. 上传其他图片到云存储
        4. 保存商品信息到数据库
        5. 保存图片信息到数据库
        6. 如果任何步骤失败，回滚所有操作
    """
    async with mysql_client.get_session() as session:
        product_id = str(uuid.uuid4())
        uploaded_images = []
        upload_cloud_paths = []
        upload_file_list = []
        
        try:
            tcb_storage_client = TCBStorageClient.get_instance()
            await tcb_storage_client._ensure_authenticated()
            
            cloud_path_prefix = f"product/{product_id}/images"
            
            if cover_image_file is not None:
                cover_uuid = uuid.uuid4().hex[:8]
                if hasattr(cover_image_file, 'filename') and cover_image_file.filename:
                    original_filename = cover_image_file.filename.strip()
                    cover_filename = f"cover_{cover_uuid}_{original_filename}"
                else:
                    cover_filename = f"cover_{cover_uuid}.jpg"
                cover_cloud_path = f"{cloud_path_prefix}/{cover_filename}"
                upload_cloud_paths.append(cover_cloud_path)
                upload_file_list.append(cover_image_file)
            
            if other_image_files:
                for idx, image_file in enumerate(other_image_files):
                    image_uuid = uuid.uuid4().hex[:8]
                    if hasattr(image_file, 'filename') and image_file.filename:
                        original_filename = image_file.filename.strip()
                        image_filename = f"image_{image_uuid}_{original_filename}"
                    else:
                        image_filename = f"image_{image_uuid}.jpg"
                    image_cloud_path = f"{cloud_path_prefix}/{image_filename}"
                    upload_cloud_paths.append(image_cloud_path)
                    upload_file_list.append(image_file)
            
            if upload_cloud_paths:
                upload_result = await tcb_storage_client.upload_file(
                    cloud_paths=upload_cloud_paths,
                    files=upload_file_list
                )
                
                if not upload_result["success"]:
                    return {
                        "success": False,
                        "error": f"上传图片失败：{upload_result.get('error', '未知错误')}"
                    }
                
                uploaded_files = upload_result["data"].get("files", [])
                
                for idx, (cloud_path, _) in enumerate(zip(upload_cloud_paths, upload_file_list)):
                    if idx >= len(uploaded_files):
                        break
                    
                    file_info = uploaded_files[idx]
                    image_url = file_info.get("url")
                    is_cover = idx == 0 and cover_image_file is not None
                    
                    uploaded_images.append({
                        "cloud_path": cloud_path,
                        "url": image_url,
                        "is_cover": is_cover,
                        "sort_order": idx if not is_cover else 0
                    })
            
            new_product = Product(
                product_id=product_id,
                name=name,
                description=description,
                price=price,
                stock=stock,
                cover_image=uploaded_images[0]["url"] if uploaded_images else None,
                rental_status=rental_status,
                rental_price_single=rental_price_single,
                rental_price_week=rental_price_week,
                rental_price_month=rental_price_month,
                status=1,
                is_active=True
            )
            
            session.add(new_product)
            await session.flush()
            await session.refresh(new_product)
            
            for image_info in uploaded_images:
                new_image = ProductImage(
                    product_id=product_id,
                    image_url=image_info["url"],
                    is_cover=image_info["is_cover"],
                    sort_order=image_info.get("sort_order", 0)
                )
                session.add(new_image)
            
            await session.commit()
            
            return {
                "success": True,
                "data": {
                    "product": new_product,
                    "images": uploaded_images
                }
            }
        
        except Exception as e:
            await session.rollback()
            
            if upload_cloud_paths:
                try:
                    tcb_storage_client = TCBStorageClient.get_instance()
                    await tcb_storage_client.delete_file(upload_cloud_paths)
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": f"创建商品失败：{str(e)}"
            }


async def get_product_by_id(product_id: str) -> Optional[Product]:
    """
    根据商品ID查询商品

    参数:
        product_id: 商品唯一标识

    返回:
        Optional[Product]: 商品对象，如果不存在返回 None
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(Product).where(Product.product_id == product_id)
        )
        return result.scalar_one_or_none()


async def get_product_images(product_id: str) -> List[ProductImage]:
    """
    根据商品ID查询商品图片

    参数:
        product_id: 商品唯一标识

    返回:
        List[ProductImage]: 商品图片列表
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.is_cover.desc(), ProductImage.sort_order.asc())
        )
        return list(result.scalars().all())


async def list_products(
    skip: int = 0,
    limit: int = 100,
    status: Optional[int] = None
) -> List[Product]:
    """
    查询商品列表

    参数:
        skip: 跳过记录数
        limit: 返回记录数
        status: 商品状态过滤

    返回:
        List[Product]: 商品列表
    """
    async with mysql_client.get_session() as session:
        query = select(Product)
        
        if status is not None:
            query = query.where(Product.status == status)
        
        result = await session.execute(
            query.offset(skip).limit(limit)
        )
        return list(result.scalars().all())


async def count_products(
    status: Optional[int] = None
) -> int:
    """
    统计商品数量

    参数:
        status: 商品状态过滤

    返回:
        int: 商品总数
    """
    async with mysql_client.get_session() as session:
        query = select(func.count()).select_from(Product)
        
        if status is not None:
            query = query.where(Product.status == status)
        
        result = await session.execute(query)
        return result.scalar()


async def update_product(
    product_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[int] = None,
    rental_status: Optional[int] = None,
    rental_price_single: Optional[float] = None,
    rental_price_week: Optional[float] = None,
    rental_price_month: Optional[float] = None,
    cover_image_file: Any = None,
    other_image_files: List[Any] = None
) -> Dict[str, Any]:
    """
    更新商品信息

    参数:
        product_id: 商品唯一标识
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        rental_status: 租赁状态
        rental_price_single: 单次租赁价格
        rental_price_week: 周租价格
        rental_price_month: 月租价格
        cover_image_file: 封面图片文件对象
        other_image_files: 其他图片文件对象列表

    返回:
        Dict[str, Any]: 包含 success 和 data/error 的字典
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(Product).where(Product.product_id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return {
                "success": False,
                "error": "商品不存在"
            }
        
        uploaded_images = []
        upload_cloud_paths = []
        upload_file_list = []
        
        try:
            tcb_storage_client = TCBStorageClient.get_instance()
            await tcb_storage_client._ensure_authenticated()
            
            cloud_path_prefix = f"product/{product_id}/images"
            
            if cover_image_file is not None:
                cover_uuid = uuid.uuid4().hex[:8]
                if hasattr(cover_image_file, 'filename') and cover_image_file.filename:
                    original_filename = cover_image_file.filename.strip()
                    cover_filename = f"cover_{cover_uuid}_{original_filename}"
                else:
                    cover_filename = f"cover_{cover_uuid}.jpg"
                cover_cloud_path = f"{cloud_path_prefix}/{cover_filename}"
                upload_cloud_paths.append(cover_cloud_path)
                upload_file_list.append(cover_image_file)
            
            if other_image_files:
                for idx, image_file in enumerate(other_image_files):
                    image_uuid = uuid.uuid4().hex[:8]
                    if hasattr(image_file, 'filename') and image_file.filename:
                        original_filename = image_file.filename.strip()
                        image_filename = f"image_{image_uuid}_{original_filename}"
                    else:
                        image_filename = f"image_{image_uuid}.jpg"
                    image_cloud_path = f"{cloud_path_prefix}/{image_filename}"
                    upload_cloud_paths.append(image_cloud_path)
                    upload_file_list.append(image_file)
            
            if upload_cloud_paths:
                upload_result = await tcb_storage_client.upload_file(
                    cloud_paths=upload_cloud_paths,
                    files=upload_file_list
                )
                
                if not upload_result["success"]:
                    return {
                        "success": False,
                        "error": f"上传图片失败：{upload_result.get('error', '未知错误')}"
                    }
                
                uploaded_files = upload_result["data"].get("files", [])
                
                for idx, (cloud_path, _) in enumerate(zip(upload_cloud_paths, upload_file_list)):
                    if idx >= len(uploaded_files):
                        break
                    
                    file_info = uploaded_files[idx]
                    image_url = file_info.get("url")
                    is_cover = idx == 0 and cover_image_file is not None
                    
                    uploaded_images.append({
                        "cloud_path": cloud_path,
                        "url": image_url,
                        "is_cover": is_cover,
                        "sort_order": idx if not is_cover else 0
                    })
            
            if name is not None:
                product.name = name
            
            if description is not None:
                product.description = description
            
            if price is not None:
                product.price = price
            
            if stock is not None:
                product.stock = stock
            
            if rental_status is not None:
                product.rental_status = rental_status
            
            if rental_price_single is not None:
                product.rental_price_single = rental_price_single
            
            if rental_price_week is not None:
                product.rental_price_week = rental_price_week
            
            if rental_price_month is not None:
                product.rental_price_month = rental_price_month
            
            if uploaded_images:
                product.cover_image = uploaded_images[0]["url"]
            
            await session.flush()
            await session.refresh(product)
            
            for image_info in uploaded_images:
                new_image = ProductImage(
                    product_id=product_id,
                    image_url=image_info["url"],
                    is_cover=image_info["is_cover"],
                    sort_order=image_info.get("sort_order", 0)
                )
                session.add(new_image)
            
            await session.commit()
            
            return {
                "success": True,
                "data": {
                    "product": product,
                    "images": uploaded_images
                }
            }
        
        except Exception as e:
            await session.rollback()
            
            if upload_cloud_paths:
                try:
                    tcb_storage_client = TCBStorageClient.get_instance()
                    await tcb_storage_client.delete_file(upload_cloud_paths)
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": f"更新商品失败：{str(e)}"
            }


async def delete_product(product_id: str) -> Dict[str, Any]:
    """
    删除商品

    参数:
        product_id: 商品唯一标识

    返回:
        Dict[str, Any]: 包含 success 和 error 的字典
    """
    async with mysql_client.get_session() as session:
        result = await session.execute(
            select(Product).where(Product.product_id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return {
                "success": False,
                "error": "商品不存在"
            }
        
        result = await session.execute(
            select(ProductImage).where(ProductImage.product_id == product_id)
        )
        images = result.scalars().all()
        
        try:
            tcb_storage_client = TCBStorageClient.get_instance()
            await tcb_storage_client._ensure_authenticated()
        except Exception:
            pass
        
        if images:
            cloud_paths = [
                f"product/{product_id}/images/{image.image_url.split('/')[-1]}"
                for image in images
            ]
            try:
                await tcb_storage_client.delete_file(cloud_paths)
            except Exception:
                pass
        
        await session.delete(product)
        await session.commit()
        
        return {
            "success": True,
            "data": {}
        }
