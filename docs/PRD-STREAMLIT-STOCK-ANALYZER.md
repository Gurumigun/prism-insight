# PRD: PRISM-INSIGHT Streamlit - 개인용 주식 AI 분석 웹 앱

## 문서 정보
- **문서 버전**: 1.0.0
- **작성일**: 2025-11-09
- **제품명**: PRISM-INSIGHT Streamlit App
- **프로젝트 코드명**: Stock AI Review Streamlit

---

## ⚠️ 절대 원칙: 기존 코드 수정 금지

```
🚨🚨🚨 중요 🚨🚨🚨

이 프로젝트는 기존 PRISM-INSIGHT 시스템의 기능을
활용하되, 기존 코드를 절대 수정하지 않습니다.

금지 사항:
❌ cores/ 폴더 내 파일 수정
❌ examples/streamlit/app_modern.py 수정
❌ stock_analysis_orchestrator.py 수정
❌ telegram_*.py 파일 수정
❌ 기타 모든 기존 파일 수정

허용 사항:
✅ 새로운 독립 모듈 생성
✅ 기존 모듈 import만 허용
✅ 새로운 디렉토리 생성
✅ 새로운 설정 파일 생성
```

---

## 1. 제품 개요

### 1.1 제품 설명

PRISM-INSIGHT Streamlit App은 **개인용 웹 기반 주식 AI 분석 도구**입니다. 브라우저에서 실행되며, 12개의 전문화된 AI 에이전트가 협업하여 실시간으로 종합 분석을 수행하고, 직관적인 웹 UI로 결과를 제공합니다.

### 1.2 제품 비전

"개인 투자자를 위한 가장 쉽고 편리한 웹 기반 AI 주식 분석 환경 제공"

### 1.3 핵심 가치 제안

- ✅ **편의성**: 브라우저만 있으면 어디서나 접근
- ✅ **시각화**: 차트와 그래프로 직관적 분석
- ✅ **대화형**: Claude AI와 실시간 Q&A
- ✅ **전문성**: 12개 AI 에이전트(GPT-5, Claude 4.1)의 협업
- ✅ **빠른 개발**: 기존 코드 100% 재사용, 버그 최소화

### 1.4 기존 시스템과의 차이점

| 구분 | 기존 app_modern.py | 새로운 앱 |
|------|-------------------|-----------|
| **파일명** | `examples/streamlit/app_modern.py` | `streamlit_apps/personal_analyzer.py` |
| **수정 여부** | ❌ 절대 수정 금지 | ✅ 새로 생성 |
| **PDF 생성** | 자동 생성 | 선택적 생성 |
| **텔레그램** | 자동 전송 | 전송 안 함 |
| **이메일** | 자동 전송 | 전송 안 함 |
| **Q&A** | 없음 | Claude AI Q&A |
| **대상** | 상용 서비스 | 개인용 |

---

## 2. 목표 사용자

### 2.1 주요 페르소나

**단일 페르소나: 개인 투자자**
- 특징: 여러 종목 비교 분석, 빠른 의사결정
- 니즈: 브라우저에서 편하게 주식 분석, PDF 선택적 저장
- 시나리오: "삼성전자 분석 → SK하이닉스 분석 → 비교 → PDF 저장"

---

## 3. 사용자 스토리

### Epic 1: 웹 기반 분석

```
AS A 개인 투자자
I WANT 브라우저에서 주식 코드를 입력하여 AI 분석을 받고
SO THAT 편하게 여러 종목을 비교 분석 가능
```

**User Stories:**
- US-001: 사용자는 브라우저에서 앱을 실행한다 (localhost:8501)
- US-002: 사용자는 종목코드 또는 종목명을 입력한다
- US-003: 사용자는 분석 버튼을 클릭한다
- US-004: 사용자는 진행 상황을 실시간으로 확인한다 (프로그레스 바)
- US-005: 사용자는 분석 결과를 웹 페이지에서 읽는다
- US-006: 사용자는 필요시 PDF로 다운로드한다

### Epic 2: AI 분석 엔진

```
AS A 시스템
I WANT 기존 cores/ 모듈을 그대로 활용하여
SO THAT 일관된 품질의 분석 제공
```

**User Stories:**
- US-101: 시스템은 cores/analysis.py의 analyze_stock() 함수를 호출한다
- US-102: 시스템은 6개 분석 에이전트 결과를 받는다
- US-103: 시스템은 투자 전략 에이전트 결과를 받는다
- US-104: 시스템은 매수/매도 의견(GPT-5)을 받는다
- US-105: 시스템은 결과를 웹 UI로 렌더링한다

### Epic 3: Q&A 기능

```
AS A 사용자
I WANT 분석 결과에 대해 Claude AI에게 질문하고
SO THAT 더 깊은 인사이트 획득
```

**User Stories:**
- US-201: 사용자는 사이드바에 채팅 창을 본다
- US-202: 사용자는 분석 결과 기반 질문을 입력한다
- US-203: 사용자는 Claude AI의 답변을 실시간으로 받는다
- US-204: 사용자는 대화 히스토리를 확인한다

### Epic 4: 보고서 관리

```
AS A 사용자
I WANT 분석 결과를 선택적으로 저장하고
SO THAT 필요한 것만 관리
```

**User Stories:**
- US-301: 사용자는 "PDF 다운로드" 버튼을 본다
- US-302: 사용자가 버튼 클릭 시 PDF가 생성된다
- US-303: PDF는 `reports/streamlit/{종목코드}_{날짜}.pdf` 형식으로 저장된다
- US-304: 사용자는 다운로드 링크를 통해 PDF를 받는다

---

## 4. 기능 요구사항 (Functional Requirements)

### 4.1 핵심 기능

#### F-001: Streamlit 웹 인터페이스

**설명**: 브라우저 기반 직관적 UI 제공

**세부 요구사항**:
- Streamlit 프레임워크 기반
- 반응형 레이아웃 (wide mode)
- 실시간 상태 업데이트
- 세션 상태 관리 (st.session_state)

**페이지 구조**:
```
┌─────────────────────────────────────────────────────────┐
│ 📊 PRISM-INSIGHT AI 주식 분석                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [사이드바]              │ [메인 영역]                    │
│                        │                               │
│ 📝 종목 입력            │ 📊 분석 결과                   │
│ ┌─────────────┐       │                               │
│ │ 종목코드    │       │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ └─────────────┘       │ 📌 핵심 투자 포인트             │
│                        │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ [분석 시작]            │                               │
│                        │ 📈 기술적 분석                 │
│ ━━━━━━━━━━━━━━        │ [차트 및 상세 내용]            │
│                        │                               │
│ 💬 AI 질문             │ 💰 재무 분석                   │
│ ┌─────────────┐       │ [테이블 및 지표]               │
│ │ 질문 입력   │       │                               │
│ └─────────────┘       │ 🎯 투자 전략                   │
│                        │ [AI 의견]                     │
│ [대화 내역]            │                               │
│                        │ 💾 [PDF 다운로드]              │
│                        │                               │
└─────────────────────────────────────────────────────────┘
```

#### F-002: AI 분석 통합

**설명**: 기존 cores/ 모듈을 활용한 분석

**세부 요구사항**:
- **절대 원칙**: cores/ 폴더 수정 금지
- `cores.analysis.analyze_stock()` import 후 호출만
- 분석 중 프로그레스 바 표시
- 완료 후 결과 렌더링

**구현 방법**:
```python
# streamlit_apps/personal_analyzer.py

# ✅ 허용: import만
from cores.analysis import analyze_stock

# ✅ 허용: 호출만
async def run_analysis(code, name):
    result = await analyze_stock(code, name)
    return result

# ❌ 금지: cores/ 파일 수정
# cores/analysis.py를 수정하지 않음!
```

#### F-003: Claude Q&A 에이전트

**설명**: 분석 결과 기반 대화형 질의응답

**세부 요구사항**:
- Streamlit 사이드바에 채팅 UI
- Claude Sonnet 4.5 API 호출
- 분석 결과를 컨텍스트로 제공
- 대화 히스토리 표시

**UI 예시**:
```python
# 사이드바
with st.sidebar:
    st.header("💬 AI 질문")

    # 채팅 히스토리
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # 입력
    if prompt := st.chat_input("궁금한 점을 물어보세요"):
        # Claude API 호출
        answer = qa_agent.ask(prompt, analysis_result)
        st.chat_message("assistant").write(answer)
```

#### F-004: 결과 시각화

**설명**: 분석 결과를 웹 UI로 렌더링

**세부 요구사항**:
- 섹션별 구조화된 표시
- Markdown 렌더링 (기존 보고서 활용)
- 차트 표시 (matplotlib → st.pyplot)
- 테이블 표시 (st.table, st.dataframe)

**섹션 구조**:
```python
# 1. 요약
st.header("📌 핵심 투자 포인트")
st.markdown(result['summary'])

# 2. 기술적 분석
st.header("📈 기술적 분석")
st.markdown(result['technical_analysis'])
if result['chart']:
    st.pyplot(result['chart'])

# 3. 재무 분석
st.header("💰 재무 분석")
st.dataframe(result['financial_table'])

# 4. AI 투자 의견
st.header("🎯 AI 투자 의견")
col1, col2, col3 = st.columns(3)
col1.metric("매수 점수", f"{result['buy_score']}/10")
col2.metric("목표가", f"{result['target_price']:,}원")
col3.metric("손절가", f"{result['stop_loss']:,}원")
```

#### F-005: PDF 다운로드 (선택적)

**설명**: 사용자가 원할 때만 PDF 생성

**세부 요구사항**:
- "PDF 다운로드" 버튼 제공
- 버튼 클릭 시 pdf_converter.py 호출
- 생성된 PDF 다운로드 링크 제공
- 저장 경로: `reports/streamlit/{종목코드}_{timestamp}.pdf`

**구현**:
```python
if st.button("💾 PDF 다운로드"):
    with st.spinner("PDF 생성 중..."):
        # ✅ 허용: 기존 모듈 호출
        from pdf_converter import convert_to_pdf

        pdf_path = convert_to_pdf(
            markdown_content=result['full_report'],
            output_dir="reports/streamlit"
        )

        # 다운로드 링크
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📥 PDF 다운로드",
                data=f,
                file_name=f"{stock_code}_{datetime.now():%Y%m%d}.pdf",
                mime="application/pdf"
            )
```

#### F-006: 세션 관리

**설명**: 분석 이력 및 상태 관리

**세부 요구사항**:
- `st.session_state` 활용
- 분석 이력 저장 (메모리)
- 마지막 분석 결과 보관
- 페이지 새로고침 시 유지

**상태 변수**:
```python
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
```

### 4.2 제외 기능 (기존 앱과의 차이)

❌ **텔레그램 전송**: telegram_bot_agent.py 사용 안 함
❌ **이메일 전송**: email_sender.py 사용 안 함
❌ **자동 PDF 생성**: 선택적으로만 생성
❌ **급등주 트리거**: trigger_batch.py 사용 안 함
❌ **자동매매 실행**: 시뮬레이션만 표시

---

## 5. 비기능 요구사항 (Non-Functional Requirements)

### 5.1 성능 (Performance)

- **분석 시간**: 3분 이내 (기존 시스템과 동일)
- **페이지 로딩**: 2초 이내
- **동시 사용자**: 1명 (개인용)

### 5.2 안정성 (Reliability)

- **에러 처리**: API 실패 시 사용자 친화적 메시지
- **세션 유지**: 브라우저 새로고침 시 상태 유지
- **캐싱**: `@st.cache_data` 활용

### 5.3 사용성 (Usability)

- **학습 곡선**: 즉시 사용 가능 (웹 UI)
- **접근성**: 브라우저만 있으면 사용 가능
- **반응성**: 실시간 피드백 (프로그레스 바, 스피너)

### 5.4 유지보수성 (Maintainability)

- **모듈화**: 단일 파일로 구성 (1,000줄 이하)
- **독립성**: 기존 코드 수정 없이 독립 실행
- **문서화**: 코드 주석 충분

### 5.5 호환성 (Compatibility)

- **OS**: Linux, macOS, Windows
- **Python**: 3.10 이상
- **브라우저**: Chrome, Firefox, Safari, Edge (최신 버전)

---

## 6. 기술 스택

### 6.1 프로그래밍 언어

- **Python 3.10+**: 기존 프로젝트와 동일

### 6.2 핵심 라이브러리

```txt
# 웹 프레임워크
streamlit>=1.30.0

# 기존 의존성 재사용 (수정 없음)
mcp-agent>=0.1.10
openai~=1.64.0
anthropic~=0.64.0
pykrx==1.0.48
matplotlib~=3.10.1
pdfkit>=1.0.0
```

### 6.3 아키텍처 원칙

**절대 원칙**:
```
🚨 기존 코드 수정 금지 🚨

허용:
✅ 새 파일 생성: streamlit_apps/personal_analyzer.py
✅ import만: from cores.analysis import analyze_stock
✅ 호출만: result = await analyze_stock(code, name)

금지:
❌ 기존 파일 수정
❌ 기존 함수 시그니처 변경
❌ 기존 로직 수정
```

---

## 7. 시스템 아키텍처

### 7.1 전체 구조

```
┌────────────────────────────────────────────────────────┐
│     PRISM-INSIGHT Streamlit App (새로운 독립 모듈)      │
│     streamlit_apps/personal_analyzer.py                │
└────────────────────────────────────────────────────────┘
                       │
                       │ import (읽기 전용)
                       │
         ┌─────────────┼─────────────────┐
         │             │                 │
    ┌────▼────┐   ┌───▼────┐      ┌────▼────┐
    │ cores/  │   │ cores/ │      │  pdf_   │
    │analysis │   │agents/ │      │converter│
    └─────────┘   └────────┘      └─────────┘
         │             │                 │
         └─────────┬───┴─────────────────┘
                   │
           ┌───────▼────────┐
           │  MCP Servers   │
           │  pykrx, etc.   │
           └────────────────┘
```

### 7.2 디렉토리 구조

```
prism-insight/
├── streamlit_apps/                    # ✨ 새로운 디렉토리
│   ├── __init__.py
│   ├── personal_analyzer.py           # 메인 앱 파일
│   ├── qa_agent.py                    # Claude Q&A 에이전트
│   └── config.py                      # Streamlit 설정
│
├── cores/                             # ❌ 수정 금지
│   ├── analysis.py                    # ✅ import만
│   └── agents/                        # ✅ import만
│
├── examples/streamlit/                # ❌ 수정 금지
│   └── app_modern.py                  # ✅ 참고만
│
├── reports/streamlit/                 # PDF 저장 경로
│
├── docs/
│   ├── PRD-STREAMLIT-STOCK-ANALYZER.md
│   ├── STREAMLIT-ARCHITECTURE.md
│   ├── STREAMLIT-USER-GUIDE.md
│   └── STREAMLIT-DEVELOPMENT-GUIDE.md
│
└── run_streamlit.sh                   # 실행 스크립트
```

### 7.3 파일 역할

| 파일 | 책임 | 수정 여부 |
|------|------|-----------|
| `streamlit_apps/personal_analyzer.py` | 메인 앱 로직 | ✅ 새로 생성 |
| `streamlit_apps/qa_agent.py` | Claude Q&A | ✅ 새로 생성 |
| `streamlit_apps/config.py` | 설정 관리 | ✅ 새로 생성 |
| `cores/analysis.py` | 분석 로직 | ❌ 읽기 전용 |
| `examples/streamlit/app_modern.py` | 기존 앱 | ❌ 참고만 |

---

## 8. 데이터 흐름

### 8.1 분석 플로우

```
사용자 입력 (종목코드)
    │
    ├─> [Streamlit UI]
    │       │
    │       ├─> st.text_input("종목코드")
    │       ├─> st.button("분석 시작")
    │       └─> st.spinner("분석 중...")
    │
    ├─> [cores/analysis.py] ✅ import만
    │       │
    │       └─> analyze_stock(code, name)
    │               │
    │               ├─> 6개 분석 에이전트
    │               ├─> 투자 전략 에이전트
    │               └─> 매수 전문가 (GPT-5)
    │
    ├─> [결과 렌더링]
    │       │
    │       ├─> st.markdown(summary)
    │       ├─> st.pyplot(chart)
    │       ├─> st.dataframe(table)
    │       └─> st.metric(score)
    │
    ├─> [PDF 다운로드] (선택)
    │       │
    │       └─> pdf_converter.py ✅ import만
    │
    └─> [Claude Q&A] (선택)
            │
            └─> qa_agent.ask(question, context)
```

---

## 9. UI/UX 설계

### 9.1 메인 페이지 레이아웃

```python
# streamlit_apps/personal_analyzer.py

import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="PRISM-INSIGHT AI 주식 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
with st.sidebar:
    st.title("📊 주식 분석")

    # 종목 입력
    stock_input = st.text_input(
        "종목코드 또는 종목명",
        placeholder="예: 005930 또는 삼성전자"
    )

    analyze_btn = st.button("🔍 분석 시작", type="primary")

    st.divider()

    # Q&A 섹션
    st.header("💬 AI 질문")
    # [채팅 UI]

# 메인 영역
st.title("🤖 PRISM-INSIGHT AI 주식 분석")

if analyze_btn:
    # 분석 실행
    with st.spinner("분석 중... (2~3분 소요)"):
        result = run_analysis(stock_input)

    # 결과 표시
    display_result(result)
```

### 9.2 결과 표시 예시

```python
def display_result(result):
    """분석 결과 렌더링"""

    # 상단 요약
    st.success("✅ 분석 완료!")

    col1, col2, col3 = st.columns(3)
    col1.metric("현재가", f"{result['price']:,}원", f"{result['change']}%")
    col2.metric("매수 점수", f"{result['buy_score']}/10")
    col3.metric("목표가", f"{result['target_price']:,}원")

    # 탭으로 섹션 구분
    tab1, tab2, tab3, tab4 = st.tabs([
        "📌 요약",
        "📈 기술적 분석",
        "💰 재무 분석",
        "🎯 투자 전략"
    ])

    with tab1:
        st.markdown(result['summary'])

    with tab2:
        st.markdown(result['technical_analysis'])
        if result['chart']:
            st.pyplot(result['chart'])

    with tab3:
        st.dataframe(result['financial_table'])

    with tab4:
        st.markdown(result['investment_strategy'])

    # PDF 다운로드
    st.divider()
    if st.button("💾 PDF 다운로드"):
        generate_pdf(result)
```

---

## 10. 개발 로드맵

### Phase 1: 기본 구조 (1일차)

**목표**: Streamlit 앱 기본 틀 완성

**작업 항목**:
- [x] 디렉토리 생성: `streamlit_apps/`
- [ ] `personal_analyzer.py` 파일 생성
- [ ] 페이지 레이아웃 구성
- [ ] 사이드바 입력 UI 구현
- [ ] 메인 영역 레이아웃 구성

**산출물**:
- `streamlit_apps/personal_analyzer.py` (기본 틀)

### Phase 2: 분석 통합 (1일차)

**목표**: cores/ 모듈 연동

**작업 항목**:
- [ ] `cores.analysis` import
- [ ] `analyze_stock()` 호출 로직
- [ ] 프로그레스 바 표시
- [ ] 결과 렌더링 함수
- [ ] 에러 핸들링

**주의사항**:
```python
# ✅ 올바른 방법
from cores.analysis import analyze_stock
result = await analyze_stock(code, name)

# ❌ 잘못된 방법
# cores/analysis.py 파일을 수정하지 않음!
```

**산출물**:
- 분석 기능 완성

### Phase 3: Q&A 에이전트 (2일차)

**목표**: Claude AI 통합

**작업 항목**:
- [ ] `qa_agent.py` 생성
- [ ] Claude API 클라이언트 구현
- [ ] 사이드바 채팅 UI
- [ ] 대화 히스토리 관리
- [ ] 컨텍스트 제공 로직

**산출물**:
- `streamlit_apps/qa_agent.py`
- 채팅 기능 완성

### Phase 4: UI 개선 및 PDF (2일차)

**목표**: 사용자 경험 향상

**작업 항목**:
- [ ] 탭 기반 결과 표시
- [ ] 차트 시각화
- [ ] 테이블 포맷팅
- [ ] PDF 다운로드 버튼
- [ ] 로딩 애니메이션

**산출물**:
- 완성된 UI

### Phase 5: 테스트 및 문서 (3일차)

**목표**: 안정화 및 문서화

**작업 항목**:
- [ ] 수동 테스트
- [ ] 버그 수정
- [ ] 사용자 가이드 작성
- [ ] README 업데이트
- [ ] 실행 스크립트 작성

**산출물**:
- 배포 가능한 앱

**총 예상 기간: 2~3일**

---

## 11. 성공 지표 (Success Metrics)

### 11.1 개발 완성도

- ✅ 기존 코드 수정 0건
- ✅ 모든 핵심 기능 구현
- ✅ 버그 없이 안정적 실행

### 11.2 성능 지표

- ⏱️ 분석 완료: 3분 이내
- 🖱️ UI 반응성: 즉시
- 💾 PDF 생성: 10초 이내

### 11.3 사용성 지표

- 📖 학습 시간: 0분 (즉시 사용)
- 🎯 오류 입력 처리: 사용자 친화적 메시지
- 🔁 세션 안정성: 새로고침 시 유지

---

## 12. 위험 관리 (Risk Management)

### 12.1 기술적 위험

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| API 호출 실패 | 중 | 중 | try-except + 사용자 메시지 |
| 비동기 처리 오류 | 낮 | 중 | asyncio.run() 사용 |
| 세션 상태 손실 | 낮 | 낮 | st.session_state 활용 |

### 12.2 개발 위험

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| 기존 코드 실수로 수정 | 중 | 높음 | Git diff 철저히 확인 |
| import 경로 오류 | 중 | 낮음 | sys.path 설정 |

---

## 13. 제약 사항 및 전제 조건

### 13.1 절대 제약 사항

```
🚨 기존 코드 수정 절대 금지 🚨

금지 목록:
❌ cores/ 폴더 내 모든 파일
❌ examples/streamlit/app_modern.py
❌ telegram_*.py
❌ pdf_converter.py
❌ stock_analysis_orchestrator.py
❌ 기타 모든 기존 파일

위반 시:
→ 커밋 거부
→ 코드 리뷰 탈락
→ 처음부터 재작업
```

### 13.2 사용 전제 조건

- ✅ Python 3.10 이상 설치
- ✅ MCP 서버 구성 완료
- ✅ OpenAI API 키 (GPT-4.1, GPT-5)
- ✅ Anthropic API 키 (Claude Sonnet 4.5)
- ✅ 인터넷 연결

---

## 14. 부록

### 14.1 파일 구조 예시

```python
# streamlit_apps/personal_analyzer.py
"""
개인용 주식 AI 분석 Streamlit 앱

⚠️ 주의: 기존 코드를 수정하지 않습니다!
✅ cores/ 모듈은 import만 합니다.
"""

import streamlit as st
import asyncio

# ✅ 허용: import만
from cores.analysis import analyze_stock

# ✅ 허용: 새로운 함수 생성
async def run_analysis(code: str, name: str):
    """분석 실행"""
    result = await analyze_stock(code, name)
    return result

# ✅ 허용: Streamlit UI
def main():
    st.title("📊 주식 분석")
    # ...
```

### 14.2 실행 스크립트

```bash
#!/bin/bash
# run_streamlit.sh

cd "$(dirname "$0")"
streamlit run streamlit_apps/personal_analyzer.py --server.port 8501
```

**실행 방법**:
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

### 14.3 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2025-11-09 | 초안 작성 (TUI → Streamlit 전환) | AI Assistant |

---

## 15. 승인

본 PRD는 다음 문서들과 함께 검토되어야 합니다:
- [ ] STREAMLIT-ARCHITECTURE.md (시스템 설계)
- [ ] STREAMLIT-USER-GUIDE.md (사용자 가이드)
- [ ] STREAMLIT-DEVELOPMENT-GUIDE.md (개발자 가이드)

**문서 상태**: ✅ 초안 완료, 검토 대기 중

---

**문서 끝**
