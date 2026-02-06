from fastapi import APIRouter

from . import hello
from . import analyze_clothing
from . import user
from . import product

api_v1_router = APIRouter()

api_v1_router.include_router(
    hello.router,
    prefix="/hello",
    tags=["hello"]
)

api_v1_router.include_router(
    analyze_clothing.router,
    prefix="/clothing",
    tags=["clothing"]
)

api_v1_router.include_router(
    user.router,
    prefix="/auth",
    tags=["auth"]
)

api_v1_router.include_router(
    product.router,
    prefix="/product",
    tags=["product"]
)