# PRISM-INSIGHT Streamlit 개발자 가이드

## 📚 목차

1. [개발 환경 설정](#1-개발-환경-설정)
2. [개발 원칙](#2-개발-원칙)
3. [구현 가이드](#3-구현-가이드)
4. [코드 예시](#4-코드-예시)
5. [테스트](#5-테스트)
6. [배포](#6-배포)

---

## ⚠️ 가장 중요한 원칙

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 절대 원칙: 기존 코드를 수정하지 마세요! 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

이 프로젝트는 기존 시스템의 기능을 활용하되,
단 한 줄의 기존 코드도 수정하지 않습니다.

✅ ALLOWED (허용)
  1. 새 파일 생성
     → streamlit_apps/personal_analyzer.py
     → streamlit_apps/qa_agent.py
     → streamlit_apps/utils.py

  2. 기존 모듈 import
     → from cores.analysis import analyze_stock

  3. 기존 함수 호출
     → result = await analyze_stock(code, name)

❌ FORBIDDEN (절대 금지)
  1. 기존 파일 수정
     → cores/analysis.py 수정 금지
     → examples/streamlit/app_modern.py 수정 금지
     → pdf_converter.py 수정 금지

  2. 기존 함수 시그니처 변경
     → analyze_stock() 파라미터 추가 금지

  3. Monkey Patching
     → cores.analysis.some_func = new_func  # 금지!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
커밋 전 반드시 확인:
  $ git diff cores/
  $ git diff examples/
  $ git diff pdf_converter.py

  → 출력이 비어있어야 함 (No changes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 1. 개발 환경 설정

### 1.1 필수 요구사항

- **Python**: 3.10 이상
- **Git**: 2.0 이상
- **에디터**: VS Code 권장

### 1.2 저장소 설정

```bash
cd prism-insight

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate  # Windows

# 기존 의존성 설치
pip install -r requirements.txt

# Streamlit 추가 설치
pip install streamlit>=1.30.0
```

### 1.3 API 키 설정

```bash
# .env 파일 확인
cat .env
```

**.env 필수 항목**:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
PERPLEXITY_API_KEY=pplx-...
```

---

## 2. 개발 원칙

### 2.1 Read-Only Import Pattern

**✅ 올바른 방법**:
```python
# streamlit_apps/personal_analyzer.py

# 1. Import만 (읽기 전용)
from cores.analysis import analyze_stock

# 2. 호출만
async def run_analysis(code, name):
    result = await analyze_stock(code, name)
    return result
```

**❌ 잘못된 방법**:
```python
# ❌ 금지 1: 기존 파일 수정
# cores/analysis.py 파일을 열어서 수정  ← 절대 금지!

# ❌ 금지 2: Monkey Patching
import cores.analysis as ca
ca.analyze_stock = my_custom_function  ← 절대 금지!

# ❌ 금지 3: 파라미터 추가
# analyze_stock() 함수에 새 파라미터 추가  ← 절대 금지!
```

### 2.2 Adapter Pattern

기존 시스템과 새 UI 사이에 어댑터 레이어 구축:

```python
# streamlit_apps/personal_analyzer.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Adapter Layer (우리가 작성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_analysis(code: str, name: str) -> dict:
    """
    기존 analyze_stock() 호출 래퍼

    ⚠️ 주의: cores/analysis.py를 수정하지 않습니다!
    """
    # ✅ import만 사용
    from cores.analysis import analyze_stock

    # ✅ 호출만
    result = await analyze_stock(code, name)

    # ✅ 새로운 로직 추가 (어댑터에서만)
    result['ui_formatted'] = format_for_ui(result)

    return result


def format_for_ui(result: dict) -> dict:
    """UI용 포맷팅 (새 함수)"""
    # 여기서만 로직 추가 가능
    pass
```

### 2.3 파일 구조 원칙

```
✅ 새로 생성 가능
streamlit_apps/
├── __init__.py              ✅
├── personal_analyzer.py     ✅
├── qa_agent.py              ✅
└── utils.py                 ✅

❌ 수정 금지
cores/
├── analysis.py              ❌ 읽기 전용
└── agents/                  ❌ 읽기 전용

examples/streamlit/
└── app_modern.py            ❌ 참고만 (수정 금지)

pdf_converter.py             ❌ 읽기 전용
telegram_bot_agent.py        ❌ 사용 안 함
```

---

## 3. 구현 가이드

### 3.1 Phase 1: 프로젝트 구조 생성 (30분)

#### Task 1-1: 디렉토리 생성
```bash
# 새 디렉토리 생성
mkdir -p streamlit_apps
mkdir -p reports/streamlit

# 파일 생성
touch streamlit_apps/__init__.py
touch streamlit_apps/personal_analyzer.py
touch streamlit_apps/qa_agent.py
touch streamlit_apps/utils.py
```

#### Task 1-2: __init__.py 작성
```python
# streamlit_apps/__init__.py
"""
PRISM-INSIGHT Streamlit 앱

⚠️ 주의: 기존 코드를 수정하지 않는 새로운 모듈입니다.
"""

__version__ = "1.0.0"
```

#### Task 1-3: 실행 스크립트 작성
```bash
# run_streamlit.sh
#!/bin/bash

cd "$(dirname "$0")"
streamlit run streamlit_apps/personal_analyzer.py \
    --server.port 8501 \
    --server.headless true
```

```bash
chmod +x run_streamlit.sh
```

### 3.2 Phase 2: 기본 UI 구현 (2시간)

#### Task 2-1: 페이지 설정
```python
# streamlit_apps/personal_analyzer.py

import streamlit as st

def setup_page():
    """페이지 설정"""
    st.set_page_config(
        page_title="PRISM-INSIGHT AI 주식 분석",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 커스텀 CSS
    st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
```

#### Task 2-2: 사이드바 구현
```python
def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("📊 주식 분석")

        # 종목 입력
        stock_input = st.text_input(
            "종목코드 또는 종목명",
            placeholder="예: 005930 또는 삼성전자",
            help="6자리 종목코드 또는 종목명을 입력하세요"
        )

        # 분석 버튼
        analyze_btn = st.button(
            "🔍 분석 시작",
            type="primary",
            use_container_width=True
        )

        return stock_input, analyze_btn
```

#### Task 2-3: 메인 영역 구현
```python
def main():
    """메인 함수"""
    setup_page()

    # 사이드바
    stock_input, analyze_btn = render_sidebar()

    # 메인 영역
    st.title("🤖 PRISM-INSIGHT AI 주식 분석")
    st.caption("12개 전문 AI 에이전트의 협업 분석")

    if analyze_btn and stock_input:
        st.info("분석 기능은 다음 단계에서 구현합니다.")


if __name__ == "__main__":
    main()
```

#### Task 2-4: 실행 테스트
```bash
streamlit run streamlit_apps/personal_analyzer.py
```

브라우저에서 `http://localhost:8501` 확인

### 3.3 Phase 3: 분석 통합 (3시간)

#### Task 3-1: utils.py 구현
```python
# streamlit_apps/utils.py

from typing import Tuple, Optional
from pykrx import stock as pykrx_stock


def parse_stock_input(user_input: str) -> Tuple[Optional[str], Optional[str]]:
    """
    사용자 입력 파싱

    Args:
        user_input: 종목코드 또는 종목명

    Returns:
        (종목코드, 종목명) 튜플
    """
    user_input = user_input.strip()

    # 종목코드로 검색
    if user_input.isdigit() and len(user_input) == 6:
        try:
            name = pykrx_stock.get_market_ticker_name(user_input)
            if name:
                return (user_input, name)
        except:
            pass

    # 종목명으로 검색
    try:
        tickers = pykrx_stock.get_market_ticker_list(market="ALL")
        for ticker in tickers:
            ticker_name = pykrx_stock.get_market_ticker_name(ticker)
            if user_input in ticker_name:
                return (ticker, ticker_name)
    except:
        pass

    return (None, None)


def format_currency(value: int) -> str:
    """금액 포맷팅"""
    return f"{value:,}원"
```

#### Task 3-2: 분석 함수 구현
```python
# streamlit_apps/personal_analyzer.py

import asyncio
from streamlit_apps.utils import parse_stock_input

# ✅ 허용: import만
from cores.analysis import analyze_stock


async def run_analysis(code: str, name: str) -> dict:
    """
    분석 실행

    ⚠️ 주의: cores/analysis.py를 수정하지 않습니다!
    ✅ import 후 호출만 합니다.

    Args:
        code: 종목코드
        name: 종목명

    Returns:
        분석 결과 딕셔너리
    """
    # ✅ 허용: 기존 함수 호출
    result = await analyze_stock(
        company_code=code,
        company_name=name
    )

    return result
```

#### Task 3-3: main() 업데이트
```python
def main():
    """메인 함수"""
    setup_page()

    # 세션 상태 초기화
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    # 사이드바
    stock_input, analyze_btn = render_sidebar()

    # 메인 영역
    st.title("🤖 PRISM-INSIGHT AI 주식 분석")

    if analyze_btn and stock_input:
        # 입력 파싱
        code, name = parse_stock_input(stock_input)

        if code and name:
            with st.spinner(f"{name}({code}) 분석 중... (2~3분 소요)"):
                try:
                    # ✅ 허용: 기존 함수 호출
                    result = asyncio.run(run_analysis(code, name))

                    # 세션에 저장
                    st.session_state.analysis_result = result

                    # 성공 메시지
                    st.success("✅ 분석 완료!")

                    # 결과 표시 (다음 단계에서 구현)
                    st.json(result)  # 임시

                except Exception as e:
                    st.error(f"분석 실패: {str(e)}")
        else:
            st.error("올바른 종목코드 또는 종목명을 입력하세요.")
```

### 3.4 Phase 4: 결과 표시 (2시간)

#### Task 4-1: display_result() 구현
```python
def display_result(result: dict):
    """분석 결과 표시"""

    st.success("✅ 분석 완료!")

    # 상단 메트릭
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "현재가",
            format_currency(result.get('current_price', 0)),
            f"{result.get('change_percent', 0):+.2f}%"
        )
    with col2:
        st.metric(
            "매수 점수",
            f"{result.get('buy_score', 0)}/10"
        )
    with col3:
        st.metric(
            "목표가",
            format_currency(result.get('target_price', 0))
        )

    # 탭으로 섹션 구분
    tabs = st.tabs([
        "📌 요약",
        "📈 기술적 분석",
        "💼 거래 동향",
        "💰 재무 분석",
        "🏢 산업 분석",
        "📰 뉴스",
        "📊 시장 분석",
        "🎯 투자 전략"
    ])

    with tabs[0]:
        st.markdown(result.get('summary', ''))

    with tabs[1]:
        st.markdown(result.get('technical_analysis', ''))

    with tabs[2]:
        st.markdown(result.get('trading_flow', ''))

    with tabs[3]:
        st.markdown(result.get('financial_analysis', ''))

    with tabs[4]:
        st.markdown(result.get('industry_analysis', ''))

    with tabs[5]:
        st.markdown(result.get('news_analysis', ''))

    with tabs[6]:
        st.markdown(result.get('market_analysis', ''))

    with tabs[7]:
        st.markdown(result.get('investment_strategy', ''))
```

#### Task 4-2: main()에 추가
```python
def main():
    # ... (이전 코드)

    # 결과 표시
    if st.session_state.analysis_result:
        display_result(st.session_state.analysis_result)
```

### 3.5 Phase 5: Q&A 기능 (2시간)

#### Task 5-1: qa_agent.py 구현
```python
# streamlit_apps/qa_agent.py

import anthropic
from typing import List, Dict


class QAAgent:
    """Claude 기반 Q&A 에이전트"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-5-20250929"
        self.conversation_history: List[Dict] = []

    async def ask(self, question: str, analysis_context: str) -> str:
        """질문에 대한 답변 생성"""

        system_prompt = f"""
당신은 주식 투자 전문가입니다.

다음은 AI가 분석한 주식 보고서입니다:

{analysis_context}

사용자의 질문에 대해 이 보고서를 기반으로 답변해주세요.
"""

        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=self.conversation_history
        )

        answer = response.content[0].text

        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        return answer
```

#### Task 5-2: 사이드바에 Q&A 추가
```python
def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("📊 주식 분석")

        # 종목 입력
        stock_input = st.text_input(...)
        analyze_btn = st.button(...)

        st.divider()

        # Q&A 섹션
        st.header("💬 AI 질문")
        render_qa_section()

        return stock_input, analyze_btn


def render_qa_section():
    """Q&A 섹션"""
    # 세션 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'qa_agent' not in st.session_state:
        from streamlit_apps.qa_agent import QAAgent
        st.session_state.qa_agent = QAAgent()

    # 채팅 히스토리 표시
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 입력
    if prompt := st.chat_input("궁금한 점을 물어보세요"):
        # 사용자 메시지
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        # Claude에게 질문
        if st.session_state.analysis_result:
            import asyncio
            answer = asyncio.run(
                st.session_state.qa_agent.ask(
                    question=prompt,
                    analysis_context=st.session_state.analysis_result['full_report']
                )
            )

            # AI 답변
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

            st.rerun()
        else:
            st.warning("먼저 종목을 분석해주세요.")
```

### 3.6 Phase 6: PDF 다운로드 (1시간)

#### Task 6-1: PDF 다운로드 버튼 추가
```python
def render_pdf_download(result: dict):
    """PDF 다운로드"""

    if st.button("💾 PDF 다운로드", use_container_width=True):
        with st.spinner("PDF 생성 중..."):
            try:
                # ✅ 허용: 기존 함수 호출
                from pdf_converter import convert_to_pdf
                from datetime import datetime

                pdf_path = convert_to_pdf(
                    markdown_content=result['full_report'],
                    output_dir="reports/streamlit"
                )

                # 다운로드 링크
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 다운로드",
                        data=f,
                        file_name=f"{result['company_code']}_{datetime.now():%Y%m%d}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                st.success(f"✅ PDF 생성 완료: {pdf_path}")

            except Exception as e:
                st.error(f"PDF 생성 실패: {str(e)}")
```

#### Task 6-2: display_result()에 추가
```python
def display_result(result: dict):
    # ... (탭 표시)

    # PDF 다운로드
    st.divider()
    render_pdf_download(result)
```

---

## 4. 코드 예시

### 4.1 완성된 personal_analyzer.py

```python
"""
개인용 주식 AI 분석 Streamlit 앱

⚠️ 주의사항:
1. 기존 코드를 절대 수정하지 않습니다
2. cores/ 모듈은 import만 합니다
3. 새로운 기능만 작성합니다

작성자: [이름]
작성일: 2025-11-09
"""

import streamlit as st
import asyncio
from datetime import datetime

# ✅ 허용: 기존 모듈 import (수정 안 함)
from cores.analysis import analyze_stock
from pdf_converter import convert_to_pdf

# ✅ 허용: 새 모듈 import
from streamlit_apps.qa_agent import QAAgent
from streamlit_apps.utils import format_currency, parse_stock_input


def setup_page():
    """페이지 설정"""
    st.set_page_config(
        page_title="PRISM-INSIGHT AI 주식 분석",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def init_session_state():
    """세션 상태 초기화"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'qa_agent' not in st.session_state:
        st.session_state.qa_agent = QAAgent()


async def run_analysis(code: str, name: str) -> dict:
    """
    분석 실행

    ⚠️ 주의: cores/analysis.py를 수정하지 않습니다!
    """
    result = await analyze_stock(code, name)
    return result


def display_result(result: dict):
    """분석 결과 표시"""
    # [이전 코드 참고]
    pass


def render_pdf_download(result: dict):
    """PDF 다운로드"""
    # [이전 코드 참고]
    pass


def render_qa_section():
    """Q&A 섹션"""
    # [이전 코드 참고]
    pass


def render_sidebar():
    """사이드바"""
    with st.sidebar:
        st.title("📊 주식 분석")

        stock_input = st.text_input(
            "종목코드 또는 종목명",
            placeholder="예: 005930"
        )

        analyze_btn = st.button(
            "🔍 분석 시작",
            type="primary",
            use_container_width=True
        )

        st.divider()
        render_qa_section()

        return stock_input, analyze_btn


def main():
    """메인 함수"""
    setup_page()
    init_session_state()

    stock_input, analyze_btn = render_sidebar()

    st.title("🤖 PRISM-INSIGHT AI 주식 분석")

    if analyze_btn and stock_input:
        code, name = parse_stock_input(stock_input)

        if code and name:
            with st.spinner(f"{name}({code}) 분석 중..."):
                try:
                    result = asyncio.run(run_analysis(code, name))
                    st.session_state.analysis_result = result
                    display_result(result)
                except Exception as e:
                    st.error(f"분석 실패: {str(e)}")
        else:
            st.error("올바른 종목코드를 입력하세요.")

    elif st.session_state.analysis_result:
        display_result(st.session_state.analysis_result)


if __name__ == "__main__":
    main()
```

---

## 5. 테스트

### 5.1 수동 테스트

```bash
# 실행
streamlit run streamlit_apps/personal_analyzer.py

# 테스트 시나리오
1. 종목 입력: 005930
2. 분석 실행
3. 결과 확인
4. Q&A 테스트
5. PDF 다운로드
```

### 5.2 코드 수정 확인

```bash
# 기존 파일 수정 여부 확인 (중요!)
git diff cores/
git diff examples/
git diff pdf_converter.py

# 출력이 비어있어야 함
```

---

## 6. 배포

### 6.1 체크리스트

- [ ] `streamlit_apps/` 디렉토리 생성
- [ ] `personal_analyzer.py` 작성
- [ ] `qa_agent.py` 작성
- [ ] `utils.py` 작성
- [ ] `run_streamlit.sh` 작성
- [ ] 기존 코드 수정 여부 확인 (git diff)
- [ ] 테스트 실행
- [ ] 문서 작성

### 6.2 커밋

```bash
git add streamlit_apps/
git add reports/streamlit/.gitkeep
git add run_streamlit.sh

git commit -m "feat(streamlit): Add personal stock analyzer app

- New Streamlit web app for personal use
- Claude AI Q&A integration
- PDF download feature
- No modifications to existing code"

git push
```

---

**개발 완료 예상 시간: 10~12시간 (1~2일)**

**문서 끝**
