# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
import openai
import os
import supabase
from datetime import datetime
from dotenv import load_dotenv
load_dotenv() 

# Set your OpenAI key (or use environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class DiaryRequest(BaseModel):
    content: str

class DiaryResponse(BaseModel):
    mood: str
    reason: str
    advice: str
    color_hex: str
    color_desc: str
    image_prompt: str
    gift: str

class ImageRequest(BaseModel):
    prompt: str
    size: Literal["1024x1024", "512x512", "768x1024"] = "512x512"

class ImageResponse(BaseModel):
    url: str

@app.post("/analyze", response_model=DiaryResponse)
def analyze_diary(diary: DiaryRequest):
    try:
        prompt = f"""
        다음은 사용자의 일기 내용입니다. 이 내용을 바탕으로:
        1. 감정 요약 (한 단어)
        2. 감정 이유 (2~3줄)
        3. 조언 (2~3줄)
        4. 오늘의 색상 (HEX 코드와 한글 설명)
        5. 오늘의 이미지 프롬프트 (귀여운 동물 포함, 일본 애니메이션 스타일)
        6. 3만원 이하의 위로 선물 추천 (예: 배달음식, 키링, 간식, 카페 등)

        일기: "{diary.content}"

        JSON 형식으로 응답해:
        {{
          "mood": "감정 요약",
          "reason": "감정 이유",
          "advice": "조언",
          "color_hex": "#778899",
          "color_desc": "슬레이트 그레이",
          "image_prompt": "일러스트 스타일의 고양이가 창가에서 비를 보고 있는 장면",
          "gift": "비 오는 날 어울리는 따뜻한 배달 라떼"
        }}
        """

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 섬세한 감정 분석가이자 위로 요정이야."},
                {"role": "user", "content": prompt},
            ]
        )
        result = completion.choices[0].message.content
        json_data = eval(result)  # 임시 처리, 실제론 json.loads() 형태 권장

        # Supabase 저장
        supabase_client.table("diaries").insert({
            "content": diary.content,
            "mood": json_data["mood"],
            "reason": json_data["reason"],
            "advice": json_data["advice"],
            "color_hex": json_data["color_hex"],
            "color_desc": json_data["color_desc"],
            "image_prompt": json_data["image_prompt"],
            "gift": json_data["gift"],
            "date": datetime.now().isoformat()
        }).execute()

        return json_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image", response_model=ImageResponse)
def generate_image(data: ImageRequest):
    try:
        response = openai.Image.create(
            prompt=data.prompt,
            size=data.size,
            n=1
        )
        return {"url": response["data"][0]["url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
