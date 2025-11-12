import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any
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

# 상태 파일 저장 디렉토리 설정
STATUS_DIR = Path(__file__).parent.parent.parent / "analysis_status"
STATUS_DIR.mkdir(exist_ok=True)

# 요약 정보 저장 디렉토리 설정
SUMMARY_DIR = Path(__file__).parent.parent.parent / "analysis_summary"
SUMMARY_DIR.mkdir(exist_ok=True)

# 작업 큐 및 스레드 풀 설정
analysis_queue = Queue()

# 상태 관리 헬퍼 함수
def update_analysis_status(request_id: str, status: str, progress: int, message: str, current_step: str = ""):
    """분석 상태를 파일에 저장"""
    status_file = STATUS_DIR / f"status_{request_id}.json"
    status_data = {
        "status": status,
        "progress": progress,
        "message": message,
        "current_step": current_step,
        "updated_at": datetime.now().isoformat()
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

def get_analysis_status(request_id: str) -> dict:
    """분석 상태를 파일에서 읽기"""
    status_file = STATUS_DIR / f"status_{request_id}.json"
    if status_file.exists():
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "pending",
        "progress": 0,
        "message": "분석 대기 중...",
        "current_step": "",
        "updated_at": datetime.now().isoformat()
    }

def cleanup_status_file(request_id: str):
    """분석 완료 후 상태 파일 삭제 (선택적)"""
    status_file = STATUS_DIR / f"status_{request_id}.json"
    if status_file.exists():
        status_file.unlink()

class AnalysisRequest:
    def __init__(self, stock_code: str, reference_date: str):
        self.id = str(uuid.uuid4())
        self.stock_code = stock_code
        self.company_name = self._get_company_name(stock_code)
        self.reference_date = reference_date
        self.status = "pending"
        self.result = None
        self.progress = 0
        self.current_step = ""
        self.message = "분석 대기 중..."

    @staticmethod
    def _get_company_name(stock_code: str) -> str:
        """종목코드로 회사명 자동 조회"""
        try:
            if stock:  # pykrx가 사용 가능한 경우
                # 코스피 조회
                name = stock.get_market_ticker_name(stock_code)
                if name:
                    return name
            # 조회 실패 시 종목코드 반환
            return stock_code
        except:
            return stock_code

class ModernStockAnalysisApp:
    def __init__(self):
        self.setup_page()
        self.initialize_session_state()
        self.start_background_worker()

    def setup_page(self):
        """페이지 설정 및 커스텀 CSS 적용"""
        st.set_page_config(
            page_title="프리즘 애널리틱스 | AI 주식 분석 에이전트",
            page_icon="📊",
            layout="wide",
            # Open Graph 메타데이터 추가
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': """
                # 프리즘 애널리틱스
                AI 주식 분석 에이전트
                """
            }
        )

        # Open Graph 태그 직접 주입
        og_html = """
        <head>
            <title>프리즘 애널리틱스 | AI 주식 분석 에이전트</title>
            <meta property="og:title" content="프리즘 애널리틱스 | AI 주식 분석 에이전트" />
            <meta property="og:description" content="AI 주식 분석 에이전트" />
            <meta property="og:image" content="https://media.istockphoto.com/id/2045262949/ko/%EC%82%AC%EC%A7%84/excited-businessman-raises-hands-and-punches-air-while-celebrating-successful-deal-stock.jpg?s=2048x2048&w=is&k=20&c=XtdmbV6gILRK1ahoMOf0_SFC256rgHyiaID_FeW4ojU=" />
            <meta property="og:url" content="https://analysis.stocksimulation.kr" />
            <meta property="og:type" content="website" />
            <meta property="og:site_name" content="프리즘 애널리틱스" />
        </head>
        """
        st.markdown(og_html, unsafe_allow_html=True)

        # 커스텀 CSS 적용
        self.apply_custom_styles()

    def apply_custom_styles(self):
        """모던한 다크/라이트 테마 대응 디자인 스타일 적용"""
        # CSS 파일 경로
        css_file = Path(__file__).parent / "modern_theme.css"

        # CSS 파일 읽기
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()

            # CSS 적용
            st.markdown(f"""
            <style>
            {css_content}
            </style>
            """, unsafe_allow_html=True)

        except FileNotFoundError:
            st.warning("⚠️ CSS 테마 파일을 찾을 수 없습니다. 기본 스타일을 사용합니다.")
            # 기본 스타일 (fallback)
            st.markdown("""
            <style>
            .main {
                background-color: #fafafa;
                padding: 1.5rem;
            }
            </style>
            """, unsafe_allow_html=True)

    def add_app_header(self):
        """앱 헤더와 브랜딩 추가"""
        st.markdown("""
        <div class="header">
            <div class="logo-container">
                <div class="logo">📊</div>
                <div class="app-title">프리즘 애널리틱스</div>
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
        if 'current_analysis' not in st.session_state:
            st.session_state.current_analysis = None
        if 'analysis_mode' not in st.session_state:
            st.session_state.analysis_mode = False

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
                request.status = "completed"
                request.progress = 100
                request.message = "캐시된 보고서 로드 완료"
                update_analysis_status(request.id, "completed", 100, "캐시된 보고서 로드 완료", "완료")
            else:
                # 초기 상태 파일 생성
                update_analysis_status(request.id, "pending", 5, "분석 준비 중...", "분석 준비")
                request.progress = 5
                request.message = "분석 준비 중..."
                request.current_step = "분석 준비"

                # 별도 프로세스로 분석 실행
                import subprocess
                import tempfile
                import json

                # 프로젝트 루트 디렉토리와 streamlit 디렉토리 경로
                project_root = str(Path(__file__).parent.parent.parent.absolute())
                streamlit_dir = str(Path(__file__).parent.absolute())
                status_dir = str(STATUS_DIR.absolute())
                summary_dir = str(SUMMARY_DIR.absolute())

                # 요청 정보를 임시 파일에 저장
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    request_info = {
                        'request_id': request.id,
                        'stock_code': request.stock_code,
                        'company_name': request.company_name,
                        'reference_date': request.reference_date,
                        'output_file': f"reports/{request.stock_code}_{request.company_name}_{request.reference_date}_gpt4.1.md",
                        'status_dir': status_dir,
                        'summary_dir': summary_dir
                    }
                    json.dump(request_info, f)
                    request_file = f.name

                # 별도 프로세스 실행
                subprocess.Popen([
                    "python", "-c",
                    f'''
import asyncio, json, os, sys
from datetime import datetime
from pathlib import Path

# Python path 설정
project_root = "{project_root}"
streamlit_dir = "{streamlit_dir}"
sys.path.insert(0, project_root)
sys.path.insert(0, streamlit_dir)

# 작업 디렉토리 변경
os.chdir(project_root)

# 상태 업데이트 함수
def update_status(request_id, status, progress, message, current_step=""):
    status_file = Path("{status_dir}") / f"status_{{request_id}}.json"
    status_data = {{
        "status": status,
        "progress": progress,
        "message": message,
        "current_step": current_step,
        "updated_at": datetime.now().isoformat()
    }}
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

# 요청 정보 로드
with open("{request_file}", "r") as f:
    info = json.load(f)

request_id = info["request_id"]

try:
    # 1단계: 모듈 임포트
    update_status(request_id, "analyzing", 10, "AI 분석 모듈 로드 중...", "모듈 로드")
    from cores.main import analyze_stock

    # 2단계: 데이터 수집 시작
    update_status(request_id, "analyzing", 20, "주가 및 재무 데이터 수집 중...", "데이터 수집")

    # 분석 실행
    async def run():
        try:
            # 3단계: AI 분석 시작
            update_status(request_id, "analyzing", 40, "AI 종합 분석 수행 중...", "AI 분석")

            report = await analyze_stock(
                company_code=info["stock_code"],
                company_name=info["company_name"],
                reference_date=info["reference_date"]
            )

            # 4단계: 보고서 작성
            update_status(request_id, "analyzing", 80, "분석 보고서 작성 중...", "보고서 작성")

            # 결과 저장
            with open(info["output_file"], "w", encoding="utf-8") as f:
                f.write(report)

            # 4.5단계: 요약 정보 생성
            update_status(request_id, "analyzing", 90, "핵심 정보 요약 중...", "요약 생성")

            try:
                from cores.report_parser import parse_report_file, save_summary_json

                # 보고서 파싱 및 요약 생성
                summary = parse_report_file(info["output_file"])

                # 요약 JSON 저장
                summary_file = Path(info["summary_dir"]) / f"summary_{{request_id}}.json"
                save_summary_json(summary, str(summary_file))

            except Exception as e:
                # 요약 생성 실패해도 분석은 완료로 처리
                print(f"Warning: Failed to generate summary: {{e}}")

            # 5단계: 완료
            update_status(request_id, "completed", 100, "분석이 완료되었습니다!", "완료")

        except Exception as e:
            update_status(request_id, "failed", 0, f"분석 중 오류 발생: {{str(e)}}", "오류")
            raise

    asyncio.run(run())

    # 임시 파일 삭제
    os.remove("{request_file}")

except Exception as e:
    update_status(request_id, "failed", 0, f"분석 중 오류 발생: {{str(e)}}", "오류")
    import traceback
    traceback.print_exc()
'''
                ], cwd=project_root)

                request.result = f"분석이 시작되었습니다."
                # status는 pending으로 유지 (백그라운드 프로세스가 업데이트)

        except Exception as e:
            request.status = "failed"
            request.result = f"분석 중 오류가 발생했습니다: {str(e)}"
            update_analysis_status(request.id, "failed", 0, str(e), "오류")

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

    def submit_analysis(self, stock_code: str, reference_date: str) -> str:
        """분석 요청 제출"""
        request = AnalysisRequest(stock_code, reference_date)
        st.session_state.requests[request.id] = request
        analysis_queue.put(request)
        return request.id

    def render_modern_analysis_form(self):
        """모던한 디자인의 분석 요청 폼"""
        # 커스텀 헤더 추가
        self.add_app_header()

        # 분석 모드가 활성화된 경우 분석 상세 페이지 렌더링
        if st.session_state.analysis_mode and st.session_state.current_analysis:
            self.render_analysis_detail()
            return

        # 앱 설명 카드 (텍스트만 사용)
        st.markdown("### 🤖 AI 주식 분석 에이전트 서비스")
        st.markdown("이 서비스는 AI를 활용하여 종목을 심층 분석하고 전문가 수준의 투자 분석 보고서를 자동으로 생성합니다.")

        # 두 개의 열로 나누어 레이아웃 구성
        col1, col2 = st.columns([2, 1])

        with col1:
            # 분석 요청 카드
            st.markdown("## 분석 요청")

            with st.form("analysis_form"):
                stock_code = st.text_input("종목코드", placeholder="예: 005930 (6자리)")

                # 디자인된 제출 버튼
                submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
                with submit_col2:
                    submitted = st.form_submit_button("분석 시작", use_container_width=True)

            # 폼 제출 처리
            if submitted:
                if not self.validate_inputs(stock_code):
                    return

                # 자동으로 오늘 날짜 사용
                reference_date = datetime.now().strftime("%Y%m%d")
                request_id = self.submit_analysis(stock_code, reference_date)

                # 분석 모드 활성화
                st.session_state.analysis_mode = True
                st.session_state.current_analysis = request_id
                st.rerun()

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
            st.markdown("### ⏱️ 분석 예상 시간")
            st.markdown("**5-10분** 소요 예상")

    def render_analysis_detail(self):
        """분석 상세 페이지 렌더링"""
        request_id = st.session_state.current_analysis

        if request_id not in st.session_state.requests:
            st.error("분석 요청을 찾을 수 없습니다.")
            if st.button("🏠 처음으로 돌아가기"):
                st.session_state.analysis_mode = False
                st.session_state.current_analysis = None
                st.rerun()
            return

        request = st.session_state.requests[request_id]

        # 상태 파일에서 실시간 상태 읽기
        status_data = get_analysis_status(request_id)
        current_status = status_data.get("status", "pending")
        progress = status_data.get("progress", 0)
        message = status_data.get("message", "분석 대기 중...")
        current_step = status_data.get("current_step", "")

        # request 객체 업데이트
        request.progress = progress
        request.message = message
        request.current_step = current_step

        # status 업데이트 (completed나 failed는 변경)
        if current_status in ["completed", "failed"]:
            request.status = current_status

        # 헤더
        if current_status == "completed":
            st.markdown(f"# ✅ AI 분석 완료!")
        elif current_status == "failed":
            st.markdown(f"# ❌ 분석 실패")
        else:
            st.markdown(f"# 🔬 AI 분석 진행 중")

        st.markdown(f"## **{request.company_name}** ({request.stock_code})")
        st.markdown("---")

        # 진행 상황에 따른 표시
        if current_status in ["pending", "analyzing"]:
            # 진행 중
            st.markdown("### 📊 분석 진행 상황")

            # 실시간 프로그레스 바
            progress_value = progress / 100.0
            st.progress(progress_value)

            # 현재 상태 메시지 표시
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**현재 단계**: {current_step}")
            with col2:
                st.markdown(f"**진행률**: {progress}%")
            with col3:
                # 경과 시간 계산
                import time
                if not hasattr(request, 'start_time'):
                    request.start_time = time.time()
                elapsed = int(time.time() - request.start_time)
                st.markdown(f"**경과**: {elapsed // 60}분 {elapsed % 60}초")

            st.info(f"⏳ {message}")

            # 단계별 상세 정보
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🔍 분석 단계")

                # 진행률 기반 단계 표시
                steps = [
                    {"icon": "🔍", "title": "분석 준비", "progress_threshold": 5},
                    {"icon": "📊", "title": "모듈 로드", "progress_threshold": 10},
                    {"icon": "📈", "title": "데이터 수집", "progress_threshold": 20},
                    {"icon": "🤖", "title": "AI 분석", "progress_threshold": 40},
                    {"icon": "📝", "title": "보고서 작성", "progress_threshold": 80},
                    {"icon": "🎯", "title": "요약 생성", "progress_threshold": 90},
                    {"icon": "✅", "title": "완료", "progress_threshold": 100}
                ]

                for step in steps:
                    if progress >= step["progress_threshold"]:
                        st.markdown(f"✅ {step['icon']} {step['title']}")
                    elif progress >= step["progress_threshold"] - 5:
                        st.markdown(f"🔄 **{step['icon']} {step['title']} (진행 중)**")
                    else:
                        st.markdown(f"⏳ {step['icon']} {step['title']}")

            with col2:
                st.markdown("#### 📈 분석 내용")
                analysis_items = [
                    "📊 기술적 지표 분석",
                    "💰 재무제표 분석",
                    "🏢 경쟁사 비교 분석",
                    "📰 뉴스 센티멘트 분석",
                    "📈 투자 지표 산출"
                ]
                for item in analysis_items:
                    st.markdown(f"• {item}")

            st.markdown("---")
            st.warning("⏳ 분석이 진행 중입니다. 예상 소요 시간: 5-10분\n\n이 페이지는 3초마다 자동으로 새로고침됩니다.")

            # 자동 새로고침 (3초마다)
            import time
            time.sleep(3)
            st.rerun()

        elif current_status == "completed":
            # 완료
            st.success("✅ 분석이 완료되었습니다!")

            # 요약 정보 로드
            summary_file = SUMMARY_DIR / f"summary_{request_id}.json"
            summary = None
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)

            # 요약 카드 표시
            if summary:
                st.markdown("---")
                st.markdown("## 🎯 AI 종합 평가")

                # 핵심 지표 3개
                col1, col2, col3 = st.columns(3)

                with col1:
                    opinion = summary.get('investment_opinion', '분석중')
                    opinion_emoji = "🟢" if opinion == "매수" else "🟡" if opinion == "중립" else "🔴" if opinion == "매도" else "⚪"
                    st.markdown(f"### {opinion_emoji} 투자 의견")
                    st.markdown(f"**{opinion}**")

                with col2:
                    target = summary.get('target_price', 'N/A')
                    st.markdown(f"### 💰 목표가")
                    st.markdown(f"**{target}**")

                with col3:
                    risk = summary.get('risk_level', '중간')
                    risk_emoji = "🔴" if risk == "높음" else "🟡" if risk == "중간" else "🟢"
                    st.markdown(f"### {risk_emoji} 리스크")
                    st.markdown(f"**{risk}**")

                # 주요 분석 하이라이트
                st.markdown("---")
                st.markdown("## 📊 주요 분석 하이라이트")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 💡 기술적 분석")
                    tech_indicators = summary.get('technical_indicators', {})
                    if tech_indicators:
                        if 'rsi' in tech_indicators:
                            st.markdown(f"• **RSI**: {tech_indicators['rsi']}")
                        if 'macd' in tech_indicators:
                            st.markdown(f"• **MACD**: {tech_indicators['macd']}")
                        if 'moving_average' in tech_indicators:
                            st.markdown(f"• **이동평균**: {tech_indicators['moving_average']}")
                    else:
                        st.info("기술적 지표 정보 없음")

                    st.markdown("### 💰 재무 분석")
                    fin_metrics = summary.get('financial_metrics', {})
                    if fin_metrics:
                        if 'per' in fin_metrics:
                            st.markdown(f"• **PER**: {fin_metrics['per']}")
                        if 'pbr' in fin_metrics:
                            st.markdown(f"• **PBR**: {fin_metrics['pbr']}")
                        if 'roe' in fin_metrics:
                            st.markdown(f"• **ROE**: {fin_metrics['roe']}%")
                    else:
                        st.info("재무 지표 정보 없음")

                with col2:
                    st.markdown("### 🎯 매수 전략")
                    buy_zones = summary.get('buy_zones', [])
                    if buy_zones:
                        for i, zone in enumerate(buy_zones[:3], 1):
                            st.markdown(f"• **{i}차 매수**: {zone.get('low')} ~ {zone.get('high')}")
                    else:
                        st.info("매수 가격대 정보 없음")

                    stop_loss = summary.get('stop_loss')
                    if stop_loss:
                        st.markdown(f"• **손절가**: {stop_loss}")

                    st.markdown("### 📈 핵심 투자 포인트")
                    key_points = summary.get('key_points', [])
                    if key_points:
                        for point in key_points[:3]:
                            st.markdown(f"• {point}")
                    else:
                        st.info("핵심 포인트 정보 없음")

                # 다음 액션
                st.markdown("---")
                st.markdown("## 🎬 다음 액션")

                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button("📄 전체 보고서 보기", use_container_width=True, type="primary"):
                        st.session_state.analysis_mode = False
                        st.session_state.current_analysis = None
                        st.info("보고서 보기 메뉴로 이동하여 결과를 확인하세요.")

                with btn_col2:
                    if st.button("📊 차트 상세 분석", use_container_width=True):
                        st.info("차트 분석 기능은 준비 중입니다.")

                with btn_col3:
                    if st.button("💾 요약 다운로드", use_container_width=True):
                        # JSON 다운로드
                        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="JSON 다운로드",
                            data=summary_json,
                            file_name=f"summary_{request.company_name}_{request.stock_code}.json",
                            mime="application/json"
                        )

            else:
                # 요약 정보가 없는 경우 기본 화면
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown("### 📊 분석 결과")
                    st.markdown(f"**{request.result}**")

                with col2:
                    if st.button("📄 보고서 보기", use_container_width=True, type="primary"):
                        st.session_state.analysis_mode = False
                        st.session_state.current_analysis = None
                        st.info("보고서 보기 메뉴로 이동하여 결과를 확인하세요.")

                # 분석 완료 상세 정보
                st.markdown("---")
                st.markdown("### ✨ 생성된 분석 항목")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("기술적 분석", "완료 ✅")
                    st.metric("재무 분석", "완료 ✅")

                with col2:
                    st.metric("경쟁사 비교", "완료 ✅")
                    st.metric("투자 지표", "완료 ✅")

                with col3:
                    st.metric("뉴스 분석", "완료 ✅")
                    st.metric("종합 평가", "완료 ✅")

        elif current_status == "failed":
            # 실패
            st.error("❌ 분석 중 오류가 발생했습니다.")
            st.markdown(f"**오류 내용**: {message}")

            st.markdown("---")
            st.warning("분석을 다시 시도하거나, 종목코드를 확인해주세요.")

        # 하단 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🏠 처음으로 돌아가기", use_container_width=True):
                st.session_state.analysis_mode = False
                st.session_state.current_analysis = None
                st.rerun()

        with col2:
            if current_status == "completed" or current_status == "failed":
                if st.button("🔄 새 분석 시작", use_container_width=True, type="primary"):
                    st.session_state.analysis_mode = False
                    st.session_state.current_analysis = None
                    st.rerun()

        with col3:
            if st.button("📋 분석 기록 보기", use_container_width=True):
                st.session_state.analysis_mode = False
                st.session_state.current_analysis = None
                st.info("보고서 보기 메뉴에서 과거 분석 기록을 확인하세요.")

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

    def validate_inputs(self, stock_code: str) -> bool:
        """입력값 유효성 검사"""
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
        global stock

        try:
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
        global stock

        if stock is None:
            return None, None, None, None, None, None

        try:
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

    def save_buy_record(self, ticker, company_name, buy_price, buy_date, quantity, rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, reason):
        """매수 기록 저장"""
        try:
            # 데이터베이스 경로를 project_root로 명시
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")

            # TradingJournalDB를 사용하여 저장
            with TradingJournalDB(db_path) as db:
                # buy_date가 date 객체인 경우 문자열로 변환
                if hasattr(buy_date, 'strftime'):
                    buy_date_str = buy_date.strftime("%Y-%m-%d")
                else:
                    buy_date_str = str(buy_date)

                scenario = {
                    "rationale": reason if reason else "미입력",
                    "investment_period": "중기",
                    "sector": "기타"
                }

                success = db.add_position(
                    ticker=ticker,
                    company_name=company_name,
                    buy_price=buy_price,
                    buy_date=buy_date_str,
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
        global stock, TradingJournalDB

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

                # Form 밖에서 매수가 입력 및 금액 선택
                st.markdown("#### 💵 거래 정보")

                # 매수가 입력 (form 밖에서 session_state에 저장)
                if 'buy_price_input' not in st.session_state:
                    st.session_state.buy_price_input = int(current_price) if current_price else 0

                buy_price = st.number_input(
                    "💰 매수가 (원) *",
                    min_value=1,
                    value=st.session_state.buy_price_input,
                    step=100,
                    key="buy_price_field",
                    help="실제 매수한 가격을 입력해주세요"
                )
                st.session_state.buy_price_input = buy_price

                st.markdown("---")
                st.markdown("#### 💸 투자 금액 선택")
                st.markdown("버튼을 클릭할 때마다 수량이 누적됩니다.")

                # 세션 상태 초기화
                if 'accumulated_quantity' not in st.session_state:
                    st.session_state.accumulated_quantity = 0
                if 'accumulated_amount' not in st.session_state:
                    st.session_state.accumulated_amount = 0

                # 금액 버튼들
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button("💵 10만원", use_container_width=True):
                        if buy_price > 0:
                            qty = int(100000 / buy_price)
                            st.session_state.accumulated_quantity += qty
                            st.session_state.accumulated_amount += qty * buy_price
                        else:
                            st.warning("매수가를 먼저 입력하세요")

                with col2:
                    if st.button("💵 20만원", use_container_width=True):
                        if buy_price > 0:
                            qty = int(200000 / buy_price)
                            st.session_state.accumulated_quantity += qty
                            st.session_state.accumulated_amount += qty * buy_price
                        else:
                            st.warning("매수가를 먼저 입력하세요")

                with col3:
                    if st.button("💵 50만원", use_container_width=True):
                        if buy_price > 0:
                            qty = int(500000 / buy_price)
                            st.session_state.accumulated_quantity += qty
                            st.session_state.accumulated_amount += qty * buy_price
                        else:
                            st.warning("매수가를 먼저 입력하세요")

                with col4:
                    if st.button("💵 100만원", use_container_width=True):
                        if buy_price > 0:
                            qty = int(1000000 / buy_price)
                            st.session_state.accumulated_quantity += qty
                            st.session_state.accumulated_amount += qty * buy_price
                        else:
                            st.warning("매수가를 먼저 입력하세요")

                with col5:
                    if st.button("🔄 초기화", type="secondary", use_container_width=True):
                        st.session_state.accumulated_quantity = 0
                        st.session_state.accumulated_amount = 0
                        st.rerun()

                # 직접 입력
                st.markdown("##### ✏️ 직접 입력")
                col1, col2 = st.columns([3, 1])
                with col1:
                    custom_amount = st.number_input(
                        "투자 금액 (원)",
                        min_value=0,
                        value=0,
                        step=10000,
                        key="custom_amount_field",
                        help="원하는 투자 금액을 입력하세요"
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)  # 정렬을 위한 여백
                    if st.button("➕ 추가", use_container_width=True):
                        if buy_price > 0 and custom_amount > 0:
                            qty = int(custom_amount / buy_price)
                            st.session_state.accumulated_quantity += qty
                            st.session_state.accumulated_amount += qty * buy_price
                            st.rerun()
                        else:
                            st.warning("매수가와 금액을 입력하세요")

                # 누적 수량 및 금액 표시
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("누적 수량", f"{st.session_state.accumulated_quantity}주",
                             help="버튼 클릭으로 누적된 총 수량")
                with col2:
                    st.metric("누적 투자금액", f"{st.session_state.accumulated_amount:,}원",
                             help="누적 수량 × 매수가")

                # calculated_quantity 설정 (최종 수량 필드에 사용)
                calculated_quantity = st.session_state.accumulated_quantity if st.session_state.accumulated_quantity > 0 else 1

                st.markdown("---")

                # Form 시작 (최종 수량 및 기타 정보 입력용)
                with st.form("buy_record_form"):

                    # 최종 수량 입력 (수정 가능)
                    col1, col2 = st.columns(2)
                    with col1:
                        quantity = st.number_input(
                            "📦 최종 매수 수량 *",
                            min_value=1,
                            value=calculated_quantity if calculated_quantity > 0 else 1,
                            step=1,
                            help="위에서 계산된 수량이 자동 입력됩니다. 수정 가능합니다."
                        )
                    with col2:
                        total_investment = buy_price * quantity
                        st.metric("총 투자금액", f"{total_investment:,}원")

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
                            # 저장 - buy_date를 전달
                            if self.save_buy_record(ticker, stock_name, buy_price, buy_date, quantity, rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, reason):
                                st.success(f"✅ {stock_name}({ticker}) {quantity}주 매수 기록이 저장되었습니다!")
                                st.info("💡 새로운 종목을 등록하려면 위에서 종목코드를 다시 입력하세요.")
                                # 세션 상태 초기화 - 모든 관련 상태 제거
                                for key in ['searched_ticker', 'searched_name', 'searched_price', 'searched_chart',
                                           'searched_rsi', 'searched_macd', 'searched_adr',
                                           'searched_kospi_adr', 'searched_kosdaq_adr', 'date_selector',
                                           'accumulated_quantity', 'accumulated_amount', 'buy_price_input']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                # rerun 없이 상태만 초기화하여 사용자가 계속 작업할 수 있도록 함
                                # st.rerun()을 제거하여 form이 정상적으로 리셋되도록 함

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

            # 현재가 업데이트 버튼
            col1, col2, col3 = st.columns([4, 1, 1])
            with col2:
                refresh_button = st.button("🔄 자동 업데이트", use_container_width=True)
            with col3:
                manual_update = st.button("✏️ 수동 입력", use_container_width=True)

            try:
                # 데이터베이스 경로를 project_root로 명시
                db_path = os.path.join(project_root, "stock_tracking_db.sqlite")

                # 탭 진입 시 자동으로 1회 업데이트 (pykrx 사용 가능한 경우에만)
                if 'buy_records_auto_updated' not in st.session_state and stock is not None:
                    with st.spinner("💡 현재가를 자동으로 업데이트하는 중..."):
                        with TradingJournalDB(db_path) as db:
                            positions = db.get_open_positions()
                            if positions:  # 보유 종목이 있을 때만
                                tickers = list(set([p['ticker'] for p in positions]))
                                updated_count = 0
                                for ticker in tickers:
                                    try:
                                        end_date = datetime.now().strftime("%Y%m%d")
                                        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
                                        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
                                        if not df.empty:
                                            current_price = df['종가'].iloc[-1]
                                            db.cursor.execute("""
                                                UPDATE stock_holdings
                                                SET current_price = ?, last_updated = ?
                                                WHERE ticker = ? AND (is_sold = 0 OR is_sold IS NULL)
                                            """, (current_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticker))
                                            updated_count += 1
                                    except:
                                        continue
                                db.conn.commit()
                                if updated_count > 0:
                                    st.info(f"✅ {updated_count}개 종목의 현재가가 자동 업데이트되었습니다!")
                    st.session_state.buy_records_auto_updated = True

                # 현재가 업데이트가 요청되었을 때
                if refresh_button and stock is not None:
                    with st.spinner("현재가를 업데이트하고 있습니다..."):
                        with TradingJournalDB(db_path) as db:
                            # 모든 보유 종목의 ticker를 가져옴
                            positions = db.get_open_positions()
                            tickers = list(set([p['ticker'] for p in positions]))

                            # 각 ticker의 현재가를 가져와서 업데이트
                            updated_count = 0
                            for ticker in tickers:
                                try:
                                    # 현재가 조회
                                    end_date = datetime.now().strftime("%Y%m%d")
                                    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

                                    df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
                                    if not df.empty:
                                        current_price = df['종가'].iloc[-1]

                                        # 해당 ticker의 모든 레코드 업데이트
                                        db.cursor.execute("""
                                            UPDATE stock_holdings
                                            SET current_price = ?, last_updated = ?
                                            WHERE ticker = ? AND (is_sold = 0 OR is_sold IS NULL)
                                        """, (current_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticker))
                                        updated_count += 1
                                except Exception as e:
                                    # 개별 종목 업데이트 실패는 무시하고 계속 진행
                                    continue

                            db.conn.commit()
                            st.success(f"✅ {updated_count}개 종목의 현재가가 업데이트되었습니다!")

                # 수동 업데이트 모드
                if manual_update:
                    st.session_state.manual_update_mode = True

                # 수동 업데이트 폼 표시
                if st.session_state.get('manual_update_mode', False):
                    st.markdown("---")
                    st.markdown("### ✏️ 수동 현재가 입력")
                    st.markdown("종목별로 현재가를 직접 입력하세요.")

                    with TradingJournalDB(db_path) as db:
                        # 중복 제거된 종목 리스트
                        db.cursor.execute("""
                            SELECT DISTINCT ticker, company_name,
                                   MAX(current_price) as current_price
                            FROM stock_holdings
                            WHERE is_sold = 0 OR is_sold IS NULL
                            GROUP BY ticker
                        """)
                        unique_stocks = db.cursor.fetchall()

                        if not unique_stocks:
                            st.info("보유 종목이 없습니다.")
                        else:
                            with st.form("manual_price_update_form"):
                                st.markdown("#### 현재가 입력")

                                price_updates = {}
                                for stock_row in unique_stocks:
                                    ticker = stock_row['ticker']
                                    company_name = stock_row['company_name']
                                    current_price = stock_row['current_price']

                                    # current_price를 float로 변환 (bytes 타입 대응)
                                    try:
                                        if isinstance(current_price, bytes):
                                            current_price = float(current_price.decode())
                                        else:
                                            current_price = float(current_price) if current_price else 0.0
                                    except:
                                        current_price = 0.0

                                    col1, col2 = st.columns([3, 2])
                                    with col1:
                                        st.markdown(f"**{company_name} ({ticker})**")
                                        st.caption(f"현재 DB 저장값: {current_price:,.0f}원")
                                    with col2:
                                        new_price = st.number_input(
                                            "새 현재가 (원)",
                                            min_value=0,
                                            value=int(current_price),
                                            step=100,
                                            key=f"price_{ticker}",
                                            label_visibility="collapsed"
                                        )
                                        price_updates[ticker] = new_price

                                st.markdown("")  # 간격 추가

                                col1, col2, col3 = st.columns([1, 1, 1])
                                with col1:
                                    submit = st.form_submit_button("💾 저장", use_container_width=True)
                                with col2:
                                    cancel = st.form_submit_button("❌ 취소", use_container_width=True)

                                if submit:
                                    updated_count = 0
                                    for ticker, new_price in price_updates.items():
                                        if new_price > 0:
                                            if db.update_current_price(ticker, float(new_price)):
                                                updated_count += 1

                                    st.success(f"✅ {updated_count}개 종목의 현재가가 업데이트되었습니다!")
                                    st.session_state.manual_update_mode = False
                                    st.rerun()

                                if cancel:
                                    st.session_state.manual_update_mode = False
                                    st.rerun()

                    st.markdown("---")

                with TradingJournalDB(db_path) as db:
                    aggregated = db.get_aggregated_positions()

                    if not aggregated:
                        st.info("📭 현재 보유 중인 종목이 없습니다.")
                    else:
                        # 통계 정보 표시
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("보유 종목 수", f"{len(aggregated)}개")
                        with col2:
                            avg_profit = sum(agg['profit_rate'] for agg in aggregated) / len(aggregated) if aggregated else 0
                            st.metric("평균 수익률", f"{avg_profit:+.2f}%")
                        with col3:
                            profitable = sum(1 for agg in aggregated if agg['profit_rate'] > 0)
                            st.metric("수익 종목", f"{profitable}개")
                        with col4:
                            losing = sum(1 for agg in aggregated if agg['profit_rate'] < 0)
                            st.metric("손실 종목", f"{losing}개")

                        st.markdown("---")

                        # 데이터프레임 표시 (종목별 합산) - 요약 테이블을 먼저 표시
                        st.markdown("### 📋 요약 테이블")
                        df_data = []
                        for agg in aggregated:
                            total_value = agg['current_price'] * agg['total_quantity']
                            net_profit = total_value - agg['total_cost']

                            df_data.append({
                                '종목명': agg['company_name'],
                                '종목코드': agg['ticker'],
                                '평균 매수가': f"{agg['avg_buy_price']:,.0f}원",
                                '현재가': f"{agg['current_price']:,.0f}원",
                                '총 수량': f"{agg['total_quantity']}주",
                                '매수 횟수': f"{agg['buy_count']}회",
                                '수익률': f"{agg['profit_rate']:+.2f}%",
                                '순수익': f"{net_profit:+,.0f}원"
                            })

                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        st.markdown("---")
                        st.markdown("### 📊 종목별 상세 정보")

                        # 보유 종목 목록 표시 (종목별 합산)
                        for idx, agg in enumerate(aggregated, 1):
                            profit_rate = agg['profit_rate']
                            if profit_rate > 0:
                                color = "green"
                                emoji = "🔺"
                            elif profit_rate < 0:
                                color = "red"
                                emoji = "🔻"
                            else:
                                color = "gray"
                                emoji = "➖"

                            ticker = agg['ticker']
                            company_name = agg['company_name']
                            buy_count = agg['buy_count']

                            # 종목별 합산 정보
                            with st.expander(
                                f"{emoji} {company_name} ({ticker}) - 총 {agg['total_quantity']}주 ({buy_count}회 매수) - 수익률: {profit_rate:+.2f}%",
                                expanded=(idx <= 3)
                            ):
                                # 합산 정보
                                st.markdown("#### 📊 종목 합산 정보")
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.markdown(f"**평균 매수가:** {agg['avg_buy_price']:,.0f}원")
                                    st.markdown(f"**현재가:** {agg['current_price']:,.0f}원")
                                    st.markdown(f"**총 보유 수량:** {agg['total_quantity']}주")

                                with col2:
                                    st.markdown(f"**총 투자금액:** {agg['total_cost']:,.0f}원")
                                    total_value = agg['current_price'] * agg['total_quantity']
                                    st.markdown(f"**총 평가금액:** {total_value:,.0f}원")
                                    profit_loss = total_value - agg['total_cost']
                                    st.markdown(f"**평가손익:** :{color}[{profit_loss:+,.0f}원]")

                                with col3:
                                    st.markdown(f"**수익률:** :{color}[{profit_rate:+.2f}%]")
                                    st.markdown(f"**매수 횟수:** {buy_count}회")

                                st.markdown("---")

                                # 개별 매수 내역
                                st.markdown("#### 📝 개별 매수 내역")
                                details = db.get_position_details_by_ticker(ticker)

                                for detail_idx, detail in enumerate(details, 1):
                                    # 개별 수익률 계산
                                    detail_profit_rate = ((detail['current_price'] - detail['buy_price']) / detail['buy_price'] * 100)
                                    detail_profit_loss = (detail['current_price'] - detail['buy_price']) * detail['quantity']

                                    if detail_profit_rate > 0:
                                        detail_color = "green"
                                    elif detail_profit_rate < 0:
                                        detail_color = "red"
                                    else:
                                        detail_color = "gray"

                                    with st.container():
                                        st.markdown(f"**매수 #{detail_idx} - {detail['buy_date']}**")

                                        dcol1, dcol2, dcol3 = st.columns(3)

                                        with dcol1:
                                            st.markdown(f"• 매수가: {detail['buy_price']:,.0f}원")
                                            st.markdown(f"• 수량: {detail['quantity']}주")
                                            st.markdown(f"• 투자금액: {detail['buy_price'] * detail['quantity']:,.0f}원")

                                        with dcol2:
                                            st.markdown(f"• 현재가: {detail['current_price']:,.0f}원")
                                            st.markdown(f"• 평가금액: {detail['current_price'] * detail['quantity']:,.0f}원")
                                            st.markdown(f"• 손익: :{detail_color}[{detail_profit_loss:+,.0f}원]")

                                        with dcol3:
                                            st.markdown(f"• 수익률: :{detail_color}[{detail_profit_rate:+.2f}%]")
                                            st.markdown(f"• RSI: {detail.get('rsi', 0):.2f}" if detail.get('rsi') else "• RSI: N/A")
                                            st.markdown(f"• MACD: {detail.get('macd', 0):.2f}" if detail.get('macd') else "• MACD: N/A")

                                        # 기술적 지표 추가 정보
                                        st.markdown(f"📈 **당시 시장 지표** - 종목 ADR: {detail.get('adr', 0):.2f}, "
                                                   f"코스피 ADR: {detail.get('market_kospi_adr', 0):.2f}, "
                                                   f"코스닥 ADR: {detail.get('market_kosdaq_adr', 0):.2f}")

                                        # 투자 근거
                                        if detail.get('scenario'):
                                            try:
                                                scenario = json.loads(detail['scenario']) if isinstance(detail['scenario'], str) else detail['scenario']
                                                if scenario.get('rationale') and scenario.get('rationale') != "미입력":
                                                    st.markdown(f"💡 **투자 근거:** {scenario.get('rationale')}")
                                            except:
                                                pass

                                        if detail_idx < len(details):
                                            st.markdown("---")

            except Exception as e:
                st.error(f"보유 종목 조회 중 오류가 발생했습니다: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    def render_sell_records(self):
        """매도 기록 화면 (분할 뷰: 보유종목 목록 + 매도 폼)"""
        global stock, TradingJournalDB

        self.add_app_header()

        st.markdown("## 📉 매도 기록")
        st.markdown("보유 중인 종목을 선택하여 매도를 기록할 수 있습니다.")

        if TradingJournalDB is None:
            st.error("TradingJournalDB 모듈을 불러올 수 없습니다.")
            return

        if stock is None:
            st.warning("pykrx 라이브러리가 설치되지 않았습니다. `pip install pykrx`를 실행해주세요.")

        try:
            # 데이터베이스 경로를 project_root로 명시
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")

            # 탭 진입 시 자동으로 1회 업데이트 (pykrx 사용 가능한 경우에만)
            if 'sell_records_auto_updated' not in st.session_state and stock is not None:
                with st.spinner("💡 현재가를 자동으로 업데이트하는 중..."):
                    with TradingJournalDB(db_path) as db:
                        positions = db.get_open_positions()
                        if positions:  # 보유 종목이 있을 때만
                            tickers = list(set([p['ticker'] for p in positions]))
                            updated_count = 0
                            for ticker in tickers:
                                try:
                                    end_date = datetime.now().strftime("%Y%m%d")
                                    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
                                    df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
                                    if not df.empty:
                                        current_price = df['종가'].iloc[-1]
                                        db.update_current_price(ticker, float(current_price))
                                        updated_count += 1
                                except:
                                    continue
                            if updated_count > 0:
                                st.info(f"✅ {updated_count}개 종목의 현재가가 자동 업데이트되었습니다!")
                st.session_state.sell_records_auto_updated = True

            # 화면 분할: 왼쪽(보유종목), 오른쪽(매도 폼)
            col_left, col_right = st.columns([1, 1])

            # 왼쪽: 보유 종목 목록
            with col_left:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("### 💼 보유 종목 목록")
                with col2:
                    refresh_sell = st.button("🔄 현재가", key="refresh_sell", use_container_width=True)

                # 현재가 업데이트 처리
                if refresh_sell and stock is not None:
                    with st.spinner("현재가를 업데이트하고 있습니다..."):
                        with TradingJournalDB(db_path) as db:
                            positions_temp = db.get_open_positions()
                            tickers_temp = list(set([p['ticker'] for p in positions_temp]))

                            updated_count = 0
                            for ticker in tickers_temp:
                                try:
                                    end_date = datetime.now().strftime("%Y%m%d")
                                    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

                                    df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
                                    if not df.empty:
                                        current_price = df['종가'].iloc[-1]
                                        db.update_current_price(ticker, float(current_price))
                                        updated_count += 1
                                except:
                                    continue

                            st.success(f"✅ {updated_count}개 종목 업데이트!")

                with TradingJournalDB(db_path) as db:
                    positions = db.get_open_positions()

                    if not positions:
                        st.info("📭 현재 보유 중인 종목이 없습니다.")
                    else:
                        st.markdown(f"### 💼 보유 종목 ({len(positions)}건)")
                        st.markdown("매도할 종목을 선택하세요")

                        # session_state에 선택된 포지션 저장
                        if 'selected_position_id' not in st.session_state:
                            st.session_state.selected_position_id = None

                        # 각 포지션을 카드 형식의 버튼으로 표시
                        for idx, pos in enumerate(positions):
                            profit_rate = pos['profit_rate']
                            is_selected = st.session_state.selected_position_id == pos.get('id')

                            # 수익률에 따른 색상 결정
                            if profit_rate > 0:
                                profit_color = "🟢"
                                profit_emoji = "📈"
                            elif profit_rate < 0:
                                profit_color = "🔴"
                                profit_emoji = "📉"
                            else:
                                profit_color = "⚪"
                                profit_emoji = "➖"

                            # 선택된 포지션은 primary 버튼으로 표시
                            button_type = "primary" if is_selected else "secondary"

                            # 버튼 라벨 구성 (더 큰 폰트와 명확한 정보)
                            button_label = f"{profit_emoji} **{pos['company_name']}** ({pos['ticker']})"

                            if st.button(
                                button_label,
                                key=f"position_btn_{idx}_{pos.get('id')}",
                                type=button_type,
                                use_container_width=True
                            ):
                                st.session_state.selected_position_id = pos.get('id')

                            # 선택된 포지션의 경우 상세 정보 표시
                            if is_selected:
                                with st.container():
                                    st.markdown(f"""
                                    <div style='padding: 10px; background-color: rgba(128, 128, 128, 0.1); border-radius: 5px; margin-bottom: 10px;'>
                                        <p style='font-size: 14px; margin: 5px 0;'>💰 <strong>매수가:</strong> {pos['buy_price']:,.0f}원 | <strong>현재가:</strong> {pos['current_price']:,.0f}원</p>
                                        <p style='font-size: 14px; margin: 5px 0;'>📊 <strong>보유 수량:</strong> {pos['quantity']}주 | <strong>매수일:</strong> {pos['buy_date']}</p>
                                        <p style='font-size: 16px; margin: 5px 0;'>{profit_color} <strong>수익률:</strong> {profit_rate:+.2f}%</p>
                                    </div>
                                    """, unsafe_allow_html=True)

                        # 선택된 포지션 정보를 변수로 저장
                        selected_position = None
                        if st.session_state.selected_position_id is not None:
                            for pos in positions:
                                if pos.get('id') == st.session_state.selected_position_id:
                                    selected_position = pos
                                    break

            # 오른쪽: 매도 폼
            with col_right:
                st.markdown("### 📝 매도 기록 입력")

                if not positions:
                    st.info("매도할 보유 종목이 없습니다.")
                elif selected_position:
                    # 현재가 조회 (최신 가격)
                    with st.spinner("현재가를 조회하고 있습니다..."):
                        if stock is not None:
                            try:
                                end_date = datetime.now().strftime("%Y%m%d")
                                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

                                df = stock.get_market_ohlcv_by_date(start_date, end_date, selected_position['ticker'])
                                if not df.empty:
                                    latest_price = df['종가'].iloc[-1]
                                    st.info(f"💹 최신 현재가: {latest_price:,.0f}원")
                                else:
                                    latest_price = selected_position['current_price']
                            except:
                                latest_price = selected_position['current_price']
                        else:
                            latest_price = selected_position['current_price']

                    # 매도 폼
                    with st.form("sell_record_form"):
                        st.markdown("#### 💰 매도 정보")

                        col1, col2 = st.columns(2)
                        with col1:
                            sell_price = st.number_input(
                                "💵 매도가 (원) *",
                                min_value=1,
                                value=int(latest_price),
                                step=100,
                                help="실제 매도한 가격을 입력해주세요"
                            )
                        with col2:
                            sell_quantity = st.number_input(
                                "📦 매도 수량 *",
                                min_value=1,
                                max_value=selected_position['quantity'],
                                value=selected_position['quantity'],
                                step=1,
                                help=f"최대 {selected_position['quantity']}주까지 매도 가능"
                            )

                        sell_date = st.date_input(
                            "📅 매도일",
                            value=datetime.now(),
                            max_value=datetime.now(),
                            help="매도한 날짜를 선택하세요"
                        )

                        # 매도 사유
                        sell_reason = st.text_area(
                            "매도 사유 (선택사항)",
                            placeholder="매도 이유를 간단히 작성해주세요...",
                            height=100
                        )

                        # 예상 수익 계산
                        buy_price = selected_position['buy_price']
                        profit_per_share = sell_price - buy_price
                        total_profit = profit_per_share * sell_quantity
                        profit_rate = (profit_per_share / buy_price) * 100

                        st.markdown("---")
                        st.markdown("#### 📊 예상 수익 분석")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("주당 손익", f"{profit_per_share:+,.0f}원")
                        with col2:
                            st.metric("총 손익", f"{total_profit:+,.0f}원")
                        with col3:
                            st.metric("수익률", f"{profit_rate:+.2f}%")

                        st.markdown("---")

                        # 제출 버튼
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            submitted = st.form_submit_button("💾 매도 기록 저장", use_container_width=True, type="primary")

                        if submitted:
                            if sell_price <= 0:
                                st.error("❌ 매도가를 입력해주세요.")
                            elif sell_quantity <= 0:
                                st.error("❌ 매도 수량을 입력해주세요.")
                            elif sell_quantity > selected_position['quantity']:
                                st.error(f"❌ 매도 수량은 최대 {selected_position['quantity']}주까지 가능합니다.")
                            else:
                                # position_id 검증
                                position_id = selected_position.get('id')
                                if position_id is None:
                                    st.error("❌ 포지션 ID를 찾을 수 없습니다.")
                                    st.error("💡 **해결 방법**: 데이터베이스 스키마 문제일 수 있습니다.")
                                    st.code(f"""
# 다음 파일을 삭제하고 앱을 다시 시작하세요:
{db_path}

# 또는 터미널에서:
rm {db_path}
streamlit run examples/streamlit/app_modern.py
                                    """)
                                else:
                                    # 매도 처리
                                    sell_date_str = sell_date.strftime("%Y-%m-%d")

                                    with TradingJournalDB(db_path) as db:
                                        success = db.sell_position(
                                            position_id=position_id,
                                            sell_quantity=sell_quantity,
                                            sell_price=sell_price,
                                            sell_date=sell_date_str
                                        )

                                        if success:
                                            if sell_quantity == selected_position['quantity']:
                                                st.success(f"✅ {selected_position['company_name']} {sell_quantity}주 전체 매도가 완료되었습니다!")
                                            else:
                                                remaining = selected_position['quantity'] - sell_quantity
                                                st.success(f"✅ {selected_position['company_name']} {sell_quantity}주 부분 매도가 완료되었습니다! (잔여: {remaining}주)")

                                            st.info(f"💰 실현 손익: {total_profit:+,.0f}원 ({profit_rate:+.2f}%)")
                                            st.rerun()
                                        else:
                                            st.error("❌ 매도 처리 중 오류가 발생했습니다.")
                                            st.warning("💡 로그를 확인하거나 데이터베이스를 다시 생성해보세요.")

                else:
                    st.info("왼쪽에서 매도할 종목을 선택해주세요.")

            # 구분선
            st.markdown("---")
            st.markdown("## 📜 과거 매도 내역")

            # 과거 매도 기록 조회 (stock_holdings에서 is_sold=1인 것들)
            with TradingJournalDB(db_path) as db:
                # is_sold=1인 레코드 조회
                db.cursor.execute("""
                    SELECT
                        id, ticker, company_name, buy_price, buy_date, quantity,
                        sell_price, sell_date, rsi, macd, adr,
                        market_kospi_adr, market_kosdaq_adr, scenario
                    FROM stock_holdings
                    WHERE is_sold = 1
                    ORDER BY sell_date DESC
                """)

                sold_records = db.cursor.fetchall()

                if not sold_records:
                    st.info("📭 매도 기록이 없습니다.")
                else:
                    # 통계 정보
                    total_trades = len(sold_records)
                    profitable = sum(1 for r in sold_records if r['sell_price'] > r['buy_price'])
                    losing = total_trades - profitable
                    win_rate = (profitable / total_trades * 100) if total_trades > 0 else 0
                    avg_profit_rate = sum(((r['sell_price'] - r['buy_price']) / r['buy_price'] * 100) for r in sold_records) / total_trades if total_trades > 0 else 0

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("총 거래", f"{total_trades}건")
                    with col2:
                        st.metric("수익 거래", f"{profitable}건", delta=f"{win_rate:.1f}% 승률")
                    with col3:
                        st.metric("손실 거래", f"{losing}건")
                    with col4:
                        st.metric("평균 수익률", f"{avg_profit_rate:+.2f}%")

                    st.markdown("---")

                    # 정렬 옵션
                    st.markdown("### 💰 매도 내역")
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        sort_option = st.selectbox(
                            "정렬 기준",
                            ["매도일 (최신순)", "매도일 (오래된순)", "수익률 (높은순)", "수익률 (낮은순)"],
                            index=0
                        )

                    # 정렬 적용
                    sold_list = [dict(r) for r in sold_records]
                    if sort_option == "매도일 (최신순)":
                        sold_list.sort(key=lambda x: x['sell_date'], reverse=True)
                    elif sort_option == "매도일 (오래된순)":
                        sold_list.sort(key=lambda x: x['sell_date'])
                    elif sort_option == "수익률 (높은순)":
                        sold_list.sort(key=lambda x: ((x['sell_price'] - x['buy_price']) / x['buy_price'] * 100), reverse=True)
                    elif sort_option == "수익률 (낮은순)":
                        sold_list.sort(key=lambda x: ((x['sell_price'] - x['buy_price']) / x['buy_price'] * 100))

                    st.markdown(f"**총 {len(sold_list)}건의 거래 내역**")

                    for idx, trade in enumerate(sold_list, 1):
                        profit_rate = ((trade['sell_price'] - trade['buy_price']) / trade['buy_price'] * 100)
                        net_profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']

                        if profit_rate > 0:
                            color = "green"
                            emoji = "✅"
                            result = "수익"
                        else:
                            color = "red"
                            emoji = "❌"
                            result = "손실"

                        with st.expander(
                            f"{emoji} {trade['company_name']} ({trade['ticker']}) - {result}: {profit_rate:+.2f}% | 순수익: {net_profit:+,.0f}원",
                            expanded=(idx <= 5)
                        ):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.markdown("#### 💰 거래 정보")
                                st.markdown(f"**매수가:** {trade['buy_price']:,.0f}원")
                                st.markdown(f"**매도가:** {trade['sell_price']:,.0f}원")
                                st.markdown(f"**수량:** {trade['quantity']}주")
                                st.markdown(f"**투자금액:** {trade['buy_price'] * trade['quantity']:,.0f}원")

                            with col2:
                                st.markdown("#### 📊 수익 분석")
                                st.markdown(f"**매수일:** {trade['buy_date']}")
                                st.markdown(f"**매도일:** {trade['sell_date']}")
                                st.markdown(f"**수익률:** :{color}[{profit_rate:+.2f}%]")
                                st.markdown(f"**순수익:** :{color}[{net_profit:+,.0f}원]")

                            with col3:
                                st.markdown("#### 📈 매수 당시 지표")
                                st.markdown(f"**RSI:** {trade.get('rsi', 0):.2f}" if trade.get('rsi') else "**RSI:** N/A")
                                st.markdown(f"**MACD:** {trade.get('macd', 0):.2f}" if trade.get('macd') else "**MACD:** N/A")
                                st.markdown(f"**종목 ADR:** {trade.get('adr', 0):.2f}" if trade.get('adr') else "**종목 ADR:** N/A")

                            # 투자 근거
                            if trade.get('scenario'):
                                try:
                                    scenario = json.loads(trade['scenario']) if isinstance(trade['scenario'], str) else trade['scenario']
                                    if scenario.get('rationale') and scenario.get('rationale') != "미입력":
                                        st.markdown("---")
                                        st.markdown(f"💡 **투자 근거:** {scenario.get('rationale')}")
                                except:
                                    pass

                    # 데이터프레임으로도 표시
                    st.markdown("### 📋 거래 내역 테이블")
                    df_data = []
                    for trade in sold_list:
                        profit_rate = ((trade['sell_price'] - trade['buy_price']) / trade['buy_price'] * 100)
                        net_profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']

                        df_data.append({
                            '종목명': trade['company_name'],
                            '종목코드': trade['ticker'],
                            '매수가': f"{trade['buy_price']:,.0f}원",
                            '매도가': f"{trade['sell_price']:,.0f}원",
                            '수량': f"{trade['quantity']}주",
                            '수익률': f"{profit_rate:+.2f}%",
                            '순수익': f"{net_profit:+,.0f}원",
                            '매수일': trade['buy_date'].split()[0] if ' ' in trade['buy_date'] else trade['buy_date'],
                            '매도일': trade['sell_date'].split()[0] if ' ' in trade['sell_date'] else trade['sell_date']
                        })

                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"매도 기록 조회 중 오류가 발생했습니다: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    def render_transaction_history(self):
        """전체 거래 히스토리 화면 (보유 + 매도)"""
        self.add_app_header()

        st.markdown("## 📜 전체 거래 히스토리")
        st.markdown("모든 매수 기록을 시간순으로 확인할 수 있습니다. (보유 중인 종목 + 매도 완료 종목)")

        if TradingJournalDB is None:
            st.error("TradingJournalDB 모듈을 불러올 수 없습니다.")
            return

        try:
            # 데이터베이스 경로를 project_root로 명시
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")
            with TradingJournalDB(db_path) as db:
                transactions = db.get_all_transactions()

                if not transactions:
                    st.info("📭 거래 내역이 없습니다.")
                    return

                # 전체 통계
                holding_count = sum(1 for t in transactions if t['status'] == 'HOLDING')
                sold_count = sum(1 for t in transactions if t['status'] == 'SOLD')

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("전체 거래", f"{len(transactions)}건")
                with col2:
                    st.metric("보유 중", f"{holding_count}건", delta="HOLDING")
                with col3:
                    st.metric("매도 완료", f"{sold_count}건", delta="SOLD")
                with col4:
                    st.metric("고유 종목 수", f"{len(set(t['ticker'] for t in transactions))}개")

                st.markdown("---")

                # 필터 및 정렬 옵션
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    status_filter = st.selectbox(
                        "상태 필터",
                        ["전체", "보유 중", "매도 완료"]
                    )
                with col2:
                    sort_option = st.selectbox(
                        "정렬 기준",
                        ["매수일 (최신순)", "매수일 (오래된순)", "종목명 (가나다순)", "종목명 (역순)"]
                    )
                with col3:
                    st.markdown("")  # 간격

                # 필터 적용
                filtered_transactions = transactions
                if status_filter == "보유 중":
                    filtered_transactions = [t for t in transactions if t['status'] == 'HOLDING']
                elif status_filter == "매도 완료":
                    filtered_transactions = [t for t in transactions if t['status'] == 'SOLD']

                # 정렬 적용
                if sort_option == "매수일 (최신순)":
                    filtered_transactions.sort(key=lambda x: x['buy_date'], reverse=True)
                elif sort_option == "매수일 (오래된순)":
                    filtered_transactions.sort(key=lambda x: x['buy_date'])
                elif sort_option == "종목명 (가나다순)":
                    filtered_transactions.sort(key=lambda x: x['company_name'])
                elif sort_option == "종목명 (역순)":
                    filtered_transactions.sort(key=lambda x: x['company_name'], reverse=True)

                st.markdown(f"**총 {len(filtered_transactions)}건의 거래 내역**")
                st.markdown("---")

                # 거래 내역 표시
                for idx, trans in enumerate(filtered_transactions, 1):
                    status = trans['status']
                    current_price = trans['current_price']

                    if status == 'HOLDING':
                        # 보유 중인 종목
                        profit_rate = ((current_price - trans['buy_price']) / trans['buy_price'] * 100)
                        profit_loss = (current_price - trans['buy_price']) * trans['quantity']

                        if profit_rate > 0:
                            color = "green"
                            emoji = "🟢"
                        elif profit_rate < 0:
                            color = "red"
                            emoji = "🔴"
                        else:
                            color = "gray"
                            emoji = "⚪"

                        status_badge = "🔵 보유 중"
                    else:
                        # 매도 완료 종목
                        profit_rate = ((current_price - trans['buy_price']) / trans['buy_price'] * 100)
                        profit_loss = (current_price - trans['buy_price']) * trans['quantity']

                        if profit_rate > 0:
                            color = "green"
                            emoji = "✅"
                        else:
                            color = "red"
                            emoji = "❌"

                        status_badge = "⚫ 매도 완료"

                    with st.expander(
                        f"{emoji} {trans['company_name']} ({trans['ticker']}) | {status_badge} | 수익률: {profit_rate:+.2f}% | 순수익: {profit_loss:+,.0f}원",
                        expanded=(idx <= 5)
                    ):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("#### 💰 거래 정보")
                            st.markdown(f"**매수가:** {trans['buy_price']:,.0f}원")
                            st.markdown(f"**매수 수량:** {trans['quantity']}주")
                            st.markdown(f"**투자금액:** {trans['buy_price'] * trans['quantity']:,.0f}원")
                            st.markdown(f"**매수일:** {trans['buy_date']}")

                            if status == 'HOLDING':
                                st.markdown(f"**현재가:** {current_price:,.0f}원")
                            else:
                                st.markdown(f"**매도가:** {current_price:,.0f}원")

                        with col2:
                            st.markdown("#### 📊 수익 분석")
                            st.markdown(f"**평가/매도 금액:** {current_price * trans['quantity']:,.0f}원")
                            st.markdown(f"**평가손익:** :{color}[{profit_loss:+,.0f}원]")
                            st.markdown(f"**수익률:** :{color}[{profit_rate:+.2f}%]")
                            st.markdown(f"**상태:** {status_badge}")

                        with col3:
                            st.markdown("#### 📈 기술적 지표 (매수 당시)")
                            st.markdown(f"**RSI:** {trans.get('rsi', 0):.2f}" if trans.get('rsi') else "**RSI:** N/A")
                            st.markdown(f"**MACD:** {trans.get('macd', 0):.2f}" if trans.get('macd') else "**MACD:** N/A")
                            st.markdown(f"**종목 ADR:** {trans.get('adr', 0):.2f}" if trans.get('adr') else "**종목 ADR:** N/A")
                            st.markdown(f"**코스피 ADR:** {trans.get('market_kospi_adr', 0):.2f}" if trans.get('market_kospi_adr') else "**코스피 ADR:** N/A")
                            st.markdown(f"**코스닥 ADR:** {trans.get('market_kosdaq_adr', 0):.2f}" if trans.get('market_kosdaq_adr') else "**코스닥 ADR:** N/A")

                        # 투자 근거
                        if trans.get('scenario'):
                            try:
                                scenario = json.loads(trans['scenario']) if isinstance(trans['scenario'], str) else trans['scenario']
                                if scenario.get('rationale') and scenario.get('rationale') != "미입력":
                                    st.markdown("---")
                                    st.markdown(f"💡 **투자 근거:** {scenario.get('rationale')}")
                            except:
                                pass

                # 데이터프레임 표시
                st.markdown("### 📋 거래 내역 테이블")
                df_data = []
                for trans in filtered_transactions:
                    status = trans['status']
                    current_price = trans['current_price']
                    profit_rate = ((current_price - trans['buy_price']) / trans['buy_price'] * 100)
                    net_profit = (current_price - trans['buy_price']) * trans['quantity']

                    df_data.append({
                        '상태': '🔵 보유' if status == 'HOLDING' else '⚫ 매도',
                        '종목명': trans['company_name'],
                        '종목코드': trans['ticker'],
                        '매수가': f"{trans['buy_price']:,.0f}원",
                        '현재/매도가': f"{current_price:,.0f}원",
                        '수량': f"{trans['quantity']}주",
                        '수익률': f"{profit_rate:+.2f}%",
                        '순수익': f"{net_profit:+,.0f}원",
                        '매수일': trans['buy_date'].split()[0] if ' ' in trans['buy_date'] else trans['buy_date']
                    })

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"거래 히스토리 조회 중 오류가 발생했습니다: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    def calculate_statistics(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        기간별 통계 계산

        Args:
            year: 연도 (None이면 전체)
            month: 월 (None이면 전체 또는 연도별)

        Returns:
            통계 딕셔너리
        """
        try:
            if not TradingJournalDB:
                return {}

            db = TradingJournalDB()

            # 매도된 종목만 조회 (is_sold = 1)
            query = """
                SELECT
                    id, ticker, company_name, buy_price, buy_date,
                    sell_price, sell_date, quantity
                FROM stock_holdings
                WHERE is_sold = 1
            """
            params = []

            if year and month:
                # 특정 월의 매도 기록만
                query += " AND strftime('%Y', sell_date) = ? AND strftime('%m', sell_date) = ?"
                params = [str(year), f"{month:02d}"]
            elif year:
                # 특정 연도의 매도 기록만
                query += " AND strftime('%Y', sell_date) = ?"
                params = [str(year)]

            db.cursor.execute(query, params)
            trades = db.cursor.fetchall()

            if not trades:
                return {
                    'total_profit': 0,
                    'profit_amount': 0,
                    'loss_amount': 0,
                    'profit_rate': 0.0,
                    'buy_count': 0,
                    'sell_count': 0,
                    'profit_count': 0,
                    'loss_count': 0,
                    'total_trades': 0
                }

            # 통계 계산
            total_profit = 0
            profit_amount = 0
            loss_amount = 0
            profit_count = 0
            loss_count = 0
            total_investment = 0

            # 매수 건수 계산 (해당 기간에 매수된 건수)
            buy_query = "SELECT COUNT(*) FROM stock_holdings WHERE 1=1"
            buy_params = []
            if year and month:
                buy_query += " AND strftime('%Y', buy_date) = ? AND strftime('%m', buy_date) = ?"
                buy_params = [str(year), f"{month:02d}"]
            elif year:
                buy_query += " AND strftime('%Y', buy_date) = ?"
                buy_params = [str(year)]

            db.cursor.execute(buy_query, buy_params)
            buy_count = db.cursor.fetchone()[0]

            for trade in trades:
                buy_price = trade['buy_price']
                sell_price = trade['sell_price']
                quantity = trade['quantity']

                # 손익 계산
                profit = (sell_price - buy_price) * quantity
                investment = buy_price * quantity

                total_profit += profit
                total_investment += investment

                if profit > 0:
                    profit_amount += profit
                    profit_count += 1
                else:
                    loss_amount += abs(profit)
                    loss_count += 1

            # 수익률 계산
            profit_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0.0

            db.close()

            return {
                'total_profit': total_profit,
                'profit_amount': profit_amount,
                'loss_amount': loss_amount,
                'profit_rate': profit_rate,
                'buy_count': buy_count,
                'sell_count': len(trades),
                'profit_count': profit_count,
                'loss_count': loss_count,
                'total_trades': len(trades)
            }

        except Exception as e:
            st.error(f"통계 계산 중 오류 발생: {str(e)}")
            return {}

    def calculate_daily_statistics(self, year: int, month: int) -> Dict[int, Dict[str, Any]]:
        """
        일별 통계 계산

        Args:
            year: 연도
            month: 월

        Returns:
            {일: {profit, profit_rate, trade_count, stocks}} 형식의 딕셔너리
        """
        try:
            if not TradingJournalDB:
                return {}

            db = TradingJournalDB()

            # 해당 월의 매도 기록 조회
            query = """
                SELECT
                    strftime('%d', sell_date) as day,
                    ticker, company_name, buy_price, sell_price, quantity
                FROM stock_holdings
                WHERE is_sold = 1
                AND strftime('%Y', sell_date) = ?
                AND strftime('%m', sell_date) = ?
            """

            db.cursor.execute(query, [str(year), f"{month:02d}"])
            trades = db.cursor.fetchall()

            daily_stats = {}

            for trade in trades:
                day = int(trade['day'])
                buy_price = trade['buy_price']
                sell_price = trade['sell_price']
                quantity = trade['quantity']
                company_name = trade['company_name']

                profit = (sell_price - buy_price) * quantity
                profit_rate = ((sell_price - buy_price) / buy_price * 100) if buy_price > 0 else 0.0

                if day not in daily_stats:
                    daily_stats[day] = {
                        'profit': 0,
                        'investment': 0,
                        'trade_count': 0,
                        'stocks': []
                    }

                daily_stats[day]['profit'] += profit
                daily_stats[day]['investment'] += buy_price * quantity
                daily_stats[day]['trade_count'] += 1
                daily_stats[day]['stocks'].append(company_name)

            # 각 일별 수익률 계산
            for day in daily_stats:
                investment = daily_stats[day]['investment']
                profit = daily_stats[day]['profit']
                daily_stats[day]['profit_rate'] = (profit / investment * 100) if investment > 0 else 0.0

            db.close()

            return daily_stats

        except Exception as e:
            st.error(f"일별 통계 계산 중 오류 발생: {str(e)}")
            return {}

    def get_monthly_trades(self, year: int = None, month: int = None) -> Dict[str, list]:
        """
        월별 매수/매도 종목 리스트 조회

        Args:
            year: 연도
            month: 월

        Returns:
            {'buys': [...], 'sells': [...]} 딕셔너리
        """
        try:
            if not TradingJournalDB:
                return {'buys': [], 'sells': []}

            db = TradingJournalDB()

            # 매수 종목 조회
            buy_query = """
                SELECT
                    ticker, company_name, buy_price, buy_date, quantity,
                    is_sold, sell_price, sell_date
                FROM stock_holdings
                WHERE 1=1
            """
            buy_params = []

            if year and month:
                buy_query += " AND strftime('%Y', buy_date) = ? AND strftime('%m', buy_date) = ?"
                buy_params = [str(year), f"{month:02d}"]
            elif year:
                buy_query += " AND strftime('%Y', buy_date) = ?"
                buy_params = [str(year)]

            buy_query += " ORDER BY buy_date DESC"

            db.cursor.execute(buy_query, buy_params)
            buys = [dict(row) for row in db.cursor.fetchall()]

            # 매도 종목 조회
            sell_query = """
                SELECT
                    ticker, company_name, buy_price, buy_date, sell_price, sell_date, quantity
                FROM stock_holdings
                WHERE is_sold = 1
            """
            sell_params = []

            if year and month:
                sell_query += " AND strftime('%Y', sell_date) = ? AND strftime('%m', sell_date) = ?"
                sell_params = [str(year), f"{month:02d}"]
            elif year:
                sell_query += " AND strftime('%Y', sell_date) = ?"
                sell_params = [str(year)]

            sell_query += " ORDER BY sell_date DESC"

            db.cursor.execute(sell_query, sell_params)
            sells = [dict(row) for row in db.cursor.fetchall()]

            db.close()

            return {'buys': buys, 'sells': sells}

        except Exception as e:
            st.error(f"월별 거래 조회 중 오류 발생: {str(e)}")
            return {'buys': [], 'sells': []}

    def render_calendar(self, year: int, month: int, daily_stats: Dict[int, Dict[str, Any]]):
        """
        달력 UI 렌더링

        Args:
            year: 연도
            month: 월
            daily_stats: 일별 통계 데이터
        """
        import calendar

        # 달력 생성
        cal = calendar.monthcalendar(year, month)
        weekdays = ['월', '화', '수', '목', '금', '토', '일']

        # CSS 스타일
        calendar_css = """
        <style>
        .calendar-container {
            width: 100%;
            margin: 20px 0;
        }
        .calendar-header {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            margin-bottom: 10px;
        }
        .calendar-header-cell {
            background: var(--gradient-primary);
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            border-radius: 8px;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
        }
        .calendar-cell {
            min-height: 100px;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--border-light);
            background: var(--bg-elevated);
            position: relative;
            transition: all 0.3s ease;
        }
        .calendar-cell:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .calendar-cell-empty {
            background: transparent;
            border: none;
        }
        .calendar-day {
            font-weight: 600;
            font-size: 16px;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        .calendar-profit-positive {
            color: #EF4444;
            font-weight: 700;
            font-size: 14px;
            margin-top: 5px;
        }
        .calendar-profit-negative {
            color: #3B82F6;
            font-weight: 700;
            font-size: 14px;
            margin-top: 5px;
        }
        .calendar-rate {
            font-size: 12px;
            color: var(--text-secondary);
        }
        .calendar-trades {
            font-size: 11px;
            color: var(--text-tertiary);
            margin-top: 5px;
        }
        </style>
        """

        st.markdown(calendar_css, unsafe_allow_html=True)

        # 달력 헤더
        header_html = '<div class="calendar-container"><div class="calendar-header">'
        for weekday in weekdays:
            header_html += f'<div class="calendar-header-cell">{weekday}</div>'
        header_html += '</div>'

        # 달력 그리드
        grid_html = '<div class="calendar-grid">'

        for week in cal:
            for day in week:
                if day == 0:
                    grid_html += '<div class="calendar-cell calendar-cell-empty"></div>'
                else:
                    stats = daily_stats.get(day, None)

                    if stats:
                        profit = stats['profit']
                        profit_rate = stats['profit_rate']
                        trade_count = stats['trade_count']
                        stocks = stats.get('stocks', [])

                        profit_class = 'calendar-profit-positive' if profit >= 0 else 'calendar-profit-negative'
                        profit_sign = '+' if profit >= 0 else ''

                        # 종목명 표시 (최대 2개)
                        stocks_text = ', '.join(stocks[:2])
                        if len(stocks) > 2:
                            stocks_text += f' 외 {len(stocks)-2}'

                        grid_html += f'<div class="calendar-cell"><div class="calendar-day">{day}</div><div class="calendar-stocks" style="font-size:11px;color:var(--text-tertiary);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{stocks_text}</div><div class="{profit_class}">{profit_sign}{profit:,.0f}원<div class="calendar-rate">({profit_sign}{profit_rate:.2f}%)</div></div><div class="calendar-trades">{trade_count}건</div></div>'
                    else:
                        grid_html += f'<div class="calendar-cell"><div class="calendar-day">{day}</div></div>'

        grid_html += '</div></div>'

        st.markdown(header_html + grid_html, unsafe_allow_html=True)

    def render_statistics(self):
        """통계 탭 렌더링"""
        try:
            # 헤더
            st.markdown("## 📊 투자 통계")

            if not TradingJournalDB:
                st.warning("데이터베이스 연결이 필요합니다.")
                return

            # 세션 상태 초기화
            if 'stats_year' not in st.session_state:
                st.session_state.stats_year = datetime.now().year
            if 'stats_month' not in st.session_state:
                st.session_state.stats_month = datetime.now().month
            if 'stats_view' not in st.session_state:
                st.session_state.stats_view = 'monthly'  # monthly, yearly, all

            # 기간 선택
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

            with col1:
                if st.button("◀", key="prev_period"):
                    if st.session_state.stats_view == 'monthly':
                        if st.session_state.stats_month == 1:
                            st.session_state.stats_month = 12
                            st.session_state.stats_year -= 1
                        else:
                            st.session_state.stats_month -= 1
                    elif st.session_state.stats_view == 'yearly':
                        st.session_state.stats_year -= 1

            with col3:
                view_options = {
                    'monthly': '월별',
                    'yearly': '연도별',
                    'all': '전체'
                }
                selected_view = st.selectbox(
                    "기간 선택",
                    options=list(view_options.keys()),
                    format_func=lambda x: view_options[x],
                    index=list(view_options.keys()).index(st.session_state.stats_view),
                    key="view_selector"
                )
                st.session_state.stats_view = selected_view

            with col5:
                if st.button("▶", key="next_period"):
                    if st.session_state.stats_view == 'monthly':
                        if st.session_state.stats_month == 12:
                            st.session_state.stats_month = 1
                            st.session_state.stats_year += 1
                        else:
                            st.session_state.stats_month += 1
                    elif st.session_state.stats_view == 'yearly':
                        st.session_state.stats_year += 1

            # 현재 기간 표시
            if st.session_state.stats_view == 'monthly':
                period_text = f"{st.session_state.stats_year}년 {st.session_state.stats_month}월"
            elif st.session_state.stats_view == 'yearly':
                period_text = f"{st.session_state.stats_year}년"
            else:
                period_text = "전체 기간"

            st.markdown(f"### 📅 {period_text}")

            # 통계 계산
            if st.session_state.stats_view == 'monthly':
                stats = self.calculate_statistics(st.session_state.stats_year, st.session_state.stats_month)
            elif st.session_state.stats_view == 'yearly':
                stats = self.calculate_statistics(st.session_state.stats_year)
            else:
                stats = self.calculate_statistics()

            if not stats:
                st.info("통계 데이터가 없습니다.")
                return

            # 통계 카드 표시
            st.markdown("#### 📈 기간 요약")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                profit_color = "🔴" if stats['total_profit'] >= 0 else "🔵"
                st.metric(
                    label="순수익",
                    value=f"{stats['total_profit']:,.0f}원",
                    delta=f"{stats['profit_rate']:+.2f}%"
                )

            with col2:
                st.metric(
                    label="수익금",
                    value=f"{stats['profit_amount']:,.0f}원",
                    delta=f"{stats['profit_count']}건"
                )

            with col3:
                st.metric(
                    label="손실금",
                    value=f"{stats['loss_amount']:,.0f}원",
                    delta=f"{stats['loss_count']}건"
                )

            with col4:
                st.metric(
                    label="총 거래",
                    value=f"{stats['total_trades']}건",
                    delta=f"매수 {stats['buy_count']}건"
                )

            # 승률 표시
            col1, col2 = st.columns(2)
            with col1:
                win_rate = (stats['profit_count'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
                st.metric(label="승률", value=f"{win_rate:.1f}%", delta=f"{stats['profit_count']}/{stats['total_trades']}")
            with col2:
                avg_profit = stats['total_profit'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
                st.metric(label="평균 손익", value=f"{avg_profit:,.0f}원", delta="거래당")

            st.markdown("---")

            # 거래 종목 리스트
            st.markdown("### 📋 보유 및 거래 현황")

            if st.session_state.stats_view == 'monthly':
                trades = self.get_monthly_trades(st.session_state.stats_year, st.session_state.stats_month)
            elif st.session_state.stats_view == 'yearly':
                trades = self.get_monthly_trades(st.session_state.stats_year)
            else:
                trades = self.get_monthly_trades()

            # 보유중/매도완료 구분
            holding = [t for t in trades['buys'] if t['is_sold'] == 0]
            sold_buys = [t for t in trades['buys'] if t['is_sold'] == 1]

            # 탭으로 보유중/매도완료 구분
            tab1, tab2 = st.tabs([f"🟢 보유중 ({len(holding)})", f"✅ 매도완료 ({len(trades['sells'])})"])

            with tab1:
                st.markdown("#### 현재 보유중인 종목")
                if holding:
                    for trade in holding:
                        # 현재가 대비 수익률 계산 (임시로 매수가 사용)
                        current_price = trade.get('current_price', trade['buy_price'])
                        unrealized_profit = (current_price - trade['buy_price']) * trade['quantity']
                        unrealized_rate = ((current_price - trade['buy_price']) / trade['buy_price'] * 100) if trade['buy_price'] > 0 else 0

                        profit_emoji = "🔴" if unrealized_profit >= 0 else "🔵"
                        profit_sign = "+" if unrealized_profit >= 0 else ""

                        with st.expander(f"{profit_emoji} **{trade['company_name']}** ({trade['ticker']}) - {trade['quantity']}주 | 평가손익 {profit_sign}{unrealized_rate:.2f}%"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**매수 정보**")
                                st.markdown(f"- 매수가: {trade['buy_price']:,.0f}원")
                                st.markdown(f"- 매수일: {trade['buy_date'][:10] if len(trade['buy_date']) > 10 else trade['buy_date']}")
                                st.markdown(f"- 매수금액: {trade['buy_price'] * trade['quantity']:,.0f}원")
                            with col2:
                                st.markdown("**현재 상태**")
                                st.markdown(f"- 수량: {trade['quantity']}주")
                                st.markdown(f"- 현재가: {current_price:,.0f}원")
                                st.markdown(f"- 평가금액: {current_price * trade['quantity']:,.0f}원")
                            with col3:
                                st.markdown("**평가손익**")
                                st.markdown(f"- 손익: {profit_sign}{unrealized_profit:,.0f}원")
                                st.markdown(f"- 수익률: {profit_sign}{unrealized_rate:.2f}%")
                                st.markdown("- 상태: 🟢 보유중")
                else:
                    st.info("보유중인 종목이 없습니다.")

            with tab2:
                st.markdown("#### 매도 완료된 종목")
                if trades['sells']:
                    # 수익/손실별 구분
                    profits = []
                    losses = []

                    for trade in trades['sells']:
                        profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']
                        if profit >= 0:
                            profits.append(trade)
                        else:
                            losses.append(trade)

                    # 수익 종목
                    if profits:
                        st.markdown(f"**🔴 수익 거래 ({len(profits)}건)**")
                        for trade in profits:
                            profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']
                            profit_rate = ((trade['sell_price'] - trade['buy_price']) / trade['buy_price'] * 100) if trade['buy_price'] > 0 else 0

                            with st.expander(f"**{trade['company_name']}** ({trade['ticker']}) - +{profit_rate:.2f}% | +{profit:,.0f}원"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("**매수 정보**")
                                    st.markdown(f"- 매수가: {trade['buy_price']:,.0f}원")
                                    st.markdown(f"- 매수일: {trade['buy_date'][:10] if len(trade['buy_date']) > 10 else trade['buy_date']}")
                                    st.markdown(f"- 매수금액: {trade['buy_price'] * trade['quantity']:,.0f}원")
                                with col2:
                                    st.markdown("**매도 정보**")
                                    st.markdown(f"- 매도가: {trade['sell_price']:,.0f}원")
                                    st.markdown(f"- 매도일: {trade['sell_date'][:10] if len(trade['sell_date']) > 10 else trade['sell_date']}")
                                    st.markdown(f"- 매도금액: {trade['sell_price'] * trade['quantity']:,.0f}원")
                                with col3:
                                    st.markdown("**실현손익**")
                                    st.markdown(f"- 손익: +{profit:,.0f}원")
                                    st.markdown(f"- 수익률: +{profit_rate:.2f}%")
                                    st.markdown(f"- 수량: {trade['quantity']}주")

                    # 손실 종목
                    if losses:
                        st.markdown(f"**🔵 손실 거래 ({len(losses)}건)**")
                        for trade in losses:
                            profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']
                            profit_rate = ((trade['sell_price'] - trade['buy_price']) / trade['buy_price'] * 100) if trade['buy_price'] > 0 else 0

                            with st.expander(f"**{trade['company_name']}** ({trade['ticker']}) - {profit_rate:.2f}% | {profit:,.0f}원"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("**매수 정보**")
                                    st.markdown(f"- 매수가: {trade['buy_price']:,.0f}원")
                                    st.markdown(f"- 매수일: {trade['buy_date'][:10] if len(trade['buy_date']) > 10 else trade['buy_date']}")
                                    st.markdown(f"- 매수금액: {trade['buy_price'] * trade['quantity']:,.0f}원")
                                with col2:
                                    st.markdown("**매도 정보**")
                                    st.markdown(f"- 매도가: {trade['sell_price']:,.0f}원")
                                    st.markdown(f"- 매도일: {trade['sell_date'][:10] if len(trade['sell_date']) > 10 else trade['sell_date']}")
                                    st.markdown(f"- 매도금액: {trade['sell_price'] * trade['quantity']:,.0f}원")
                                with col3:
                                    st.markdown("**실현손익**")
                                    st.markdown(f"- 손익: {profit:,.0f}원")
                                    st.markdown(f"- 수익률: {profit_rate:.2f}%")
                                    st.markdown(f"- 수량: {trade['quantity']}주")
                else:
                    st.info("매도 기록이 없습니다.")

            # 월별 보기일 경우 달력 표시
            if st.session_state.stats_view == 'monthly':
                st.markdown("---")
                st.markdown("### 📅 일별 수익 달력")

                daily_stats = self.calculate_daily_statistics(
                    st.session_state.stats_year,
                    st.session_state.stats_month
                )

                self.render_calendar(
                    st.session_state.stats_year,
                    st.session_state.stats_month,
                    daily_stats
                )

        except Exception as e:
            st.error(f"통계 표시 중 오류가 발생했습니다: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    def render_settings(self):
        """설정 화면"""
        global TradingJournalDB

        self.add_app_header()

        st.markdown("## ⚙️ 설정")
        st.markdown("애플리케이션 설정 및 데이터 관리")

        # 탭 생성
        tab1, tab2 = st.tabs(["🗄️ 데이터베이스 관리", "ℹ️ 시스템 정보"])

        # 탭 1: 데이터베이스 관리
        with tab1:
            st.markdown("### 🗄️ 데이터베이스 관리")
            st.markdown("---")

            if TradingJournalDB is None:
                st.error("TradingJournalDB 모듈을 불러올 수 없습니다.")
                return

            # 데이터베이스 경로
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "stock_tracking_db.sqlite")

            # 데이터베이스 통계 표시
            try:
                with TradingJournalDB(db_path) as db:
                    stats = db.get_database_stats()

                    st.markdown("#### 📊 데이터베이스 현황")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("보유 종목", f"{stats.get('open_positions', 0)}개")

                    with col2:
                        st.metric("매도 종목", f"{stats.get('sold_positions', 0)}개")

                    with col3:
                        st.metric("거래 기록", f"{stats.get('history_records', 0)}건")

                    with col4:
                        st.metric("DB 크기", f"{stats.get('file_size_mb', 0)} MB")

                    st.markdown("---")

                    # DB 파일 정보
                    st.markdown("#### 📁 파일 정보")
                    st.code(stats.get('db_path', 'N/A'))

            except Exception as e:
                st.error(f"데이터베이스 통계를 불러올 수 없습니다: {str(e)}")

            st.markdown("---")

            # 백업 섹션
            st.markdown("#### 💾 데이터베이스 백업")
            st.info("⚠️ 초기화 전에 데이터베이스를 백업하는 것을 권장합니다.")

            backup_col1, backup_col2 = st.columns([3, 1])

            with backup_col1:
                st.markdown("현재 데이터베이스를 백업 파일로 저장합니다.")

            with backup_col2:
                if st.button("💾 백업 생성", use_container_width=True, type="secondary"):
                    try:
                        with TradingJournalDB(db_path) as db:
                            success = db.backup_database()
                            if success:
                                st.success("✅ 백업이 성공적으로 생성되었습니다!")
                            else:
                                st.error("❌ 백업 생성에 실패했습니다.")
                    except Exception as e:
                        st.error(f"백업 중 오류 발생: {str(e)}")

            st.markdown("---")

            # 초기화 섹션
            st.markdown("#### 🗑️ 데이터베이스 초기화")
            st.warning("⚠️ **위험**: 모든 매매 기록이 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다!")

            # 확인 체크박스
            if 'reset_confirmed' not in st.session_state:
                st.session_state.reset_confirmed = False

            confirm_check = st.checkbox(
                "모든 데이터가 삭제된다는 것을 이해했으며, 계속 진행하겠습니다.",
                key="reset_confirm_checkbox"
            )

            # 확인 입력
            col1, col2 = st.columns([3, 1])

            with col1:
                if confirm_check:
                    confirm_text = st.text_input(
                        "계속하려면 '초기화' 를 입력하세요:",
                        key="reset_confirm_text"
                    )
                    st.session_state.reset_confirmed = (confirm_text == "초기화")
                else:
                    st.session_state.reset_confirmed = False

            with col2:
                if st.button(
                    "🗑️ 초기화 실행",
                    use_container_width=True,
                    type="primary",
                    disabled=not st.session_state.reset_confirmed
                ):
                    if st.session_state.reset_confirmed:
                        with st.spinner("데이터베이스를 초기화하고 있습니다..."):
                            try:
                                with TradingJournalDB(db_path) as db:
                                    success = db.reset_database()

                                if success:
                                    st.success("✅ 데이터베이스가 성공적으로 초기화되었습니다!")
                                    st.balloons()

                                    # 상태 초기화
                                    st.session_state.reset_confirmed = False
                                    if 'reset_confirm_checkbox' in st.session_state:
                                        del st.session_state['reset_confirm_checkbox']
                                    if 'reset_confirm_text' in st.session_state:
                                        del st.session_state['reset_confirm_text']

                                    # 페이지 새로고침
                                    st.rerun()
                                else:
                                    st.error("❌ 데이터베이스 초기화에 실패했습니다.")

                            except Exception as e:
                                st.error(f"초기화 중 오류 발생: {str(e)}")
                    else:
                        st.warning("확인 절차를 완료해주세요.")

        # 탭 2: 시스템 정보
        with tab2:
            st.markdown("### ℹ️ 시스템 정보")
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📦 애플리케이션")
                st.markdown(f"- **버전**: v1.0.3")
                st.markdown(f"- **이름**: 프리즘 애널리틱스")
                st.markdown(f"- **설명**: AI 주식 분석 에이전트")

                st.markdown("#### 🔧 환경")
                st.markdown(f"- **Python**: {sys.version.split()[0]}")
                st.markdown(f"- **Streamlit**: {st.__version__}")

            with col2:
                st.markdown("#### 📁 경로")
                st.markdown(f"- **프로젝트 루트**: `{project_root}`")
                st.markdown(f"- **데이터베이스**: `{db_path}`")
                st.markdown(f"- **보고서**: `{REPORTS_DIR}`")

                st.markdown("#### 🔗 링크")
                st.markdown("- [공식 사이트](https://analysis.stocksimulation.kr)")
                st.markdown("- [GitHub](https://github.com/Gurumigun/prism-insight)")

            st.markdown("---")

            # 디버그 정보
            with st.expander("🔍 디버그 정보"):
                st.json({
                    "session_state_keys": list(st.session_state.keys()),
                    "db_stats": stats if 'stats' in locals() else "N/A",
                    "modules": {
                        "TradingJournalDB": TradingJournalDB is not None,
                        "pykrx": stock is not None
                    }
                })

    def main(self):
        """메인 애플리케이션 실행"""
        # 사이드바 디자인 개선
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-logo">📊</div>
            <div class="sidebar-title">프리즘 애널리틱스</div>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.title("메뉴")

        # 모던한 사이드바 메뉴 (버튼 스타일)
        menu_options = {
            "분석 요청": "📝",
            "보고서 보기": "📚",
            "매수 기록": "💰",
            "매도 기록": "📉",
            "거래 히스토리": "📜",
            "통계": "📊",
            "설정": "⚙️"
        }

        # session_state에 선택된 메뉴 저장 (초기값)
        if 'selected_menu' not in st.session_state:
            st.session_state.selected_menu = "분석 요청"

        # 각 메뉴를 버튼으로 표시
        for menu_name, icon in menu_options.items():
            is_selected = st.session_state.selected_menu == menu_name
            button_type = "primary" if is_selected else "secondary"

            # 버튼 클릭 시 메뉴 변경
            if st.sidebar.button(
                f"{icon} {menu_name}",
                key=f"menu_btn_{menu_name}",
                type=button_type,
                use_container_width=True
            ):
                st.session_state.selected_menu = menu_name
                st.rerun()

        menu = st.session_state.selected_menu

        # 앱 버전 및 소셜 링크
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 서비스 정보")
        st.sidebar.markdown("버전: v1.0.3")
        st.sidebar.markdown("© 2025 프리즘 애널리틱스 (https://analysis.stocksimulation.kr)")

        # 메인 콘텐츠 렌더링
        if menu == "분석 요청":
            self.render_modern_analysis_form()
        elif menu == "보고서 보기":
            self.render_modern_report_viewer()
        elif menu == "매수 기록":
            self.render_buy_records()
        elif menu == "매도 기록":
            self.render_sell_records()
        elif menu == "거래 히스토리":
            self.render_transaction_history()
        elif menu == "통계":
            self.render_statistics()
        elif menu == "설정":
            self.render_settings()

if __name__ == "__main__":
    app = ModernStockAnalysisApp()
    app.main()
