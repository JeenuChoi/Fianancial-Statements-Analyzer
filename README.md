# 📈 DART Analyst Agent (20년 차 베테랑 공시 분석 에이전트)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Gemini API](https://img.shields.io/badge/Gemini-3.1_Flash_Lite-orange)

대한민국 상장기업의 **DART(전자공시시스템) 정기보고서를 자동으로 수집**하고, GICS 11개 섹터별로 구축된 **'여의도 20년 차 시니어 애널리스트의 분석 뇌(RAG)'**를 바탕으로, 숨겨진 부실(우발채무, 오버행, 회계 착시)을 찾아내어 딥-다이브(Deep-Dive) 브리핑 리포트를 생성하는 자율형 AI 에이전트입니다.

---

## ✨ 핵심 기능 (Key Features)

### 1. 🧠 초정밀 Analyst Brain (맞춤형 RAG 시스템)
단순한 텍스트 요약을 넘어, 실제 펀드매니저들이 주석(Footnotes)을 파헤칠 때 사용하는 노하우를 총 17개의 지식 기반(RAG) 마크다운으로 구축했습니다.
- **11개 섹터 특화 뇌**: 시클리컬 기업의 피크아웃 리스크(해운/화학), 미청구공사 부실(조선/건설), IFRS17 CSM 착시(보험), 개발비 손상차손(게임/바이오) 등 각 산업의 본질적 리스크를 감지합니다.
- **6대 공통 분석 뇌**: 오버행(CB/BW 희석), 흑자부도(OCF/현금흐름 괴리), 우발채무(보증/소송), 이익의 질(밀어내기 매출) 등을 날카롭게 잡아냅니다.

### 2. ⚡ 완전 자율형 파이프라인 (`agent_core.py`)
1. 사용자가 기업명과 연도를 입력하면, **OpenDART API**를 통해 정확한 사업/분기보고서 XML 원문을 추출합니다.
2. **Gemini 3.1 Flash-Lite** 모델이 100만 토큰 한도를 활용해 본문과 주석 전체를 한 번에 싹쓸이하여 읽습니다.
3. 기업의 사업 내용을 보고 11개 섹터 중 어디에 해당하는지 스스로 판단한 뒤, 알맞은 Analyst Brain을 장착하여 정밀 타격 리포트를 작성합니다.

### 3. ⏪ 소름 돋는 '사후 백테스트(Backtest)'
과거 연도(예: 2021년)를 입력하여 분석할 경우, `FinanceDataReader`를 통해 실제 1년 뒤의 주가 등락률(%)을 자동 계산하여 LLM에 전달합니다. 
에이전트는 **"과거의 내가 지적한 리스크가 실제 주가 폭락(-30%)으로 이어졌음"**을 인과관계로 엮어내며 뼈 때리는 사후 평가 교훈을 도출합니다.

---

## 🚀 시작하기 (Getting Started)

### 1. 요구 사항 (Prerequisites)
- Python 3.9 이상
- [OpenDART API Key](https://opendart.fss.or.kr/) 발급 필요
- [Google Gemini API Key](https://aistudio.google.com/) 발급 필요 (Flash-lite 모델 사용)

### 2. 설치 (Installation)
```bash
# 저장소 클론
git clone https://github.com/your-username/dart-analyst-agent.git
cd dart-analyst-agent

# 의존성 패키지 설치
pip install google-genai requests beautifulsoup4 lxml python-dotenv pandas finance-datareader
```

### 3. 환경 변수 설정 (Configuration)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 발급받은 API 키를 입력합니다.
```env
DART_API_KEY=당신의_DART_API_KEY
GEMINI_API_KEY=당신의_GEMINI_API_KEY
```

### 4. 실행 (Usage)
```bash
python agent_core.py
```
실행 후 프롬프트 지시에 따라 기업명과 분석 연도를 입력합니다.
```text
==================================================
🤖 20년 차 베테랑 공시 분석 에이전트에 오신 것을 환영합니다.
==================================================
분석할 기업명을 입력하세요 (예: 삼성전자, HMM): HMM
분석할 공시 연도를 입력하세요 (기본값 2025): 2021
```
약 30~60초 후, 현재 디렉토리에 `HMM_2021년_최종리포트.md` 파일이 생성됩니다.

---

## 📂 프로젝트 구조 (Project Structure)
```text
├── agent_core.py                # 에이전트 핵심 실행 스크립트 (LLM 파이프라인 및 백테스트)
├── dart_collector.py            # DART API 연동 및 XML 파싱, 종목코드 추출 모듈
├── prompt.md                    # LLM 마스터 프롬프트 (위험 점수 산출 가이드)
├── .env                         # API 키 환경 변수
└── analyst_brain/               # 20년 차 애널리스트 뇌 (지식 창고)
    ├── basic_corporate_structure.md  # 지배구조/물적분할 분석
    ├── credit_risk_guide.md          # 흑자부도/파산 징후 분석
    ├── dilution_calculator.md        # 전환사채(CB) 오버행 희석 계산
    ├── earnings_quality_guide.md     # 이익의 질(밀어내기 매출) 검증
    ├── cashflow_quality_guide.md     # 현금흐름(OCF/FCF) 추적
    ├── off_balance_sheet_guide.md    # 우발채무 및 소송 리스크
    └── sectors/                      # GICS 11개 섹터별 특화 가이드라인 (01~11)
```

---

## 📝 라이선스 (License)
이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

*Disclaimer: 본 에이전트가 생성한 리포트는 AI 모델의 분석 결과물이며, 실제 투자 판단의 절대적 근거로 활용될 수 없습니다. 투자 책임은 전적으로 투자자 본인에게 있습니다.*
