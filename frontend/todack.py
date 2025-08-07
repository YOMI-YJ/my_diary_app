# frontend/app.py

import streamlit as st
import requests
from datetime import date

st.set_page_config(page_title="오늘의 감성 일기")
st.title("📓 오늘의 감성 일기")
st.markdown("일기를 작성하고 감정 분석을 받아보세요. 조언, 색상, 이미지까지 함께 제공합니다!")

# --- 일기 작성 영역 ---
st.subheader("🖊️ 오늘의 일기를 작성해주세요")
diary_content = st.text_area("", height=200)
today = date.today().isoformat()

# --- GPT 분석 요청 ---
if st.button("분석 시작하기"):
    if not diary_content.strip():
        st.warning("일기 내용을 입력해주세요.")
    else:
        with st.spinner("GPT가 감정을 분석하고 있어요..."):
            try:
                res = requests.post("http://localhost:8000/analyze", json={
                    "content": diary_content
                })

                if res.status_code == 200:
                    result = res.json()

                    st.markdown("---")
                    st.subheader("🧠 GPT 분석 결과")
                    st.markdown(f"**감정 요약:** {result['mood']}")
                    st.markdown(f"**감정 이유:** {result['reason']}")
                    st.markdown(f"**조언:** {result['advice']}")

                    # 색상 선택
                    st.markdown(f"**오늘의 색상:** {result['color_desc']} `{result['color_hex']}`")
                    st.color_picker("색 미리보기", result['color_hex'], label_visibility="collapsed")

                    # 이미지 프롬프트 출력
                    st.markdown("**🎨 GPT가 추천한 이미지 프롬프트:**")
                    st.code(result['image_prompt'])

                    if st.button("이미지 생성하기"):
                        with st.spinner("DALL·E가 이미지를 그리는 중..."):
                            image_res = requests.post("http://localhost:8000/generate-image", json={
                                "prompt": result['image_prompt'],
                                "size": "1024x1024"
                            })

                            if image_res.status_code == 200:
                                img_url = image_res.json()['url']
                                st.image(img_url, caption="GPT가 만든 위로의 이미지", use_container_width=True)
                            else:
                                st.error("이미지 생성에 실패했습니다.")

                    # 선물 추천
                    st.markdown("---")
                    st.subheader("🎁 오늘의 작은 선물 추천")
                    st.markdown(result['gift'])

                else:
                    st.error("GPT 분석 요청에 실패했습니다. 백엔드 서버를 확인해주세요.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
