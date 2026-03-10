# worship_agent

주일 예배 찬양 선곡 AI 에이전트. 설교 주제와 회중 특성을 입력하면 맞춤형 찬양 5곡과 유튜브 검색 결과를 제공합니다.

## 로컬 실행 (Streamlit)

```bash
pip install -r requirements.txt
# .env 파일에 GOOGLE_API_KEY=키값 설정
streamlit run app.py
```

## Vercel 배포 (worship-agent.vercel.app)

1. [Vercel](https://vercel.com)에 로그인 후 **Add New Project** → **Import Git Repository**에서 이 저장소 선택.
2. **Root Directory**는 그대로 두고 **Deploy**.
3. 배포 후 **Project → Settings → Environment Variables**에서 다음 추가:
   - `GOOGLE_API_KEY`: Google AI Studio에서 발급한 Gemini API 키
4. (선택) **Settings → Domains**에서 `worship-agent.vercel.app` 커스텀 도메인 연결.

배포가 완료되면 루트 URL(예: `https://worship-agent.vercel.app`)에서 사용할 수 있습니다.

**404 NOT_FOUND가 나올 때**
- Vercel 대시보드 → 해당 프로젝트 → **Settings** → **General** → **Root Directory**가 비어 있거나 `.` 인지 확인하세요. 하위 폴더로 설정돼 있으면 `index.html`을 찾지 못해 404가 납니다.
- **Redeploy** 한 번 해보세요.

## 스택

- UI: Streamlit(로컬) / HTML+JS(Vercel)
- AI: Google Gemini 2.5 Flash
- 검색: ddgs (DuckDuckGo)
