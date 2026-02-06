from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage

import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import json

from app.mode.config.config import ALI_LLM_DICT
from app.mode.llm.create_llm import create_ali_llm


class ColorInfo(BaseModel):
    """服饰颜色详情"""
    main: str = Field(description="主色调，如：白色、黑色、藏青色")
    secondary: List[str] = Field(default=[], description="辅助色列表，如：['灰色', '米色']")
    pattern_color: List[str] = Field(default=[], description="图案颜色列表，无则为空数组")


class ImageFeatures(BaseModel):
    """图像识别特征"""
    detected_colors: List[str] = Field(description="识别到的颜色十六进制码，如：['#FFFFFF', '#E0E0E0']")
    confidence: float = Field(description="识别置信度，0-1之间")


class ClothingInfo(BaseModel):
    """服饰的属性信息"""
    id: str = Field(description="服饰唯一标识，如：item_001")
    category: str = Field(description="服饰的类型，如：裙子、短裤、鞋子或其他类型")
    sub_category: str = Field(description="服饰子类型，如：T恤、衬衫、牛仔裤、半身裙")
    color: ColorInfo = Field(description="服饰的颜色")
    pattern: str = Field(description="服饰图案，如：纯色、条纹、格子、波点、印花")
    style: List[str] = Field(description="整体风格，如：['休闲', '简约', '复古']")
    season: List[str] = Field(description="适合的季节，如：['夏季', '春秋']")
    scene: List[str] = Field(description="适用场景，如：['日常通勤', '居家', '运动']")
    material: str = Field(description="面料类型，如：棉、麻、丝、涤纶、牛仔、皮革")
    texture: str = Field(description="面料质感，如：柔软、粗糙、顺滑、软糯")
    thickness: str = Field(description="面料厚度，如：薄、中、厚")
    transparency: str = Field(description="透明度，如：不透明、半透明、透明")
    neckline: str = Field(description="领口类型，如：圆领、V领、高领、方领、POLO领")
    sleeve_length: str = Field(description="袖长，如：短袖、七分袖、长袖、无袖")
    fit: str = Field(description="版型，如：宽松、修身、直筒、Oversize、紧身")
    length: str = Field(description="长度，如：短款、常规、中长、长款")
    details: List[str] = Field(default=[], description="细节设计，如：['印花', '口袋', '腰带', '蕾丝']")
    silhouette: str = Field(description="廓形，如：直筒、收腰、A字、H型、O型")
    closure: str = Field(description="闭合方式，如：拉链、纽扣、系带、魔术贴、无")
    shoulder: str = Field(description="肩型，如：正肩、落肩、垫肩、溜肩")
    collar: str = Field(description="衣领类型，如：翻领、立领、无领、娃娃领")
    brand: Optional[str] = Field(default=None, description="品牌名称，无则为None")
    gender: str = Field(description="适用性别，如：男、女、中性")
    age_group: str = Field(description="适用年龄段，如：儿童、青年、中年、老年")
    occasion: List[str] = Field(description="适用场合，如：['休闲外出', '校园', '正式会议']")
    compatibility: List[str] = Field(description="适配的服饰品类，如：['牛仔裤', '休闲裤', '短裤']")
    image_features: ImageFeatures = Field(description="图像识别特征信息")


async def create_ali_agent():
    model = create_ali_llm(
        model_name=ALI_LLM_DICT.get("qwen3VlFlash")
    )

    system_prompt=SystemMessage("""
        你是一个图片内容识别专家，专注于衣物服饰的识别，能高效精准的识别衣物属性，并整理出图片中衣物的信息
    """)

    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=system_prompt,
        response_format=ClothingInfo
    )

    messages = [
         HumanMessage(content=[
             {
                 "type": "image_url",
                 "image_url": {
                     "url": "https://luxatlast.com/cdn/shop/files/R-T-Shirt_Symbol-G-01_1024x1024.jpg?v=1696562495"
                 },
             },
             {"type": "text", "text": "帮我识别这个图片中的衣服？"}
         ])
    ]

    try:

        result = await agent.ainvoke({"messages": messages } )

        print(result["structured_response"].model_dump_json())
    except Exception as e:
        print(f"❌ 调用失败：{str(e)}")
        raise
