import json
import os
import re
from http.server import BaseHTTPRequestHandler
def get_recommendation(sermon_topic: str, age_group: str, leadership_role: str, atmosphere: str) -> dict:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_API_KEY가 설정되지 않았습니다. Vercel 대시보드에서 환경 변수를 추가해 주세요."}
    if not sermon_topic or not sermon_topic.strip():
        return {"error": "설교 주제를 입력해 주세요."}

    os.environ["GOOGLE_API_KEY"] = api_key
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    prompt_template = """
    당신은 탁월한 영성과 음악성을 갖춘 교회 찬양팀 디렉터입니다.
    아래의 예배 환경과 설교 주제를 바탕으로 가장 은혜로운 찬양 10곡의 콘티를 기승전결에 맞게 짜주세요.

    [금지] BPM, 템포, 128 BPM, 120 BPM 등 템포 관련 숫자나 표기는 출력에 절대 넣지 마세요. Key(조)만 적으세요.

    [예배 환경]
    - 설교 주제/본문: {sermon_topic}
    - 주요 연령대: {age_group}
    - 주요 직급 및 신앙 연륜: {leadership_role}
    - 원하는 분위기: {atmosphere}

    [선곡 가이드라인]
    1. 주요 연령대와 직급에 익숙하고 은혜받을 수 있는 장르를 적절히 배분하세요.
    2. 찬양의 흐름이 끊기지 않도록 키를 고려하여 순서를 정하세요.
    3. 각 곡마다 '선곡 이유'를 2~3줄로 명확히 적어주세요.

    [출력 형식] (10곡 모두 아래 형식으로. 괄호 안에는 Key만 적고 BPM/템포 숫자 금지.)
    1. 곡 제목 - 아티스트 (Key)
       - 선곡 이유: ...
       - 검색용 키워드: [유튜브에서 이 곡을 찾기 위한 정확한 한글 검색어]
    """
    prompt = PromptTemplate(
        input_variables=["sermon_topic", "age_group", "leadership_role", "atmosphere"],
        template=prompt_template,
    )
    chain = prompt | llm
    result = chain.invoke({
        "sermon_topic": sermon_topic,
        "age_group": age_group,
        "leadership_role": leadership_role,
        "atmosphere": atmosphere or "",
    })
    ai_response = result.content

    # 키워드 추출 후 유튜브 링크 검색 (타임아웃 가능성 있음)
    youtube_links = {}
    try:
        keywords = re.findall(r"검색용 키워드:\s*\[?(.*?)\]", ai_response, re.DOTALL)
        if not keywords:
            keywords = re.findall(r"검색용 키워드:\s*([^\n\[\]-]+)", ai_response)
        if keywords:
            from ddgs import DDGS
            ddgs = DDGS()
            for kw in keywords[:10]:
                kw = kw.strip().strip("]").strip()
                if len(kw) < 2:
                    continue
                try:
                    results = list(ddgs.text(f"{kw} 찬양", max_results=8))
                    links = []
                    for r in results:
                        if not isinstance(r, dict):
                            continue
                        url = r.get("href") or r.get("link") or ""
                        if "youtube.com/watch" in url or "youtu.be/" in url:
                            links.append({"title": (r.get("title") or url)[:80], "href": url})
                            if len(links) >= 5:
                                break
                    if links:
                        youtube_links[kw] = links
                except Exception:
                    pass
    except Exception:
        pass

    return {"content": ai_response, "youtube_links": youtube_links}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if "recommend" not in (self.path or ""):
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._send_json(400, {"error": f"잘못된 요청: {e}"})
            return

        sermon_topic = data.get("sermon_topic", "")
        age_group = data.get("age_group", "전 연령 통합")
        leadership_role = data.get("leadership_role", "직급 무관/초신자 포함")
        atmosphere = data.get("atmosphere", "")

        try:
            out = get_recommendation(sermon_topic, age_group, leadership_role, atmosphere)
            if out.get("error") and not out.get("content"):
                code = 400 if "설교 주제" in out["error"] or "GOOGLE_API_KEY" in out["error"] else 500
                self._send_json(code, {"error": out["error"]})
            else:
                self._send_json(200, out)
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                self._send_json(429, {"error": "API 한도 초과. 잠시 후 다시 시도해 주세요."})
            else:
                self._send_json(500, {"error": f"오류: {err}"})

    def _send_json(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
