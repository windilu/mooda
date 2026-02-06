from fastapi import APIRouter

from app.service.hello.hello_service import hello_service

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def read_root():
    result = await hello_service()
    return result