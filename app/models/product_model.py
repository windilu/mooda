"""
商品数据模型模块

本模块定义了商品表的数据结构，继承自 BaseModel 基类。
包含商品的基本信息字段，如商品名称、描述、价格、库存、图片、租赁信息等。
"""

from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.utils.mysql_utils import BaseModel


class Product(BaseModel):
    """
    商品表模型

    存储商品的基本信息，包括商品名称、描述、价格、库存、图片、租赁信息等。

    属性:
        id: 商品ID（主键，继承自 BaseModel）
        product_id: 商品唯一标识（UUID）
        name: 商品名称
        description: 商品描述
        price: 商品价格
        stock: 库存数量
        cover_image: 封面图片URL
        rental_status: 租赁状态（0-不可租赁，1-可租赁）
        rental_price_single: 单次租赁价格
        rental_price_week: 一周租赁价格
        rental_price_month: 一个月租赁价格
        status: 商品状态（0-下架，1-上架）
        is_active: 是否激活
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间（继承自 BaseModel）
    """

    __tablename__ = "products"

    product_id = Column(String(100), unique=True, nullable=False, index=True, comment="商品唯一标识")
    name = Column(String(200), nullable=False, comment="商品名称")
    description = Column(Text, comment="商品描述")
    price = Column(Float, nullable=False, comment="商品价格")
    stock = Column(Integer, default=0, comment="库存数量")
    cover_image = Column(String(500), comment="封面图片URL")
    rental_status = Column(Integer, default=0, comment="租赁状态：0-不可租赁，1-可租赁")
    rental_price_single = Column(Float, comment="单次租赁价格")
    rental_price_week = Column(Float, comment="一周租赁价格")
    rental_price_month = Column(Float, comment="一个月租赁价格")
    status = Column(Integer, default=1, comment="商品状态：0-下架，1-上架")

    is_active = Column(Boolean, default=True, comment="是否激活")


class ProductImage(BaseModel):
    """
    商品图片表模型

    存储商品的图片信息，包括封面图和其他图片。

    属性:
        id: 图片ID（主键，继承自 BaseModel）
        product_id: 商品唯一标识（外键）
        image_url: 图片URL
        is_cover: 是否封面图
        sort_order: 排序
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间（继承自 BaseModel）
    """

    __tablename__ = "product_images"

    product_id = Column(String(100), nullable=False, index=True, comment="商品唯一标识")
    image_url = Column(String(500), nullable=False, comment="图片URL")
    is_cover = Column(Boolean, default=False, comment="是否封面图")
    sort_order = Column(Integer, default=0, comment="排序")
