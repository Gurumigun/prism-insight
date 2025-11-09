"""
개인용 주식 AI 분석 Streamlit 앱

⚠️ 주의사항:
1. 기존 코드를 절대 수정하지 않습니다
2. cores/ 모듈은 import만 합니다
3. 새로운 기능만 작성합니다

작성일: 2025-11-09
버전: 1.0.0
"""

import streamlit as st
import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ✅ 허용: 새 모듈 import
from streamlit_apps.utils import (
    parse_stock_input,
    format_currency,
    format_percentage,
    get_current_timestamp
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_page():
    """페이지 설정 및 스타일"""
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
        h1 {
            color: #1E293B;
            font-weight: 700;
        }
        .stButton>button {
            width: 100%;
        }
        .stButton>button[kind="primary"] {
            background-color: #4CAF50;
            color: white;
        }
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 세션 상태 초기화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_session_state():
    """세션 상태 초기화"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'qa_agent' not in st.session_state:
        try:
            from streamlit_apps.qa_agent import QAAgent
            st.session_state.qa_agent = QAAgent()
        except Exception as e:
            st.session_state.qa_agent = None
            st.session_state.qa_error = str(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 분석 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_analysis(stock_code: str, stock_name: str) -> dict:
    """
    분석 실행 (기존 cores/analysis.py 호출)

    ⚠️ 주의: cores/analysis.py를 수정하지 않습니다!
    ✅ import 후 호출만 합니다.

    Args:
        stock_code: 종목코드
        stock_name: 종목명

    Returns:
        분석 결과 딕셔너리
    """
    try:
        # ✅ 허용: 기존 모듈 import (수정 안 함)
        from cores.analysis import analyze_stock

        # ✅ 허용: 기존 함수 호출
        result = await analyze_stock(
            company_code=stock_code,
            company_name=stock_name
        )

        return result

    except ImportError as e:
        raise ImportError(f"cores.analysis 모듈을 찾을 수 없습니다: {str(e)}")
    except Exception as e:
        raise Exception(f"분석 실패: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 결과 표시
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def display_result(result: dict):
    """분석 결과 표시"""

    st.success("✅ 분석 완료!")

    # 상단 메트릭
    col1, col2, col3 = st.columns(3)

    with col1:
        current_price = result.get('current_price', 0)
        change_percent = result.get('change_percent', 0)
        st.metric(
            "현재가",
            format_currency(current_price) if current_price else "정보 없음",
            format_percentage(change_percent) if change_percent else None
        )

    with col2:
        buy_score = result.get('buy_score', 0)
        st.metric(
            "매수 점수",
            f"{buy_score}/10" if buy_score else "정보 없음"
        )

    with col3:
        target_price = result.get('target_price', 0)
        st.metric(
            "목표가",
            format_currency(target_price) if target_price else "정보 없음"
        )

    st.divider()

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
        st.markdown(result.get('summary', '분석 결과가 없습니다.'))

    with tabs[1]:
        st.markdown(result.get('technical_analysis', '분석 결과가 없습니다.'))

    with tabs[2]:
        st.markdown(result.get('trading_flow', '분석 결과가 없습니다.'))

    with tabs[3]:
        st.markdown(result.get('financial_analysis', '분석 결과가 없습니다.'))

    with tabs[4]:
        st.markdown(result.get('industry_analysis', '분석 결과가 없습니다.'))

    with tabs[5]:
        st.markdown(result.get('news_analysis', '분석 결과가 없습니다.'))

    with tabs[6]:
        st.markdown(result.get('market_analysis', '분석 결과가 없습니다.'))

    with tabs[7]:
        st.markdown(result.get('investment_strategy', '분석 결과가 없습니다.'))

    # PDF 다운로드
    st.divider()
    render_pdf_download(result)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. PDF 다운로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_pdf_download(result: dict):
    """PDF 다운로드 버튼"""

    if st.button("💾 PDF 다운로드", use_container_width=True):
        with st.spinner("PDF 생성 중..."):
            try:
                # ✅ 허용: 기존 함수 호출 (수정 안 함)
                from pdf_converter import markdown_to_pdf

                # 마크다운 내용
                markdown_content = result.get('full_report', '')

                if not markdown_content:
                    st.error("보고서 내용이 없습니다.")
                    return

                # 파일명 생성
                company_code = result.get('company_code', 'unknown')
                timestamp = get_current_timestamp()
                filename = f"{company_code}_{timestamp}.pdf"

                # PDF 저장 경로
                pdf_dir = Path("reports/streamlit")
                pdf_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = pdf_dir / filename

                # PDF 생성
                markdown_to_pdf(
                    markdown_content,
                    str(pdf_path)
                )

                # 다운로드 링크 제공
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 다운로드",
                        data=f,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                st.success(f"✅ PDF 생성 완료: {pdf_path}")

            except ImportError:
                st.error("PDF 변환 모듈을 찾을 수 없습니다. pdf_converter.py를 확인하세요.")
            except Exception as e:
                st.error(f"PDF 생성 실패: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Q&A 섹션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_qa_section():
    """Q&A 섹션 렌더링"""

    st.header("💬 AI 질문")

    # QA 에이전트 에러 체크
    if st.session_state.qa_agent is None:
        st.warning(f"Q&A 기능을 사용할 수 없습니다.")
        if hasattr(st.session_state, 'qa_error'):
            st.error(st.session_state.qa_error)
        return

    # 채팅 히스토리 표시
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 입력
    if prompt := st.chat_input("궁금한 점을 물어보세요"):
        # 분석 결과 확인
        if not st.session_state.analysis_result:
            st.warning("먼저 종목을 분석해주세요.")
            return

        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        # Claude에게 질문
        with st.spinner("Claude가 생각하는 중..."):
            try:
                answer = asyncio.run(
                    st.session_state.qa_agent.ask(
                        question=prompt,
                        analysis_context=st.session_state.analysis_result.get('full_report', '')
                    )
                )

                # AI 답변 추가
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

                st.rerun()

            except Exception as e:
                st.error(f"Q&A 실패: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

        st.divider()

        # Q&A 섹션
        render_qa_section()

        return stock_input, analyze_btn


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """메인 함수"""

    # 페이지 설정
    setup_page()

    # 세션 초기화
    init_session_state()

    # 사이드바
    stock_input, analyze_btn = render_sidebar()

    # 메인 영역
    st.title("🤖 PRISM-INSIGHT AI 주식 분석")
    st.caption("12개 전문 AI 에이전트의 협업 분석")

    # 분석 실행
    if analyze_btn and stock_input:
        # 입력 파싱
        code, name = parse_stock_input(stock_input)

        if code and name:
            st.info(f"📊 {name}({code}) 분석을 시작합니다...")

            with st.spinner(f"분석 중... (2~3분 소요)"):
                try:
                    # ✅ 허용: 기존 함수 호출
                    result = asyncio.run(run_analysis(code, name))

                    # 세션에 저장
                    st.session_state.analysis_result = result

                    # 결과 표시
                    display_result(result)

                except Exception as e:
                    st.error(f"❌ 분석 실패: {str(e)}")
                    st.info("💡 다음을 확인해주세요:\n- API 키 설정 (.env 파일)\n- 인터넷 연결\n- 올바른 종목코드")

        else:
            st.error("❌ 올바른 종목코드 또는 종목명을 입력하세요.")
            st.info("💡 예시: 005930, 삼성전자, SK하이닉스")

    # 이전 결과 표시
    elif st.session_state.analysis_result:
        display_result(st.session_state.analysis_result)

    # 처음 실행 시 안내
    else:
        st.info("""
        👋 환영합니다!

        **사용 방법:**
        1. 왼쪽 사이드바에서 종목코드 또는 종목명 입력
        2. "🔍 분석 시작" 버튼 클릭
        3. 2~3분 후 분석 결과 확인
        4. 필요시 Claude AI에게 추가 질문
        5. PDF 다운로드 (선택)

        **지원 종목:** KOSPI/KOSDAQ 전 종목
        """)


if __name__ == "__main__":
    main()
