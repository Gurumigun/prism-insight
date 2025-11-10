import streamlit as st
from datetime import datetime
import re
from pathlib import Path
import markdown
import base64
import sys
import os
import pandas as pd
import json
import plotly.graph_objects as go

# 현재 파일의 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if current_dir not in sys.path:
    sys.path.append(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from queue import Queue
from threading import Thread
import uuid

# TradingJournalDB import
try:
    from trading_journal_db import TradingJournalDB
except ImportError:
    TradingJournalDB = None

# pykrx import
try:
    from pykrx import stock
except ImportError:
    stock = None

# 보고서 저장 디렉토리 설정
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# 작업 큐 및 스레드 풀 설정
analysis_queue = Queue()

class AnalysisRequest:
    def __init__(self, stock_code: str, company_name: str, reference_date: str):
        self.id = str(uuid.uuid4())
        self.stock_code = stock_code
        self.company_name = company_name
        self.reference_date = reference_date
        self.status = "pending"
        self.result = None

class ModernStockAnalysisApp:
    def __init__(self):
        self.setup_page()
        self.initialize_session_state()
        self.start_background_worker()

    def setup_page(self):
        """페이지 설정 및 커스텀 CSS 적용"""
        st.set_page_config(
            page_title="analysis.stocksimulation.kr | AI 주식 분석 에이전트",
            page_icon="📊",
            layout="wide",
            # Open Graph 메타데이터 추가
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': """
                # analysis.stocksimulation.kr
                AI 주식 분석 에이전트
                """
            }
        )

        # Open Graph 태그 직접 주입
        og_html = """
        <head>
            <title>analysis.stocksimulation.kr | AI 주식 분석 에이전트</title>
            <meta property="og:title" content="analysis.stocksimulation.kr | AI 주식 분석 에이전트" />
            <meta property="og:description" content="AI 주식 분석 에이전트" />
            <meta property="og:image" content="https://media.istockphoto.com/id/2045262949/ko/%EC%82%AC%EC%A7%84/excited-businessman-raises-hands-and-punches-air-while-celebrating-successful-deal-stock.jpg?s=2048x2048&w=is&k=20&c=XtdmbV6gILRK1ahoMOf0_SFC256rgHyiaID_FeW4ojU=" />
            <meta property="og:url" content="https://analysis.stocksimulation.kr" />
            <meta property="og:type" content="website" />
            <meta property="og:site_name" content="analysis.stocksimulation.kr" />
        </head>
        """
        st.markdown(og_html, unsafe_allow_html=True)

        # 커스텀 CSS 적용
        self.apply_custom_styles()

    def apply_custom_styles(self):
        """모던한 디자인을 위한 커스텀 CSS 스타일 적용"""
        st.markdown("""
        <style>
            /* 전체 페이지 스타일 */
            .main {
                background-color: #fafafa;
                padding: 1.5rem;
            }
            
            /* 제목 및 헤더 스타일 */
            h1, h2, h3 {
                font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', sans-serif;
                color: #1E293B;
                font-weight: 700;
            }
            h1 {
                font-size: 2.5rem;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #E2E8F0;
            }
            h2 {
                font-size: 1.8rem;
                margin-top: 2rem;
                margin-bottom: 1rem;
            }
            h3 {
                font-size: 1.3rem;
                margin-top: 1.5rem;
                color: #334155;
            }
            
            /* 카드 컨테이너 스타일 */
            .card {
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border: 1px solid #F1F5F9;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
            }
            
            /* 폼 요소 스타일 */
            .stTextInput > div > div > input {
                border-radius: 8px;
                height: 2.8rem;
                border: 1px solid #E2E8F0;
            }
            .stTextInput > div > div > input:focus {
                border-color: #0EA5E9;
                box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.2);
            }
            .stDateInput > div > div > input {
                border-radius: 8px;
            }
            
            /* 버튼 스타일 */
            .stButton > button {
                background-color: #0EA5E9;
                color: white;
                border-radius: 8px;
                height: 3rem;
                font-weight: 600;
                border: none;
                transition: all 0.2s ease;
            }
            .stButton > button:hover {
                background-color: #0284C7;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
            }
            .stButton > button:active {
                transform: translateY(0);
            }
            
            /* 선택 요소 스타일 */
            .stSelectbox > div > div {
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
            
            /* 사이드바 스타일 */
            .css-1d391kg, .css-1om1kqc, .css-1n76uvr {
                background-color: #F8FAFC;
                padding: 2rem 1rem;
            }
            
            /* 상태 메시지 스타일 */
            .stAlert {
                border-radius: 8px;
                padding: 1rem;
            }
            .success {
                background-color: #ECFDF5;
                color: #065F46;
                border: 1px solid #D1FAE5;
            }
            .error {
                background-color: #FEF2F2;
                color: #991B1B;
                border: 1px solid #FEE2E2;
            }
            .warning {
                background-color: #FFFBEB;
                color: #92400E;
                border: 1px solid #FEF3C7;
            }
            .info {
                background-color: #EFF6FF;
                color: #1E40AF;
                border: 1px solid #DBEAFE;
            }
            
            /* 테이블 스타일 */
            .dataframe {
                font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
                width: 100%;
                border-collapse: collapse;
            }
            .dataframe th {
                background-color: #F1F5F9;
                padding: 0.75rem 1rem;
                text-align: left;
                font-weight: 600;
                color: #334155;
                border-top: 1px solid #E2E8F0;
                border-bottom: 1px solid #CBD5E1;
            }
            .dataframe td {
                padding: 0.75rem 1rem;
                border-bottom: 1px solid #E2E8F0;
            }
            .dataframe tr:nth-child(even) {
                background-color: #F8FAFC;
            }
            
            /* 다운로드 링크 스타일 */
            a {
                color: #0EA5E9;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            a:hover {
                color: #0284C7;
                text-decoration: underline;
            }
            a[download] {
                display: inline-block;
                background-color: #F1F5F9;
                color: #334155;
                font-weight: 600;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                margin-right: 0.5rem;
                border: 1px solid #E2E8F0;
                text-decoration: none;
            }
            a[download]:hover {
                background-color: #E2E8F0;
                text-decoration: none;
            }
            
            /* 프로그레스 표시 스타일 */
            .stProgress > div > div {
                background-color: #0EA5E9;
            }
            
            /* 마크다운 본문 스타일 */
            .markdown-body {
                font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
                color: #334155;
                line-height: 1.7;
            }
            .markdown-body pre {
                background-color: #F1F5F9;
                border-radius: 8px;
                padding: 1rem;
            }
            .markdown-body table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
            }
            .markdown-body table th,
            .markdown-body table td {
                padding: 0.5rem 1rem;
                border: 1px solid #E2E8F0;
            }
            .markdown-body table th {
                background-color: #F1F5F9;
            }
            
            /* 이미지 스타일 */
            img {
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
            }
            
            /* 헤더 스타일 */
            .header {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 1.5rem 0;
                margin-bottom: 2rem;
                text-align: center;
            }
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 0.5rem;
            }
            .logo {
                font-size: 2.5rem;
                margin-right: 0.75rem;
            }
            .app-title {
                font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
                font-size: 2.5rem;
                font-weight: 800;
                color: #0EA5E9;
                letter-spacing: -0.03em;
            }
            .app-description {
                font-size: 1.1rem;
                color: #64748B;
                margin-top: 0.3rem;
                font-weight: 400;
            }
            
            /* 사이드바 헤더 */
            .sidebar-header {
                display: flex;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            .sidebar-logo {
                font-size: 1.8rem;
                margin-right: 0.5rem;
            }
            .sidebar-title {
                font-size: 1.3rem;
                font-weight: 700;
                color: #0EA5E9;
            }
            
            /* 상태 카드 */
            @keyframes progress-animation {
                0% { width: 0%; }
                20% { width: 20%; }
                40% { width: 40%; }
                60% { width: 60%; }
                80% { width: 80%; }
                100% { width: 40%; }
            }
            
            .status-card {
                display: flex;
                align-items: flex-start;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            .status-icon {
                font-size: 1.5rem;
                margin-right: 1rem;
                margin-top: 0.25rem;
            }
            .status-details {
                flex: 1;
            }
            .status-title {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.3rem;
            }
            .status-info {
                color: #4B5563;
                margin-bottom: 0.5rem;
            }
            .status-card.pending {
                background-color: #FFFBEB;
                border: 1px solid #FEF3C7;
            }
            .status-card.completed {
                background-color: #ECFDF5;
                border: 1px solid #D1FAE5;
            }
            .status-card.failed {
                background-color: #FEF2F2;
                border: 1px solid #FEE2E2;
            }
            .status-progress-container {
                height: 6px;
                background-color: rgba(251, 191, 36, 0.3);
                border-radius: 3px;
                overflow: hidden;
                margin-top: 0.5rem;
            }
            .status-progress-bar {
                height: 100%;
                background-color: #F59E0B;
                width: 40%;
                border-radius: 3px;
                animation: progress-animation 2s infinite alternate;
            }
            
            /* 기능 리스트 스타일 */
            .feature-list {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            .feature-list li {
                display: flex;
                align-items: center;
                margin-bottom: 0.8rem;
            }
            .feature-icon {
                font-size: 1.2rem;
                margin-right: 0.7rem;
                width: 24px;
                text-align: center;
            }
            .feature-title {
                font-weight: 600;
                margin-right: 0.5rem;
            }
            
            /* 시간 표시 스타일 */
            .estimate-time {
                display: flex;
                align-items: center;
                margin-bottom: 0.5rem;
            }
            .time-icon {
                font-size: 1.5rem;
                margin-right: 1rem;
            }
            .time-details {
                flex: 1;
            }
            .time-title {
                font-size: 0.9rem;
                color: #64748B;
            }
            .time-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #0EA5E9;
            }
            .delivery-note {
                color: #64748B;
                font-size: 0.9rem;
                margin-top: 0.3rem;
            }
            
            /* 폼 카드 */
            .form-card, .report-card, .filter-card {
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border: 1px solid #F1F5F9;
            }
            
            /* 마크다운 미리보기 */
            .markdown-preview {
                padding: 1rem;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #F8FAFC;
                max-height: 600px;
                overflow-y: auto;
            }
        </style>
        """, unsafe_allow_html=True)

    def add_app_header(self):
        """앱 헤더와 브랜딩 추가"""
        st.markdown("""
        <div class="header">
            <div class="logo-container">
                <div class="logo">📊</div>
                <div class="app-title">analysis.stocksimulation.kr</div>
            </div>
            <div class="app-description">
                AI 주식 분석 에이전트
            </div>
        </div>
        """, unsafe_allow_html=True)

    def create_card(self, title, content, icon=None):
        """카드 컴포넌트 생성"""
        icon_html = f'<div class="card-icon">{icon}</div>' if icon else ''
        
        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                {icon_html}
                <div class="card-title">{title}</div>
            </div>
            <div class="card-content">
                {content}
            </div>
        </div>
        <style>
            .card-header {{
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
            }}
            .card-icon {{
                font-size: 1.5rem;
                margin-right: 0.8rem;
                color: #0EA5E9;
            }}
            .card-title {{
                font-size: 1.2rem;
                font-weight: 600;
                color: #1E293B;
            }}
            .card-content {{
                color: #334155;
                line-height: 1.6;
            }}
        </style>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'requests' not in st.session_state:
            st.session_state.requests = {}
        if 'processing' not in st.session_state:
            st.session_state.processing = False

    def start_background_worker(self):
        """백그라운드 작업자 시작"""
        def worker():
            while True:
                request = analysis_queue.get()
                try:
                    self.process_analysis_request(request)
                except Exception as e:
                    print(f"Error processing request {request.id}: {str(e)}")
                finally:
                    analysis_queue.task_done()

        for _ in range(5):  # 5개의 워커 스레드 시작
            Thread(target=worker, daemon=True).start()

    def process_analysis_request(self, request: AnalysisRequest):
        """분석 요청 처리"""
        try:
            # 캐시된 보고서 확인
            is_cached, cached_content, cached_file = self.get_cached_report(
                request.stock_code, request.reference_date
            )

            if is_cached:
                # 캐시된 보고서 사용
                request.result = f"캐시된 분석 보고서를 찾았습니다. (파일: {cached_file.name})"
            else:
                # 별도 프로세스로 분석 실행
                import subprocess
                import tempfile
                import json

                # 프로젝트 루트 디렉토리와 streamlit 디렉토리 경로
                project_root = str(Path(__file__).parent.parent.parent.absolute())
                streamlit_dir = str(Path(__file__).parent.absolute())

                # 요청 정보를 임시 파일에 저장
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    request_info = {
                        'stock_code': request.stock_code,
                        'company_name': request.company_name,
                        'reference_date': request.reference_date,
                        'output_file': f"reports/{request.stock_code}_{request.company_name}_{request.reference_date}_gpt4.1.md"
                    }
                    json.dump(request_info, f)
                    request_file = f.name

                # 별도 프로세스 실행
                subprocess.Popen([
                    "python", "-c",
                    f'''
import asyncio, json, os, sys

# Python path 설정
project_root = "{project_root}"
streamlit_dir = "{streamlit_dir}"
sys.path.insert(0, project_root)
sys.path.insert(0, streamlit_dir)

# 작업 디렉토리 변경
os.chdir(project_root)

print(f"Working directory: {{os.getcwd()}}")
print(f"Python path: {{sys.path[:3]}}")

try:
    from cores.main import analyze_stock
    print("Successfully imported analyze_stock")
except ImportError as e:
    print(f"Failed to import analyze_stock: {{e}}")
    exit(1)

# 요청 정보 로드
with open("{request_file}", "r") as f:
    info = json.load(f)

# 분석 실행
async def run():
    try:
        print(f"Starting analysis for {{info['company_name']}} ({{info['stock_code']}})")
        report = await analyze_stock(
            company_code=info["stock_code"],
            company_name=info["company_name"],
            reference_date=info["reference_date"]
        )

        # 결과 저장
        with open(info["output_file"], "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {{info['output_file']}}")

        # 임시 파일 삭제
        os.remove("{request_file}")
        print("Analysis completed successfully")

    except Exception as e:
        print(f"Error during analysis: {{e}}")
        import traceback
        traceback.print_exc()

asyncio.run(run())
'''
                ], cwd=project_root)

                request.result = f"분석이 시작되었습니다. 완료 후 '보고서 보기' 메뉴에서 확인하실 수 있습니다."

            request.status = "completed"

        except Exception as e:
            request.status = "failed"
            request.result = f"분석 중 오류가 발생했습니다: {str(e)}"

    @staticmethod
    def get_cached_report(stock_code: str, reference_date: str) -> tuple[bool, str, Path | None]:
        """캐시된 보고서 검색"""
        report_pattern = f"{stock_code}_*_{reference_date}*.md"
        matching_files = list(REPORTS_DIR.glob(report_pattern))

        if matching_files:
            latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
            with open(latest_file, "r", encoding="utf-8") as f:
                return True, f.read(), latest_file
        return False, "", None

    @staticmethod
    def save_report(stock_code: str, company_name: str, reference_date: str, content: str) -> Path:
        """보고서를 파일로 저장"""
        filename = f"{stock_code}_{company_name}_{reference_date}_gpt4o.md"
        filepath = REPORTS_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def submit_analysis(self, stock_code: str, company_name: str, reference_date: str) -> str:
        """분석 요청 제출"""
        request = AnalysisRequest(stock_code, company_name, reference_date)
        st.session_state.requests[request.id] = request
        analysis_queue.put(request)
        return request.id

    def render_modern_analysis_form(self):
        """모던한 디자인의 분석 요청 폼"""
        # 커스텀 헤더 추가
        self.add_app_header()

        # 앱 설명 카드 (텍스트만 사용)
        st.markdown("### 🤖 AI 주식 분석 에이전트 서비스")
        st.markdown("이 서비스는 AI를 활용하여 종목을 심층 분석하고 전문가 수준의 투자 분석 보고서를 자동으로 생성합니다. 회사 정보와 이메일을 입력하시면 분석이 완료된 후 결과가 이메일로 전송됩니다.")

        # 두 개의 열로 나누어 레이아웃 구성
        col1, col2 = st.columns([2, 1])

        with col1:
            # 분석 요청 카드
            st.markdown("## 분석 요청")

            with st.form("analysis_form"):
                form_col1, form_col2 = st.columns(2)

                with form_col1:
                    company_name = st.text_input("회사명", placeholder="예: 삼성전자")

                with form_col2:
                    stock_code = st.text_input("종목코드", placeholder="예: 005930 (6자리)")
                    today = datetime.now().date()
                    analysis_date = st.date_input(
                        "분석 기준일",
                        value=today,
                        max_value=today
                    )

                # FAQ 토글
                with st.expander("📌 자주 묻는 질문"):
                    st.markdown("""
                    **Q: 분석은 얼마나 걸리나요?**  
                    A: 일반적으로 5-10분 정도 소요됩니다.
                    
                    **Q: 어떤 정보가 포함되나요?**
                    A: 주가 분석, 재무제표 분석, 경쟁사 비교, 투자 지표, 뉴스 분석 등이 포함됩니다.

                    **Q: 결과는 어떻게 받나요?**
                    A: 분석 완료 후 '보고서 보기' 메뉴에서 확인 가능합니다.
                    """)

                # 디자인된 제출 버튼
                submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
                with submit_col2:
                    submitted = st.form_submit_button("분석 시작", use_container_width=True)

            # 폼 제출 처리
            if submitted:
                if not self.validate_inputs(company_name, stock_code):
                    return

                reference_date = analysis_date.strftime("%Y%m%d")
                request_id = self.submit_analysis(stock_code, company_name, reference_date)
                st.success("분석이 요청되었습니다. 완료되면 '보고서 보기' 메뉴에서 확인하실 수 있습니다.")

        with col2:
            # 분석 정보 카드 (네이티브 컴포넌트 사용)
            st.markdown("### ✨ 분석 내용")
            features = [
                {"icon": "📊", "title": "기술적 분석", "desc": "주가 패턴 및 모멘텀 분석"},
                {"icon": "💰", "title": "재무 분석", "desc": "종합적인 재무제표 분석"},
                {"icon": "🏢", "title": "경쟁사 비교", "desc": "동종업계 내 상대적 위치 평가"},
                {"icon": "📈", "title": "투자 지표", "desc": "PER, PBR, ROE 등 핵심 투자지표"},
                {"icon": "📰", "title": "뉴스 분석", "desc": "최신 뉴스 및 시장 반응 분석"}
            ]

            for feature in features:
                st.markdown(f"{feature['icon']} **{feature['title']}** - {feature['desc']}")

            # 분석 완료 예상 시간 (네이티브 컴포넌트 사용)
            st.markdown("### 분석 예상 시간")
            st.markdown("⏱️ **5-10분**")
            st.markdown("분석 완료 후 이메일로 전송됩니다")

        # 분석 상태 섹션
        if st.session_state.requests:
            self.render_request_status()

    def render_request_status(self):
        """요청 상태를 표시하는 메서드"""
        st.markdown("## 📋 진행 중인 분석")

        # 요청 목록을 상태별로 분류
        pending_requests = []
        completed_requests = []
        failed_requests = []

        for request_id, request in st.session_state.requests.items():
            if request.status == "pending":
                pending_requests.append(request)
            elif request.status == "completed":
                completed_requests.append(request)
            elif request.status == "failed":
                failed_requests.append(request)

        # 진행 중인 요청 표시
        if pending_requests:
            for request in pending_requests:
                st.info(f"⏳ {request.company_name} ({request.stock_code}) - 분석 진행 중... (약 5-10분 소요)")

        # 완료된 요청 표시
        if completed_requests:
            for request in completed_requests:
                st.success(f"✅ {request.company_name} ({request.stock_code}) - {request.result}")

        # 실패한 요청 표시
        if failed_requests:
            for request in failed_requests:
                st.error(f"❌ {request.company_name} ({request.stock_code}) - {request.result}")

    def render_modern_report_viewer(self):
        """모던한 디자인의 보고서 뷰어"""
        # 커스텀 헤더 추가
        self.add_app_header()
        
        # 보고서 뷰어 소개
        intro_content = """
        <p>과거에 생성된 분석 보고서를 검색하고 열람할 수 있습니다. 
        종목코드로 검색하거나 목록에서 선택하여 보고서를 확인하세요.</p>
        """
        self.create_card("보고서 뷰어", intro_content, "📑")
        
        # 검색 및 필터 영역
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            st.subheader("보고서 검색")
            search_code = st.text_input("종목코드로 검색", placeholder="예: 005930")
            
            # 저장된 보고서 목록 가져오기
            reports = list(REPORTS_DIR.glob("*.md"))
            
            if search_code:
                reports = [r for r in reports if search_code in r.stem]
            
            if not reports:
                st.warning("저장된 보고서가 없습니다.")
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            # 보고서 분류
            st.markdown("### 보고서 분류")
            report_dates = {}
            
            for report in reports:
                # 파일 수정 날짜 기준으로 분류
                mod_date = datetime.fromtimestamp(report.stat().st_mtime).strftime('%Y-%m-%d')
                if mod_date not in report_dates:
                    report_dates[mod_date] = []
                report_dates[mod_date].append(report)
            
            # 날짜별 보고서 개수 표시
            for date, date_reports in sorted(report_dates.items(), reverse=True):
                st.markdown(f"**{date}** ({len(date_reports)}개)")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # 보고서 선택 및 표시 영역
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.subheader("보고서 목록")
            
            # 보고서 정렬 (최신순)
            reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 보고서 선택을 위한 현대적인 UI
            report_options = [f"{r.stem} ({datetime.fromtimestamp(r.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})" for r in reports]
            report_dict = dict(zip(report_options, reports))
            
            selected_report_name = st.selectbox(
                "보고서 선택",
                options=report_options
            )
            
            if selected_report_name:
                selected_report = report_dict[selected_report_name]
                
                # 보고서 메타데이터 표시
                report_meta_col1, report_meta_col2 = st.columns(2)
                with report_meta_col1:
                    st.markdown(f"**생성일시:** {datetime.fromtimestamp(selected_report.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                with report_meta_col2:
                    st.markdown(f"**파일 크기:** {selected_report.stat().st_size / 1024:.1f} KB")
                
                # 다운로드 버튼 영역
                st.markdown("### 다운로드 옵션")
                download_col1, download_col2 = st.columns(2)
                with download_col1:
                    st.markdown(self.get_download_link(selected_report, 'md'), unsafe_allow_html=True)
                with download_col2:
                    st.markdown(self.get_download_link(selected_report, 'html'), unsafe_allow_html=True)
                
                # 보고서 미리보기
                st.markdown("### 보고서 미리보기")
                
                with open(selected_report, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 스타일이 적용된 마크다운으로 보여주기
                st.markdown('<div class="markdown-preview">', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    def validate_inputs(self, company_name: str, stock_code: str) -> bool:
        """입력값 유효성 검사"""
        if not company_name:
            st.error("회사명을 입력해주세요.")
            return False

        if not self.is_valid_stock_code(stock_code):
            st.error("올바른 종목코드를 입력해주세요 (6자리 숫자).")
            return False

        return True

    @staticmethod
    def is_valid_stock_code(code: str) -> bool:
        return bool(re.match(r'^\d{6}$', code))

    @staticmethod
    def get_download_link(file_path: Path, file_format: str) -> str:
        """다운로드 링크 생성"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()

        if file_format == 'html':
            # 마크다운을 HTML로 변환
            html_content = markdown.markdown(
                data,
                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
            )
            b64 = base64.b64encode(html_content.encode()).decode()
            extension = 'html'
        else:
            b64 = base64.b64encode(data.encode()).decode()
            extension = 'md'

        filename = f"{file_path.stem}.{extension}"
        return f'<a href="data:file/{extension};base64,{b64}" download="{filename}">💾 {extension.upper()} 형식으로 다운로드</a>'

    def calculate_rsi(self, df, period=14):
        """RSI 계산"""
        try:
            close = df['종가']
            delta = close.diff()

            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return round(rsi.iloc[-1], 2) if not rsi.empty else None
        except:
            return None

    def calculate_macd(self, df):
        """MACD 계산"""
        try:
            close = df['종가']
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2

            return round(macd.iloc[-1], 2) if not macd.empty else None
        except:
            return None

    def calculate_adr(self, df, period=20):
        """ADR (Average Daily Range) 계산"""
        try:
            high_low = df['고가'] - df['저가']
            adr = high_low.rolling(window=period).mean()

            return round(adr.iloc[-1], 2) if not adr.empty else None
        except:
            return None

    def calculate_market_adr(self, date_str, period=20):
        """코스피/코스닥 시장 ADR 계산"""
        try:
            from datetime import datetime, timedelta

            # 날짜 파싱
            target_date = datetime.strptime(date_str, "%Y%m%d")
            start_date = (target_date - timedelta(days=period + 30)).strftime("%Y%m%d")  # 여유있게
            end_date = date_str

            # 코스피 지수 데이터
            kospi_df = stock.get_index_ohlcv(start_date, end_date, "1001")  # 코스피
            kosdaq_df = stock.get_index_ohlcv(start_date, end_date, "2001")  # 코스닥

            kospi_adr = None
            kosdaq_adr = None

            if not kospi_df.empty and len(kospi_df) >= period:
                high_low = kospi_df['고가'] - kospi_df['저가']
                adr_series = high_low.rolling(window=period).mean()
                kospi_adr = round(adr_series.iloc[-1], 2) if not adr_series.empty else None

            if not kosdaq_df.empty and len(kosdaq_df) >= period:
                high_low = kosdaq_df['고가'] - kosdaq_df['저가']
                adr_series = high_low.rolling(window=period).mean()
                kosdaq_adr = round(adr_series.iloc[-1], 2) if not adr_series.empty else None

            return kospi_adr, kosdaq_adr

        except Exception as e:
            print(f"시장 ADR 계산 실패: {str(e)}")
            return None, None

    def get_stock_info(self, ticker, target_date=None):
        """종목 정보 조회 및 기술적 지표 계산

        Args:
            ticker: 종목코드
            target_date: 기준일 (datetime 객체 또는 None). None이면 오늘 날짜 사용
        """
        if stock is None:
            return None, None, None, None, None, None

        try:
            from datetime import timedelta

            # 종목명 조회
            stock_name = stock.get_market_ticker_name(ticker)
            if not stock_name:
                return None, None, None, None, None, None

            # 기준일 설정
            if target_date is None:
                target_date = datetime.now()
            elif isinstance(target_date, str):
                target_date = datetime.strptime(target_date, "%Y%m%d")

            # 현재가 조회 (기준일 기준)
            end_date = target_date.strftime("%Y%m%d")
            start_date = (target_date - timedelta(days=7)).strftime("%Y%m%d")

            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
            if df.empty:
                return stock_name, None, None, None, None, None

            current_price = df.iloc[-1]['종가']

            # 차트 데이터 (기준일로부터 과거 150일 - 기술적 지표 계산을 위해 더 많은 데이터 필요)
            chart_start = (target_date - timedelta(days=150)).strftime("%Y%m%d")
            chart_df = stock.get_market_ohlcv_by_date(chart_start, end_date, ticker)

            # 기술적 지표 계산
            rsi = self.calculate_rsi(chart_df)
            macd = self.calculate_macd(chart_df)
            adr = self.calculate_adr(chart_df)

            return stock_name, current_price, chart_df, rsi, macd, adr

        except Exception as e:
            st.error(f"종목 정보 조회 실패: {str(e)}")
            return None, None, None, None, None, None

    def create_stock_chart(self, df, stock_name):
        """주가 차트 생성"""
        if df is None or df.empty:
            return None

        fig = go.Figure()

        # 캔들스틱 차트
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['시가'],
            high=df['고가'],
            low=df['저가'],
            close=df['종가'],
            name=stock_name
        ))

        # 거래량 추가
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['거래량'],
            name='거래량',
            yaxis='y2',
            opacity=0.3
        ))

        fig.update_layout(
            title=f"{stock_name} 주가 차트",
            yaxis_title="주가 (원)",
            yaxis2=dict(
                title="거래량",
                overlaying='y',
                side='right'
            ),
            xaxis_rangeslider_visible=False,
            height=400
        )

        return fig

    def save_buy_record(self, ticker, company_name, buy_price, quantity, rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, reason):
        """매수 기록 저장"""
        try:
            # 데이터베이스 경로를 project_root로 명시
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")

            # TradingJournalDB를 사용하여 저장
            with TradingJournalDB(db_path) as db:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                scenario = {
                    "rationale": reason if reason else "미입력",
                    "investment_period": "중기",
                    "sector": "기타"
                }

                success = db.add_position(
                    ticker=ticker,
                    company_name=company_name,
                    buy_price=buy_price,
                    buy_date=now,
                    quantity=quantity,
                    rsi=rsi,
                    macd=macd,
                    adr=adr,
                    market_kospi_adr=market_kospi_adr,
                    market_kosdaq_adr=market_kosdaq_adr,
                    scenario=json.dumps(scenario, ensure_ascii=False)
                )

                return success

        except Exception as e:
            st.error(f"저장 실패: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return False

    def render_buy_records(self):
        """매수 기록 화면"""
        self.add_app_header()

        st.markdown("## 📊 매수 기록 관리")

        if stock is None:
            st.warning("pykrx 라이브러리가 설치되지 않았습니다. `pip install pykrx`를 실행해주세요.")

        if TradingJournalDB is None:
            st.error("TradingJournalDB 모듈을 불러올 수 없습니다.")
            return

        # 탭 생성
        tab1, tab2 = st.tabs(["📝 매수 기록 등록", "💼 보유 종목 조회"])

        # 탭 1: 매수 기록 등록
        with tab1:
            st.markdown("### 📝 새 매수 기록 등록")
            st.markdown("종목코드를 입력하면 자동으로 종목 정보를 가져옵니다.")

            # 종목코드 입력
            col1, col2 = st.columns([2, 1])
            with col1:
                ticker_input = st.text_input("종목코드 (6자리)", placeholder="예: 005930", key="ticker_input")
            with col2:
                search_button = st.button("🔍 종목 조회", type="primary", use_container_width=True)

            # 종목 정보 조회 및 표시
            if search_button and ticker_input:
                if not re.match(r'^\d{6}$', ticker_input):
                    st.error("올바른 종목코드를 입력해주세요 (6자리 숫자)")
                else:
                    with st.spinner("종목 정보 및 기술적 지표를 계산하고 있습니다..."):
                        stock_name, current_price, chart_df, rsi, macd, adr = self.get_stock_info(ticker_input)

                        if stock_name is None:
                            st.error("종목을 찾을 수 없습니다. 종목코드를 확인해주세요.")
                        else:
                            # 시장 ADR 계산 (당일 기준)
                            today_str = datetime.now().strftime("%Y%m%d")
                            kospi_adr, kosdaq_adr = self.calculate_market_adr(today_str)

                            # 세션 상태에 저장
                            st.session_state.searched_ticker = ticker_input
                            st.session_state.searched_name = stock_name
                            st.session_state.searched_price = current_price
                            st.session_state.searched_chart = chart_df
                            st.session_state.searched_rsi = rsi
                            st.session_state.searched_macd = macd
                            st.session_state.searched_adr = adr
                            st.session_state.searched_kospi_adr = kospi_adr
                            st.session_state.searched_kosdaq_adr = kosdaq_adr

            # 종목 정보가 있으면 표시
            if hasattr(st.session_state, 'searched_ticker'):
                ticker = st.session_state.searched_ticker
                stock_name = st.session_state.searched_name
                current_price = st.session_state.searched_price
                chart_df = st.session_state.searched_chart
                rsi_value = st.session_state.get('searched_rsi', 0)
                macd_value = st.session_state.get('searched_macd', 0)
                adr_value = st.session_state.get('searched_adr', 0)
                kospi_adr_value = st.session_state.get('searched_kospi_adr', 0)
                kosdaq_adr_value = st.session_state.get('searched_kosdaq_adr', 0)

                st.success(f"✅ 종목 조회 완료: {stock_name} ({ticker})")

                # 종목 정보 카드
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("종목명", stock_name)
                with col2:
                    st.metric("종목코드", ticker)
                with col3:
                    if current_price:
                        st.metric("현재가", f"{current_price:,.0f}원")
                    else:
                        st.metric("현재가", "조회 실패")

                st.markdown("---")

                # 매수 정보 입력 폼 (차트 위로 이동)
                st.markdown("### 💰 매수 정보 입력")

                # 기술적 지표 현재 값 표시 (읽기 전용)
                st.markdown("#### 📊 자동 계산된 기술적 지표")
                ind_col1, ind_col2, ind_col3, ind_col4, ind_col5 = st.columns(5)
                with ind_col1:
                    st.metric("RSI", f"{rsi_value:.2f}" if rsi_value else "N/A", help="상대강도지수 (0~100)")
                with ind_col2:
                    st.metric("MACD", f"{macd_value:.2f}" if macd_value else "N/A", help="이동평균수렴확산지수")
                with ind_col3:
                    st.metric("종목 ADR", f"{adr_value:.2f}" if adr_value else "N/A", help="평균 일일 변동폭")
                with ind_col4:
                    st.metric("코스피 ADR", f"{kospi_adr_value:.2f}" if kospi_adr_value else "N/A", help="코스피 시장 ADR")
                with ind_col5:
                    st.metric("코스닥 ADR", f"{kosdaq_adr_value:.2f}" if kosdaq_adr_value else "N/A", help="코스닥 시장 ADR")

                st.markdown("---")

                # 날짜 선택 및 재계산 영역 (form 외부)
                st.markdown("#### 📅 매수일 선택")
                date_col1, date_col2 = st.columns([2, 1])
                with date_col1:
                    selected_date = st.date_input(
                        "매수일을 선택하세요",
                        value=datetime.now(),
                        max_value=datetime.now(),
                        help="매수한 날짜를 선택하면 해당 날짜의 기술적 지표를 계산할 수 있습니다",
                        key="date_selector"
                    )
                with date_col2:
                    st.markdown("")  # 여백
                    recalc_button = st.button(
                        "📊 이 날짜로 지표 재계산",
                        use_container_width=True,
                        type="secondary"
                    )

                # 재계산 버튼이 눌렸을 때
                if recalc_button:
                    with st.spinner(f"📅 {selected_date.strftime('%Y-%m-%d')} 기준 기술적 지표를 계산하고 있습니다..."):
                        # 해당 날짜 기준으로 기술적 지표 재계산
                        _, price_at_date, chart_df_date, rsi_date, macd_date, adr_date = self.get_stock_info(
                            ticker,
                            selected_date
                        )

                        if price_at_date:
                            # 시장 ADR도 해당 날짜 기준으로 재계산
                            date_str = selected_date.strftime("%Y%m%d")
                            kospi_adr_date, kosdaq_adr_date = self.calculate_market_adr(date_str)

                            # 세션 상태 업데이트
                            st.session_state.searched_price = price_at_date
                            st.session_state.searched_chart = chart_df_date
                            st.session_state.searched_rsi = rsi_date
                            st.session_state.searched_macd = macd_date
                            st.session_state.searched_adr = adr_date
                            st.session_state.searched_kospi_adr = kospi_adr_date
                            st.session_state.searched_kosdaq_adr = kosdaq_adr_date

                            st.success(f"✅ {selected_date.strftime('%Y-%m-%d')} 기준 지표가 업데이트되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 해당 날짜의 데이터를 가져올 수 없습니다. 영업일을 선택해주세요.")

                # 현재 세션 상태의 값 다시 읽기
                current_price = st.session_state.searched_price
                rsi_value = st.session_state.get('searched_rsi', 0)
                macd_value = st.session_state.get('searched_macd', 0)
                adr_value = st.session_state.get('searched_adr', 0)
                kospi_adr_value = st.session_state.get('searched_kospi_adr', 0)
                kosdaq_adr_value = st.session_state.get('searched_kosdaq_adr', 0)

                st.markdown("---")

                with st.form("buy_record_form"):
                    st.markdown("#### 💵 거래 정보")
                    # 첫 번째 행: 매수가, 수량
                    col1, col2 = st.columns(2)
                    with col1:
                        buy_price = st.number_input(
                            "💰 매수가 (원) *",
                            min_value=1,
                            value=int(current_price) if current_price else 0,
                            step=100,
                            help="실제 매수한 가격을 입력해주세요"
                        )
                    with col2:
                        quantity = st.number_input(
                            "📦 매수 수량 *",
                            min_value=1,
                            value=1,
                            step=1,
                            help="매수한 주식 수량"
                        )

                    # 매수일은 form 위에서 선택한 날짜 사용
                    buy_date = selected_date

                    st.markdown("#### 📈 기술적 지표 (수정 가능)")
                    # 두 번째 행: 기술적 지표
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        rsi = st.number_input(
                            "RSI",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(rsi_value) if rsi_value else 50.0,
                            step=0.1,
                            help="상대강도지수 (0~100)"
                        )
                    with col2:
                        macd = st.number_input(
                            "MACD",
                            value=float(macd_value) if macd_value else 0.0,
                            step=0.1,
                            help="이동평균수렴확산지수"
                        )
                    with col3:
                        adr = st.number_input(
                            "종목 ADR",
                            min_value=0.0,
                            value=float(adr_value) if adr_value else 0.0,
                            step=0.1,
                            help="평균 일일 변동폭"
                        )
                    with col4:
                        market_kospi_adr = st.number_input(
                            "코스피 ADR",
                            min_value=0.0,
                            value=float(kospi_adr_value) if kospi_adr_value else 0.0,
                            step=0.1,
                            help="코스피 시장 ADR"
                        )
                    with col5:
                        market_kosdaq_adr = st.number_input(
                            "코스닥 ADR",
                            min_value=0.0,
                            value=float(kosdaq_adr_value) if kosdaq_adr_value else 0.0,
                            step=0.1,
                            help="코스닥 시장 ADR"
                        )

                    st.markdown("#### 📝 투자 근거 (선택사항)")
                    # 매수 이유
                    reason = st.text_area(
                        "매수 이유",
                        placeholder="이 종목을 매수한 이유를 간단히 작성해주세요...",
                        height=100,
                        label_visibility="collapsed"
                    )

                    # 제출 버튼
                    st.markdown("")  # 간격 추가
                    st.markdown(f"**선택된 매수일:** {buy_date.strftime('%Y년 %m월 %d일')}")
                    st.markdown("")  # 간격 추가

                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        submitted = st.form_submit_button("💾 매수 기록 저장", use_container_width=True, type="primary")

                    if submitted:
                        if buy_price <= 0:
                            st.error("❌ 매수가를 입력해주세요.")
                        elif quantity <= 0:
                            st.error("❌ 매수 수량을 입력해주세요.")
                        else:
                            # 저장
                            if self.save_buy_record(ticker, stock_name, buy_price, quantity, rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, reason):
                                st.success(f"✅ {stock_name}({ticker}) {quantity}주 매수 기록이 저장되었습니다!")
                                # 세션 상태 초기화
                                del st.session_state.searched_ticker
                                del st.session_state.searched_name
                                del st.session_state.searched_price
                                del st.session_state.searched_chart
                                if 'searched_rsi' in st.session_state:
                                    del st.session_state.searched_rsi
                                if 'searched_macd' in st.session_state:
                                    del st.session_state.searched_macd
                                if 'searched_adr' in st.session_state:
                                    del st.session_state.searched_adr
                                if 'searched_kospi_adr' in st.session_state:
                                    del st.session_state.searched_kospi_adr
                                if 'searched_kosdaq_adr' in st.session_state:
                                    del st.session_state.searched_kosdaq_adr
                                if 'date_selector' in st.session_state:
                                    del st.session_state.date_selector
                                st.rerun()

                st.markdown("---")

                # 차트 표시 (매수 정보 입력 아래로 이동)
                if chart_df is not None and not chart_df.empty:
                    st.markdown("#### 📈 주가 차트 (최근 100일)")
                    fig = self.create_stock_chart(chart_df, stock_name)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

        # 탭 2: 보유 종목 조회
        with tab2:
            st.markdown("### 💼 보유 종목 조회")

            try:
                # 데이터베이스 경로를 project_root로 명시
                db_path = os.path.join(project_root, "stock_tracking_db.sqlite")
                with TradingJournalDB(db_path) as db:
                    positions = db.get_open_positions()

                    if not positions:
                        st.info("📭 현재 보유 중인 종목이 없습니다.")
                    else:
                        # 통계 정보 표시
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("보유 종목 수", f"{len(positions)}개")
                        with col2:
                            avg_profit = sum(p['profit_rate'] for p in positions) / len(positions) if positions else 0
                            st.metric("평균 수익률", f"{avg_profit:+.2f}%")
                        with col3:
                            profitable = sum(1 for p in positions if p['profit_rate'] > 0)
                            st.metric("수익 종목", f"{profitable}개")
                        with col4:
                            losing = sum(1 for p in positions if p['profit_rate'] < 0)
                            st.metric("손실 종목", f"{losing}개")

                        st.markdown("---")

                        # 보유 종목 목록 표시
                        for idx, pos in enumerate(positions, 1):
                            profit_rate = pos['profit_rate']
                            if profit_rate > 0:
                                color = "green"
                                emoji = "🔺"
                            elif profit_rate < 0:
                                color = "red"
                                emoji = "🔻"
                            else:
                                color = "gray"
                                emoji = "➖"

                            with st.expander(f"{emoji} {pos['company_name']} ({pos['ticker']}) - 수익률: {profit_rate:+.2f}%", expanded=(idx <= 3)):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.markdown(f"**매수가:** {pos['buy_price']:,.0f}원")
                                    st.markdown(f"**현재가:** {pos['current_price']:,.0f}원")
                                    st.markdown(f"**보유 수량:** {pos.get('quantity', 1)}주")
                                    st.markdown(f"**수익률:** :{color}[{profit_rate:+.2f}%]")

                                with col2:
                                    st.markdown(f"**매수일:** {pos['buy_date']}")
                                    st.markdown(f"**RSI:** {pos.get('rsi', 0):.2f}" if pos.get('rsi') else "**RSI:** N/A")
                                    st.markdown(f"**MACD:** {pos.get('macd', 0):.2f}" if pos.get('macd') else "**MACD:** N/A")

                                    # 평가금액 계산
                                    total_value = pos['current_price'] * pos.get('quantity', 1)
                                    st.markdown(f"**평가금액:** {total_value:,.0f}원")

                                with col3:
                                    st.markdown(f"**종목 ADR:** {pos.get('adr', 0):.2f}" if pos.get('adr') else "**종목 ADR:** N/A")
                                    st.markdown(f"**코스피 ADR:** {pos.get('market_kospi_adr', 0):.2f}" if pos.get('market_kospi_adr') else "**코스피 ADR:** N/A")
                                    st.markdown(f"**코스닥 ADR:** {pos.get('market_kosdaq_adr', 0):.2f}" if pos.get('market_kosdaq_adr') else "**코스닥 ADR:** N/A")

                                # 시나리오 정보
                                if pos.get('scenario'):
                                    try:
                                        scenario = json.loads(pos['scenario']) if isinstance(pos['scenario'], str) else pos['scenario']
                                        if scenario.get('rationale') != "미입력":
                                            st.markdown("**투자 근거:**")
                                            st.markdown(f"- {scenario.get('rationale', '정보 없음')}")
                                    except:
                                        pass

                        # 데이터프레임 표시
                        st.markdown("### 📋 요약 테이블")
                        df_data = []
                        for pos in positions:
                            df_data.append({
                                '종목명': pos['company_name'],
                                '종목코드': pos['ticker'],
                                '매수가': f"{pos['buy_price']:,.0f}원",
                                '현재가': f"{pos['current_price']:,.0f}원",
                                '수익률': f"{pos['profit_rate']:+.2f}%",
                                '매수일': pos['buy_date'].split()[0]
                            })

                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"보유 종목 조회 중 오류가 발생했습니다: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    def render_sell_records(self):
        """매도 기록 화면"""
        self.add_app_header()

        st.markdown("## 📉 매도 기록")
        st.markdown("과거 매도한 종목의 거래 내역을 확인할 수 있습니다.")

        if TradingJournalDB is None:
            st.error("TradingJournalDB 모듈을 불러올 수 없습니다. trading_journal_db.py 파일이 존재하는지 확인해주세요.")
            return

        try:
            # 데이터베이스 경로를 project_root로 명시
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")
            with TradingJournalDB(db_path) as db:
                # 전체 매도 기록 조회
                history = db.get_trading_history(limit=9999)

                if not history:
                    st.info("📭 매도 기록이 없습니다.")
                    return

                # 통계 정보
                stats = db.get_statistics()
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("총 거래", f"{stats.get('total_trades', 0)}건")
                with col2:
                    st.metric("수익 거래", f"{stats.get('profitable_trades', 0)}건",
                             delta=f"{stats.get('win_rate', 0):.1f}% 승률")
                with col3:
                    st.metric("손실 거래", f"{stats.get('losing_trades', 0)}건")
                with col4:
                    st.metric("평균 수익률", f"{stats.get('avg_profit_rate', 0):+.2f}%")

                st.markdown("---")

                # 정렬 옵션
                st.markdown("### 💰 매도 내역")
                col1, col2 = st.columns([3, 1])
                with col2:
                    sort_option = st.selectbox(
                        "정렬 기준",
                        ["매도일 (오래된순)", "매도일 (최신순)", "수익률 (높은순)", "수익률 (낮은순)", "보유기간 (긴순)", "보유기간 (짧은순)"],
                        index=0
                    )

                # 정렬 적용
                if sort_option == "매도일 (오래된순)":
                    history.sort(key=lambda x: x['sell_date'])
                elif sort_option == "매도일 (최신순)":
                    history.sort(key=lambda x: x['sell_date'], reverse=True)
                elif sort_option == "수익률 (높은순)":
                    history.sort(key=lambda x: x['profit_rate'], reverse=True)
                elif sort_option == "수익률 (낮은순)":
                    history.sort(key=lambda x: x['profit_rate'])
                elif sort_option == "보유기간 (긴순)":
                    history.sort(key=lambda x: x['holding_days'], reverse=True)
                elif sort_option == "보유기간 (짧은순)":
                    history.sort(key=lambda x: x['holding_days'])

                st.markdown(f"**총 {len(history)}건의 거래 내역**")

                for idx, trade in enumerate(history, 1):
                    profit_rate = trade['profit_rate']
                    if profit_rate > 0:
                        color = "green"
                        emoji = "✅"
                        result = "수익"
                    else:
                        color = "red"
                        emoji = "❌"
                        result = "손실"

                    with st.expander(f"{emoji} {trade['company_name']} ({trade['ticker']}) - {result}: {profit_rate:+.2f}%", expanded=(idx <= 5)):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**매수가:** {trade['buy_price']:,.0f}원")
                            st.markdown(f"**매도가:** {trade['sell_price']:,.0f}원")
                            st.markdown(f"**수익률:** :{color}[{profit_rate:+.2f}%]")

                        with col2:
                            st.markdown(f"**매수일:** {trade['buy_date']}")
                            st.markdown(f"**매도일:** {trade['sell_date']}")
                            st.markdown(f"**보유기간:** {trade['holding_days']}일")

                        # 시나리오 정보
                        if trade.get('scenario'):
                            try:
                                scenario = json.loads(trade['scenario']) if isinstance(trade['scenario'], str) else trade['scenario']
                                st.markdown("**투자 정보:**")
                                st.markdown(f"- 투자 기간: {scenario.get('investment_period', '중기')}")
                                st.markdown(f"- 산업군: {scenario.get('sector', '알 수 없음')}")
                            except:
                                pass

                # 데이터프레임으로도 표시
                st.markdown("### 📋 거래 내역 테이블")
                df_data = []
                for trade in history:
                    df_data.append({
                        '종목명': trade['company_name'],
                        '종목코드': trade['ticker'],
                        '매수가': f"{trade['buy_price']:,.0f}원",
                        '매도가': f"{trade['sell_price']:,.0f}원",
                        '수익률': f"{trade['profit_rate']:+.2f}%",
                        '보유기간': f"{trade['holding_days']}일",
                        '매도일': trade['sell_date'].split()[0]
                    })

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"매도 기록 조회 중 오류가 발생했습니다: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    def main(self):
        """메인 애플리케이션 실행"""
        # 사이드바 디자인 개선
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-logo">📊</div>
            <div class="sidebar-title">analysis.stocksimulation.kr</div>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.title("메뉴")

        # 모던한 사이드바 메뉴
        menu_options = {
            "분석 요청": "📝",
            "보고서 보기": "📚",
            "매수 기록": "💰",
            "매도 기록": "📉"
        }

        menu = st.sidebar.radio(
            "선택",
            list(menu_options.keys()),
            format_func=lambda x: f"{menu_options[x]} {x}"
        )

        # 앱 버전 및 소셜 링크
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 서비스 정보")
        st.sidebar.markdown("버전: v1.0.3")
        st.sidebar.markdown("© 2025 https://analysis.stocksimulation.kr")

        # 메인 콘텐츠 렌더링
        if menu == "분석 요청":
            self.render_modern_analysis_form()
        elif menu == "보고서 보기":
            self.render_modern_report_viewer()
        elif menu == "매수 기록":
            self.render_buy_records()
        elif menu == "매도 기록":
            self.render_sell_records()

if __name__ == "__main__":
    app = ModernStockAnalysisApp()
    app.main()
