import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # .env 파일에서 GOOGLE_API_KEY 로드
from langchain_core.prompts import PromptTemplate
from ddgs import DDGS

# 1. UI 설정 (Streamlit)
st.set_page_config(page_title="찬양팀 선곡 AI 에이전트", layout="centered")
st.title("주일 예배 찬양 선곡 에이전트")
st.markdown("설교 주제와 회중의 특성을 입력하면, 맞춤형 찬양 5곡과 유튜브 검색 결과를 무료로 제공합니다.")

# API 키는 .env의 GOOGLE_API_KEY 사용
api_key = os.environ.get("GOOGLE_API_KEY", "")

# 2. 사용자 입력 폼
with st.form("worship_form"):
    sermon_topic = st.text_area("이번 주 설교 주제 및 핵심 메시지 (성경 본문 포함)", placeholder="예: 요한복음 3:16, 하나님의 끝없는 사랑과 우리의 결단")
    
    col1, col2 = st.columns(2)
    with col1:
        age_group = st.selectbox("주요 타겟 연령대", ["전 연령 통합", "10대 (학생부)", "2030 (청년부)", "4050 (장년층)", "60대 이상 (시니어)"])
    with col2:
        leadership_role = st.selectbox("주요 타겟 직급/신앙 연륜", ["직급 무관/초신자 포함", "청년/일반 성도", "서리집사 중심", "안수집사/권사/장로 중심"])
    
    atmosphere = st.text_input("원하는 찬양 분위기 (선택)", placeholder="예: 처음엔 신나게, 뒤에는 깊은 기도로")
    
    submitted = st.form_submit_button("찬양 5곡 추천받기")

# 3. AI 실행 로직
if submitted:
    if not api_key:
        st.warning("Gemini API 키가 없습니다. 프로젝트 폴더에 .env 파일을 만들고 GOOGLE_API_KEY=키값 을 넣어주세요.")
    elif not sermon_topic:
        st.warning("설교 주제를 입력해주세요.")
    else:
        with st.spinner("AI가 기도로 준비하며 곡을 선정하고 있습니다... 🙏"):
            try:
                # 환경 변수에 API 키 임시 저장
                os.environ["GOOGLE_API_KEY"] = api_key
                
                # 현재 사용 가능한 무료 모델 (2.5-flash 또는 2.5-flash-lite)
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

                # 프롬프트 설계
                prompt_template = """
                당신은 탁월한 영성과 음악성을 갖춘 교회 찬양팀 디렉터입니다.
                아래의 예배 환경과 설교 주제를 바탕으로 가장 은혜로운 찬양 5곡의 콘티를 기승전결에 맞게 짜주세요.

                [예배 환경]
                - 설교 주제/본문: {sermon_topic}
                - 주요 연령대: {age_group}
                - 주요 직급 및 신앙 연륜: {leadership_role}
                - 원하는 분위기: {atmosphere}

                [선곡 가이드라인]
                1. 주요 연령대와 직급에 익숙하고 은혜받을 수 있는 장르(전통 찬송가, 구식 복음성가, 최신 모던 워십 등)를 적절히 배분하세요.
                2. **각 곡의 (Key, 템포 BPM)은 반드시 그 곡의 실제 원곡·연주에 맞는 정확한 값만 적으세요.** 추천한 곡이 느린 곡/발라드이면 60~85, 빠른 곡이면 120 전후처럼 곡 성격에 맞는 숫자만 써야 합니다. 느린 곡에 140 같은 빠른 템포를 붙이거나, 곡과 안 맞는 템포로 2번 곡과 억지로 이어 붙이지 마세요.
                3. 찬양 순서는 기승전결에 맞게, 앞에서 뒤로 갈수록 분위기가 자연스럽게 이어지도록 하세요.
                4. **1번·2번이 둘 다 빠른 곡일 때만** 같은 키와 비슷한 템포로 이어부르기 좋게 맞추세요. 1번이 느린 곡이면 템포를 올려서 2번과 숫자를 맞추지 말고, 각 곡 실제 템포대로 표기하세요.
                5. 각 곡마다 '선곡 이유'를 2~3줄로 명확히 적어주세요.

                [출력 형식]
                1. 곡 제목 - 아티스트 (Key, 템포 BPM)
                   - 선곡 이유: ...
                   - 검색용 키워드: [유튜브에서 이 곡을 찾기 위한 정확한 한글 검색어 (예: 마커스워십 주 은혜임을)]
                """
                
                prompt = PromptTemplate(
                    input_variables=["sermon_topic", "age_group", "leadership_role", "atmosphere"],
                    template=prompt_template
                )
                
                # 1차: AI 선곡 결과 생성
                chain = prompt | llm
                result = chain.invoke({
                    "sermon_topic": sermon_topic,
                    "age_group": age_group,
                    "leadership_role": leadership_role,
                    "atmosphere": atmosphere
                })
                
                ai_response = result.content
                
                # 결과 출력
                st.subheader("추천 찬양 콘티")
                st.markdown(ai_response)
                
                # 2차: 추천 곡별로 유튜브 동영상 링크 검색 (ddgs로 링크만 추출)
                st.markdown("---")
                st.subheader("추천 곡 유튜브 링크 검색 결과")

                import re
                # 검색용 키워드 추출 (여러 형식 허용)
                keywords = re.findall(r'검색용 키워드:\s*\[?(.*?)\]', ai_response, re.DOTALL)
                if not keywords:
                    keywords = re.findall(r'검색용 키워드:\s*([^\n\[\]-]+)', ai_response)
                # 그래도 없으면 "1. 곡제목 - 아티스트" 형태에서 곡제목 추출
                if not keywords:
                    for m in re.finditer(r'\d+\.\s*([^-]+?)\s*-\s*[^(]+(?:\([^)]*\))?', ai_response):
                        title = m.group(1).strip()
                        if len(title) >= 2 and "선곡 이유" not in title and "Key" not in title:
                            keywords.append(title)

                if not keywords:
                    st.info("AI 응답에서 검색할 곡 정보를 찾지 못했습니다. 위 추천 콘티에 '검색용 키워드:' 형식이 포함되어 있는지 확인해 주세요.")
                else:
                    ddgs = DDGS()
                    for keyword in keywords:
                        keyword = keyword.strip().strip(']')
                        if not keyword or len(keyword) < 2:
                            continue
                        st.write(f"**{keyword}**")
                        try:
                            results = list(ddgs.text(f"{keyword} 찬양", max_results=10))
                            # href 또는 link 키 모두 처리
                            yt_links = []
                            for r in results:
                                if not isinstance(r, dict):
                                    continue
                                url = r.get("href") or r.get("link") or ""
                                if "youtube.com/watch" in url or "youtu.be/" in url:
                                    yt_links.append({"title": r.get("title") or url[:60], "href": url})
                                    if len(yt_links) >= 5:
                                        break
                            if yt_links:
                                for r in yt_links:
                                    title = (r["title"] or r["href"])[:80]
                                    st.markdown(f"- [{title}]({r['href']})")
                            else:
                                st.caption("(해당 검색어로 유튜브 링크를 찾지 못했습니다)")
                        except Exception as ex:
                            st.caption(f"(검색 중 오류: {ex})")
                        st.markdown("")

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    st.error(
                        "**무료 API 한도를 초과했습니다.**\n\n"
                        "1~2분 뒤에 다시 시도해 보세요. "
                        "계속 나오면 [Google AI 사용량](https://ai.dev/rate-limit)에서 확인해 보세요."
                    )
                else:
                    st.error(f"오류가 발생했습니다: {e}")