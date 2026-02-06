from fastapi import APIRouter
from fastapi import UploadFile, File, HTTPException
from app.service.analyze_clothing.analyze_clothing_service import analyze_clothing_service

router = APIRouter()


@router.post("/analyze-clothing", summary="AI衣物识别", description="上传衣物图片")
async def analyze_clothing(file: UploadFile = File(...)):
    try:
        result = await analyze_clothing_service(file)

        return {
            "code": 0,
            "msg": "识别成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败：{str(e)}")