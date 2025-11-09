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

async def run_analysis(stock_code: str, stock_name: str, progress_callback=None) -> dict:
    """
    분석 실행 (기존 cores/analysis.py 호출)

    ⚠️ 주의: cores/analysis.py를 수정하지 않습니다!
    ✅ import 후 호출만 합니다.

    Args:
        stock_code: 종목코드
        stock_name: 종목명
        progress_callback: 진행 상황 콜백 함수

    Returns:
        분석 결과 딕셔너리
    """
    try:
        # ✅ 허용: 기존 모듈 import (수정 안 함)
        from cores.analysis import analyze_stock
        import asyncio

        # 분석 단계 정의
        analysis_steps = [
            ("데이터 수집 준비", 5),
            ("주가 및 거래량 분석 (Technical Analyst)", 20),
            ("투자자 거래 동향 분석 (Trading Flow Analyst)", 35),
            ("재무 분석 (Financial Analyst)", 50),
            ("산업 분석 (Industry Analyst)", 65),
            ("뉴스 분석 (Information Analyst)", 75),
            ("시장 분석 (Market Analyst)", 85),
            ("투자 전략 수립 (Investment Strategist)", 95),
            ("최종 보고서 생성", 100),
        ]

        # 분석 태스크 시작
        analysis_task = asyncio.create_task(
            analyze_stock(
                company_code=stock_code,
                company_name=stock_name
            )
        )

        # 진행률 시뮬레이션 (cores/analysis.py는 수정 불가이므로)
        if progress_callback:
            for step_name, progress in analysis_steps[:-1]:
                if not analysis_task.done():
                    progress_callback(step_name, progress)
                    await asyncio.sleep(15)  # 각 단계당 약 15초 예상

        # 분석 완료 대기
        markdown_result = await analysis_task

        # 마지막 진행률
        if progress_callback:
            progress_callback("최종 보고서 생성", 100)

        # 결과를 딕셔너리로 변환
        result = {
            'company_code': stock_code,
            'company_name': stock_name,
            'full_report': markdown_result,
            # 마크다운에서 섹션 추출 (간단한 파싱)
            'summary': extract_section(markdown_result, '핵심 투자 포인트'),
            'technical_analysis': extract_section(markdown_result, '주가 및 거래량 분석'),
            'trading_flow': extract_section(markdown_result, '투자자 거래 동향 분석'),
            'financial_analysis': extract_section(markdown_result, '기업 현황 분석'),
            'industry_analysis': extract_section(markdown_result, '기업 개요 분석'),
            'news_analysis': extract_section(markdown_result, '최근 주요 뉴스'),
            'market_analysis': extract_section(markdown_result, '시장 분석'),
            'investment_strategy': extract_section(markdown_result, '투자 전략'),
        }

        return result

    except ImportError as e:
        raise ImportError(f"cores.analysis 모듈을 찾을 수 없습니다: {str(e)}")
    except Exception as e:
        raise Exception(f"분석 실패: {str(e)}")


def extract_section(markdown: str, section_title: str) -> str:
    """
    마크다운에서 특정 섹션 추출

    Args:
        markdown: 전체 마크다운 텍스트
        section_title: 섹션 제목

    Returns:
        추출된 섹션 내용
    """
    import re

    # 섹션 찾기 (# 또는 ## 로 시작)
    pattern = rf'#+\s*{re.escape(section_title)}.*?\n(.*?)(?=\n#+\s|\Z)'
    match = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return f"*{section_title} 내용을 찾을 수 없습니다.*"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 결과 표시
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def display_result(result: dict):
    """분석 결과 표시 (차트 포함)"""

    st.success("✅ 분석 완료!")

    # 종목 정보 표시
    st.subheader(f"📊 {result.get('company_name', '')} ({result.get('company_code', '')})")

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
        # 요약 섹션
        st.markdown("### 📌 핵심 투자 포인트")
        summary_content = result.get('summary', '분석 결과가 없습니다.')
        # HTML 차트 포함 렌더링
        st.markdown(summary_content, unsafe_allow_html=True)

    with tabs[1]:
        # 기술적 분석 (차트 포함)
        st.markdown("### 📈 기술적 분석")
        technical_content = result.get('technical_analysis', '분석 결과가 없습니다.')
        # HTML 차트가 포함된 마크다운 렌더링
        st.markdown(technical_content, unsafe_allow_html=True)

    with tabs[2]:
        # 거래 동향
        st.markdown("### 💼 투자자 거래 동향")
        trading_content = result.get('trading_flow', '분석 결과가 없습니다.')
        st.markdown(trading_content, unsafe_allow_html=True)

    with tabs[3]:
        # 재무 분석
        st.markdown("### 💰 재무 분석")
        financial_content = result.get('financial_analysis', '분석 결과가 없습니다.')
        st.markdown(financial_content, unsafe_allow_html=True)

    with tabs[4]:
        # 산업 분석
        st.markdown("### 🏢 산업 분석")
        industry_content = result.get('industry_analysis', '분석 결과가 없습니다.')
        st.markdown(industry_content, unsafe_allow_html=True)

    with tabs[5]:
        # 뉴스 분석
        st.markdown("### 📰 최근 뉴스")
        news_content = result.get('news_analysis', '분석 결과가 없습니다.')
        st.markdown(news_content, unsafe_allow_html=True)

    with tabs[6]:
        # 시장 분석
        st.markdown("### 📊 시장 분석")
        market_content = result.get('market_analysis', '분석 결과가 없습니다.')
        st.markdown(market_content, unsafe_allow_html=True)

    with tabs[7]:
        # 투자 전략
        st.markdown("### 🎯 투자 전략 및 AI 의견")
        strategy_content = result.get('investment_strategy', '분석 결과가 없습니다.')
        st.markdown(strategy_content, unsafe_allow_html=True)

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

            # 진행 상황 표시 영역
            progress_container = st.container()
            progress_bar = progress_container.progress(0)
            status_text = progress_container.empty()

            def update_progress(step_name: str, progress: int):
                """진행 상황 업데이트 콜백"""
                progress_bar.progress(progress)
                status_text.text(f"🤖 {step_name}... ({progress}%)")

            try:
                # ✅ 허용: 기존 함수 호출 (진행률 콜백 포함)
                result = asyncio.run(run_analysis(code, name, progress_callback=update_progress))

                # 진행 완료
                progress_bar.progress(100)
                status_text.text("✅ 분석 완료!")

                # 세션에 저장
                st.session_state.analysis_result = result

                # 진행 상황 표시 제거
                progress_container.empty()

                # 결과 표시
                display_result(result)

            except Exception as e:
                progress_container.empty()
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
