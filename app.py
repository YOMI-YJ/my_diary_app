import streamlit as st
import openai
import os
from dotenv import load_dotenv
import re
import requests

# =====================
# 1. 환경 설정 및 API 키 로드
# =====================
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================
# 2. 세션 상태 초기화
# =====================
if "gpt_result" not in st.session_state:
    st.session_state.gpt_result = None
if "image_prompt" not in st.session_state:
    st.session_state.image_prompt = None
if "image_url" not in st.session_state:
    st.session_state.image_url = None

# =====================
# 3. 앱 UI 기본 설정
# =====================
st.set_page_config(page_title="오늘의 감성 일기", layout="centered")
st.title("📘 오늘의 감성 일기")
st.write("당신의 일기를 기반으로 감정을 분석하고, 어울리는 색상과 조언, 이미지를 제공합니다.")

# =====================
# 4. 일기 입력
# =====================
diary_text = st.text_area("✏️ 오늘의 일기를 작성해주세요", height=300)


# =====================
# 6. GPT 분석 버튼
# =====================
if st.button("🔍 분석 시작하기") and diary_text:
    with st.spinner("GPT가 당신의 하루를 읽고 있어요..."):

        # GPT 프롬프트 구성
        prompt = f"""
다음은 내가 쓴 일기야:

\"\"\"{diary_text}\"\"\"

이 일기를 읽고 다음 항목들을 알려줘.

1. 감정 요약: 한 단어로 (예: 우울함, 설렘, 안정감 등)
2. 감정 분석 이유: 왜 그렇게 판단했는지 2~3문장으로 설명
3. 조언: 이 감정을 가진 나에게 따뜻한 한 마디 조언
4. 색상 추천: 이 감정에 어울리는 색상 한 가지를 HEX 코드로
        """

        # GPT 감정 분석 수행
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        st.session_state.gpt_result = result

        # 조언 추출
        advice_match = re.search(r"3\.\s*조언\s*[:：]?\s*(.*)", result)
        advice = advice_match.group(1).strip() if advice_match else "당신은 소중한 존재입니다."

        # 색상 추출
        hex_match = re.search(r"#([0-9a-fA-F]{6})", result)
        hex_color = "#" + hex_match.group(1) if hex_match else "#CCCCCC"

        # 이미지 프롬프트 생성
        image_prompt_instruction =f"""
다음은 내가 받은 조언이야:

"{advice}"

이 조언의 감정과 의미를 시각적으로 표현한 **2D 일러스트 이미지**를 만들고 싶어.

다음 조건을 지켜서 DALL·E 3에 사용할 **영어 한 줄 프롬프트**를 만들어줘:

- 일본 애니메이션 스타일 (Japanese anime style)
- 귀여운 동물이 꼭 포함되어야 해 (예: 고양이, 강아지, 토끼 등)
- 조언의 따뜻하고 감성적인 느낌이 잘 전달되도록 해줘
- 배경화면으로 어울리도록 예쁘고 부드러운 분위기로
- 너무 추상적이지 않게, 장면을 구체적으로 설명해줘

영어 한 문장으로 프롬프트를 써줘.
"""
        image_prompt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": image_prompt_instruction}],
            temperature=0.7
        )
        st.session_state.image_prompt = image_prompt_response.choices[0].message.content.strip()

# =====================
# 7. GPT 분석 결과 출력
# =====================
if st.session_state.gpt_result:
    st.markdown("### 🧠 GPT 분석 결과")
    st.markdown(st.session_state.gpt_result)

    hex_color = re.search(r"#([0-9a-fA-F]{6})", st.session_state.gpt_result)
    hex_color = "#" + hex_color.group(1) if hex_color else "#CCCCCC"

    st.markdown(f"#### 🎨 오늘의 색상: `{hex_color}`")
    st.markdown(
        f'<div style="width:100%; height:80px; background-color:{hex_color}; border-radius:10px;"></div>',
        unsafe_allow_html=True
    )

    st.markdown("### 🎨 이미지 프롬프트")
    st.markdown(f"`{st.session_state.image_prompt}`")

# =====================
# 8. 이미지 생성 단계 (분석 결과가 있을 때만 표시)
# =====================
if st.session_state.image_prompt:
    st.markdown("---")
    st.subheader("🖼 이미지 생성")

    image_size = st.radio("원하는 이미지 비율을 선택하세요:", ["스마트폰 (세로)", "컴퓨터 (가로)", "정사각형"])

    if image_size == "스마트폰 (세로)":
        image_size_code = "1024x1792"
    elif image_size == "컴퓨터 (가로)":
        image_size_code = "1792x1024"
    else:
        image_size_code = "1024x1024"

    if st.button("🖼️ 이미지 생성하기"):
        with st.spinner("이미지를 그리고 있어요..."):
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=st.session_state.image_prompt,
                size=image_size_code,
                quality="standard",
                n=1
            )
            st.session_state.image_url = image_response.data[0].url


# =====================
# 9. 이미지 출력 및 다운로드
# =====================
if st.session_state.image_url:
    st.image(st.session_state.image_url, caption="오늘의 이미지", use_container_width=True)
    image_data = requests.get(st.session_state.image_url).content
    st.download_button(
        label="📥 이미지 다운로드",
        data=image_data,
        file_name="daily_image.png",
        mime="image/png"
    )
