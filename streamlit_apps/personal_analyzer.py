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

# ✅ Trading Journal 모듈 import
from streamlit_apps.db_manager import TradingJournalDB
from streamlit_apps.technical_indicators import get_indicators_for_buy
from streamlit_apps.config_manager import ConfigManager
from datetime import datetime, date


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

    # Trading Journal DB 초기화
    if 'trading_db' not in st.session_state:
        try:
            st.session_state.trading_db = TradingJournalDB()
        except Exception as e:
            st.session_state.trading_db = None
            st.session_state.db_error = str(e)

    # Config Manager 초기화
    if 'config_manager' not in st.session_state:
        try:
            st.session_state.config_manager = ConfigManager()
        except Exception as e:
            st.session_state.config_manager = None

    # Buy Journal Prefill Data (F-TJ-007)
    if 'buy_journal_prefill' not in st.session_state:
        st.session_state.buy_journal_prefill = None


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

    # PDF 다운로드 및 매수 일지 적용 (F-TJ-007)
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        render_pdf_download(result)

    with col2:
        render_apply_to_buy_journal(result)


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
# 6. 매수 일지 적용 (F-TJ-007)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_apply_to_buy_journal(result: dict):
    """AI 분석 결과를 매수 일지에 바로 적용 (F-TJ-007)"""

    if st.button("📝 매수 일지에 적용", use_container_width=True, type="secondary"):
        # AI 의견 추출 (투자 전략 섹션)
        ai_opinion = result.get('investment_strategy', '')

        # Prefill 데이터 준비
        prefill_data = {
            'stock_code': result.get('company_code', ''),
            'stock_name': result.get('company_name', ''),
            'buy_date': datetime.now().strftime("%Y-%m-%d"),
            'buy_quantity': 1,
            'buy_price': 1000,
            'buy_reason': '',
            'potential': '',
            'ai_buy_opinion': ai_opinion,  # AI 의견 자동 입력
        }

        # 세션에 저장
        st.session_state.buy_journal_prefill = prefill_data

        st.success("✅ 매수 일지에 AI 분석 결과가 적용되었습니다!")
        st.info("📝 사이드바의 '매수일지' 탭으로 이동하세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. Q&A 섹션
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
# 8. 매수 일지 (Buy Journal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_buy_journal():
    """매수 일지 UI 렌더링 (F-TJ-001)"""

    st.subheader("📝 매수 일지")

    # DB 상태 체크
    if st.session_state.trading_db is None:
        st.error("데이터베이스를 사용할 수 없습니다.")
        if hasattr(st.session_state, 'db_error'):
            st.error(st.session_state.db_error)
        return

    # Prefill 데이터 확인 (F-TJ-007: AI 분석에서 바로 적용)
    prefill = st.session_state.buy_journal_prefill
    if prefill:
        st.info("🤖 AI 분석 결과가 적용되었습니다.")

    # 1. 종목 정보
    st.markdown("#### 📊 종목 정보")

    col1, col2 = st.columns(2)
    with col1:
        stock_code = st.text_input(
            "종목 코드",
            value=prefill.get('stock_code', '') if prefill else '',
            placeholder="예: 005930",
            help="6자리 종목 코드",
            key="buy_stock_code"
        )

    with col2:
        stock_name = st.text_input(
            "종목명",
            value=prefill.get('stock_name', '') if prefill else '',
            placeholder="예: 삼성전자",
            key="buy_stock_name"
        )

    # 2. 매수 정보
    st.markdown("#### 💰 매수 정보")

    col1, col2 = st.columns(2)
    with col1:
        buy_date = st.date_input(
            "매수일",
            value=datetime.strptime(prefill.get('buy_date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date() if prefill else date.today(),
            key="buy_date"
        )

    with col2:
        buy_quantity = st.number_input(
            "매수 수량",
            min_value=1,
            value=prefill.get('buy_quantity', 1) if prefill else 1,
            step=1,
            key="buy_quantity"
        )

    buy_price = st.number_input(
        "매수 단가 (원)",
        min_value=1,
        value=prefill.get('buy_price', 1000) if prefill else 1000,
        step=100,
        key="buy_price",
        help="주당 매수 가격"
    )

    # 매수 금액 자동 계산 표시
    buy_amount = buy_price * buy_quantity
    st.info(f"💵 매수 금액: {format_currency(buy_amount)}")

    # 3. 매수 이유 및 기대
    st.markdown("#### 📋 매수 판단")

    buy_reason = st.text_area(
        "매수 이유",
        value=prefill.get('buy_reason', '') if prefill else '',
        placeholder="매수 결정을 내린 근거를 작성하세요...",
        height=100,
        key="buy_reason"
    )

    potential = st.text_area(
        "기대 (낙관적 기대감)",
        value=prefill.get('potential', '') if prefill else '',
        placeholder="이 종목에 대한 낙관적 기대를 작성하세요...",
        height=80,
        key="buy_potential"
    )

    # 4. AI 분석 의견 (선택사항)
    st.markdown("#### 🤖 AI 분석 의견 (선택)")

    with st.expander("AI 의견 보기/입력", expanded=bool(prefill)):
        ai_buy_opinion = st.text_area(
            "AI 매수 의견",
            value=prefill.get('ai_buy_opinion', '') if prefill else '',
            placeholder="AI 분석 요청 시 자동으로 채워집니다...",
            height=150,
            key="ai_buy_opinion",
            help="'AI 분석 요청' 버튼을 클릭하면 자동으로 채워집니다."
        )

    # 5. 버튼
    st.divider()

    col1, col2 = st.columns(2)

    # AI 분석 요청 버튼 (선택사항)
    with col1:
        if st.button("🤖 AI 분석 요청", use_container_width=True, type="secondary"):
            if not stock_code or not stock_name:
                st.error("종목 코드와 종목명을 입력하세요.")
            else:
                # AI 분석 실행 후 의견 자동 입력
                st.info("AI 분석 기능은 메인 분석 탭에서 실행 후 '매수 일지 적용' 버튼을 클릭하세요.")

    # 저장 버튼
    with col2:
        if st.button("💾 매수 기록 저장", use_container_width=True, type="primary"):
            # 입력 검증
            if not stock_code or not stock_name:
                st.error("종목 코드와 종목명을 입력하세요.")
                return

            if not buy_reason:
                st.error("매수 이유를 입력하세요.")
                return

            # 매수 기록 데이터 준비
            buy_record = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'buy_date': buy_date.strftime("%Y-%m-%d"),
                'buy_quantity': buy_quantity,
                'buy_price': buy_price,
                'buy_reason': buy_reason,
                'potential': potential,
            }

            # AI 의견 추가 (입력된 경우에만)
            # PRD v1.2.0: AI 의견은 선택사항, 빈값이면 NULL
            if ai_buy_opinion and ai_buy_opinion.strip():
                buy_record['ai_buy_opinion'] = ai_buy_opinion
            else:
                buy_record['ai_buy_opinion'] = None

            # 기술적 지표 자동 계산
            with st.spinner("기술적 지표 계산 중..."):
                try:
                    indicators = get_indicators_for_buy(stock_code, buy_date.strftime("%Y%m%d"))
                    buy_record.update(indicators)
                except Exception as e:
                    st.warning(f"기술적 지표 계산 실패: {e}")
                    st.info("지표 없이 저장합니다.")

            # DB에 저장
            try:
                record_id = st.session_state.trading_db.add_buy_record(buy_record)

                if record_id:
                    st.success(f"✅ 매수 기록이 저장되었습니다! (ID: {record_id})")

                    # Prefill 데이터 초기화
                    st.session_state.buy_journal_prefill = None

                    # 입력 필드 초기화를 위해 rerun
                    st.rerun()
                else:
                    st.error("매수 기록 저장에 실패했습니다.")

            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

    # Prefill 데이터 초기화 버튼
    if prefill:
        if st.button("🔄 입력 초기화", use_container_width=True):
            st.session_state.buy_journal_prefill = None
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 매도 일지 (Sell Journal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_sell_journal():
    """매도 일지 UI 렌더링 (F-TJ-002)"""

    st.subheader("📤 매도 일지")

    # DB 상태 체크
    if st.session_state.trading_db is None:
        st.error("데이터베이스를 사용할 수 없습니다.")
        if hasattr(st.session_state, 'db_error'):
            st.error(st.session_state.db_error)
        return

    # 1. 매수 기록 선택
    st.markdown("#### 📋 매수 기록 선택")

    # 미체결 매수 기록 조회 (sell_date가 NULL인 것들)
    try:
        open_positions = st.session_state.trading_db.get_open_positions()

        if not open_positions:
            st.info("매도 가능한 매수 기록이 없습니다.")
            st.info("💡 먼저 '매수일지' 탭에서 매수 기록을 작성하세요.")
            return

        # 선택 옵션 생성
        position_options = {}
        for pos in open_positions:
            label = f"[{pos['id']}] {pos['stock_name']}({pos['stock_code']}) - {pos['buy_date']} - {pos['buy_quantity']}주 @ {format_currency(pos['buy_price'])}"
            position_options[label] = pos

        selected_label = st.selectbox(
            "매도할 매수 기록 선택",
            options=list(position_options.keys()),
            key="sell_position_select"
        )

        selected_position = position_options[selected_label]

        # 선택된 매수 기록 정보 표시
        st.info(f"""
        **선택된 매수 기록**
        - 종목: {selected_position['stock_name']} ({selected_position['stock_code']})
        - 매수일: {selected_position['buy_date']}
        - 매수 수량: {selected_position['buy_quantity']}주
        - 매수 단가: {format_currency(selected_position['buy_price'])}
        - 매수 금액: {format_currency(selected_position['buy_amount'])}
        """)

    except Exception as e:
        st.error(f"매수 기록 조회 실패: {e}")
        return

    # 2. 매도 정보
    st.markdown("#### 💰 매도 정보")

    col1, col2 = st.columns(2)
    with col1:
        sell_date = st.date_input(
            "매도일",
            value=date.today(),
            min_value=datetime.strptime(selected_position['buy_date'], "%Y-%m-%d").date(),
            key="sell_date"
        )

    with col2:
        sell_quantity = st.number_input(
            "매도 수량",
            min_value=1,
            max_value=selected_position['buy_quantity'],
            value=selected_position['buy_quantity'],
            step=1,
            key="sell_quantity",
            help=f"최대 {selected_position['buy_quantity']}주"
        )

    sell_price = st.number_input(
        "매도 단가 (원)",
        min_value=1,
        value=selected_position['buy_price'],
        step=100,
        key="sell_price",
        help="주당 매도 가격"
    )

    # 매도 금액 및 손익 자동 계산 표시
    sell_amount = sell_price * sell_quantity
    profit_amount = (sell_price - selected_position['buy_price']) * sell_quantity
    profit_rate = ((sell_price - selected_position['buy_price']) / selected_position['buy_price']) * 100
    holding_days = (sell_date - datetime.strptime(selected_position['buy_date'], "%Y-%m-%d").date()).days

    # 손익 표시 (색상 구분)
    if profit_amount > 0:
        st.success(f"""
        💵 매도 금액: {format_currency(sell_amount)}
        📈 손익: +{format_currency(profit_amount)} ({format_percentage(profit_rate)})
        📅 보유 기간: {holding_days}일
        """)
    elif profit_amount < 0:
        st.error(f"""
        💵 매도 금액: {format_currency(sell_amount)}
        📉 손익: {format_currency(profit_amount)} ({format_percentage(profit_rate)})
        📅 보유 기간: {holding_days}일
        """)
    else:
        st.info(f"""
        💵 매도 금액: {format_currency(sell_amount)}
        ➖ 손익: {format_currency(profit_amount)} ({format_percentage(profit_rate)})
        📅 보유 기간: {holding_days}일
        """)

    # 3. 매도 이유 및 교훈
    st.markdown("#### 📋 매도 판단")

    sell_reason = st.text_area(
        "매도 이유",
        placeholder="매도 결정을 내린 근거를 작성하세요...",
        height=100,
        key="sell_reason"
    )

    lesson_learned = st.text_area(
        "배운 점 (교훈)",
        placeholder="이번 매매에서 배운 점을 작성하세요...",
        height=80,
        key="lesson_learned"
    )

    # 4. AI 분석 의견 (선택사항)
    st.markdown("#### 🤖 AI 분석 의견 (선택)")

    with st.expander("AI 의견 보기/입력"):
        ai_sell_opinion = st.text_area(
            "AI 매도 의견",
            placeholder="AI 분석 요청 시 자동으로 채워집니다...",
            height=150,
            key="ai_sell_opinion",
            help="'AI 분석 요청' 버튼을 클릭하면 자동으로 채워집니다."
        )

    # 5. 버튼
    st.divider()

    col1, col2 = st.columns(2)

    # AI 분석 요청 버튼 (선택사항)
    with col1:
        if st.button("🤖 AI 분석 요청", use_container_width=True, type="secondary", key="sell_ai_btn"):
            st.info("AI 분석 기능은 메인 분석 탭에서 실행 후 '매도 일지 적용' 버튼을 클릭하세요.")

    # 저장 버튼
    with col2:
        if st.button("💾 매도 기록 저장", use_container_width=True, type="primary", key="sell_save_btn"):
            # 입력 검증
            if not sell_reason:
                st.error("매도 이유를 입력하세요.")
                return

            # 매도 기록 데이터 준비
            sell_record = {
                'sell_date': sell_date.strftime("%Y-%m-%d"),
                'sell_quantity': sell_quantity,
                'sell_price': sell_price,
                'sell_reason': sell_reason,
                'lesson_learned': lesson_learned,
            }

            # AI 의견 추가 (입력된 경우에만)
            # PRD v1.2.0: AI 의견은 선택사항, 빈값이면 NULL
            if ai_sell_opinion and ai_sell_opinion.strip():
                sell_record['ai_sell_opinion'] = ai_sell_opinion
            else:
                sell_record['ai_sell_opinion'] = None

            # 기술적 지표 자동 계산
            with st.spinner("기술적 지표 계산 중..."):
                try:
                    from streamlit_apps.technical_indicators import get_indicators_for_sell
                    indicators = get_indicators_for_sell(
                        selected_position['stock_code'],
                        sell_date.strftime("%Y%m%d")
                    )
                    sell_record.update(indicators)
                except Exception as e:
                    st.warning(f"기술적 지표 계산 실패: {e}")
                    st.info("지표 없이 저장합니다.")

            # DB에 매도 정보 업데이트
            try:
                success = st.session_state.trading_db.update_sell_record(
                    selected_position['id'],
                    sell_record
                )

                if success:
                    st.success(f"✅ 매도 기록이 저장되었습니다! (ID: {selected_position['id']})")
                    st.balloons()

                    # 페이지 새로고침
                    st.rerun()
                else:
                    st.error("매도 기록 저장에 실패했습니다.")

            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_sidebar():
    """사이드바 렌더링"""

    with st.sidebar:
        st.title("📊 PRISM-INSIGHT")

        # 탭으로 기능 분리
        tab1, tab2, tab3 = st.tabs(["🔍 분석", "📝 매수일지", "📤 매도일지"])

        with tab1:
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

        with tab2:
            # 매수 일지 (F-TJ-001)
            render_buy_journal()

        with tab3:
            # 매도 일지 (F-TJ-002)
            render_sell_journal()

        return stock_input, analyze_btn


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. 메인 함수
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
