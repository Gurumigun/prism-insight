# PRISM-INSIGHT TUI - 시스템 아키텍처 설계

## 문서 정보
- **문서 버전**: 1.0.0
- **작성일**: 2025-11-09
- **관련 문서**: PRD-TUI-STOCK-ANALYZER.md

---

## 1. 아키텍처 개요

### 1.1 설계 원칙

```
┌─────────────────────────────────────────────────────────┐
│           SOLID 원칙 기반 설계                            │
├─────────────────────────────────────────────────────────┤
│ S - Single Responsibility (단일 책임)                    │
│   → 각 모듈은 하나의 역할만 담당                           │
│                                                         │
│ O - Open/Closed (개방-폐쇄)                              │
│   → 기존 코드 수정 없이 확장 가능                          │
│                                                         │
│ L - Liskov Substitution (리스코프 치환)                   │
│   → 인터페이스 기반 모듈 교체 가능                         │
│                                                         │
│ I - Interface Segregation (인터페이스 분리)               │
│   → 최소한의 인터페이스만 의존                             │
│                                                         │
│ D - Dependency Inversion (의존성 역전)                    │
│   → 추상화에 의존, 구체화 의존 최소화                       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 아키텍처 스타일

**레이어드 아키텍처 (Layered Architecture)**

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (프레젠테이션 계층)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ TUIRenderer, InputHandler, ProgressDisplay      │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Application Layer (애플리케이션 계층)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ CommandHandler, SessionManager, QAAgent         │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Domain Layer (도메인 계층)                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ CoreAdapter, AnalysisResult, StockInfo          │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Infrastructure Layer (인프라 계층)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ cores/*, MCP Servers, SQLite, Logging           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 모듈 설계

### 2.1 전체 구조

```
tui/
├── __init__.py                  # 패키지 초기화
├── main.py                      # 메인 진입점
├── renderer.py                  # UI 렌더링 (Presentation)
├── input_handler.py             # 입력 처리 (Presentation)
├── commands.py                  # 명령어 핸들러 (Application)
├── session.py                   # 세션 관리 (Application)
├── adapter.py                   # Cores 래퍼 (Domain)
├── qa_agent.py                  # Q&A 에이전트 (Application)
├── models.py                    # 데이터 모델 (Domain)
├── config.py                    # 설정 관리 (Infrastructure)
└── utils.py                     # 유틸리티 (Infrastructure)
```

### 2.2 모듈별 상세 설계

---

## 📄 `tui/main.py` - 메인 진입점

### 책임 (Responsibility)
- 프로그램 시작 및 종료
- 메인 이벤트 루프 관리
- 전역 예외 처리

### 인터페이스

```python
async def main() -> int:
    """
    TUI 메인 함수

    Returns:
        int: 종료 코드 (0: 정상, 1: 에러)
    """
```

### 구현 예시

```python
import asyncio
from typing import Optional
from rich.console import Console

from tui.renderer import TUIRenderer
from tui.input_handler import InputHandler
from tui.commands import CommandHandler
from tui.session import SessionManager
from tui.adapter import CoreAdapter
from tui.config import TUIConfig


async def main() -> int:
    """TUI 메인 함수"""
    console = Console()
    config = TUIConfig.load()

    # 컴포넌트 초기화
    renderer = TUIRenderer(console, config)
    input_handler = InputHandler(console)
    session_manager = SessionManager()
    adapter = CoreAdapter()
    command_handler = CommandHandler(
        renderer=renderer,
        session=session_manager,
        adapter=adapter
    )

    try:
        # 환영 메시지
        renderer.show_welcome()

        # 메인 루프
        while True:
            try:
                # 사용자 입력 받기
                user_input = await input_handler.get_input(
                    "📊 분석할 종목을 입력하세요"
                )

                # 종료 명령 처리
                if user_input.lower() in ['exit', 'quit', '/exit', '/quit']:
                    if renderer.confirm_exit():
                        break
                    continue

                # 명령어 처리
                if user_input.startswith('/'):
                    await command_handler.handle(user_input)
                    continue

                # 주식 분석
                if user_input.strip():
                    await analyze_stock_interactive(
                        user_input=user_input,
                        adapter=adapter,
                        renderer=renderer,
                        input_handler=input_handler,
                        session=session_manager
                    )

            except KeyboardInterrupt:
                # Ctrl+C 처리
                console.print("\n⚠️  분석을 중단하시겠습니까?", style="yellow")
                if renderer.confirm_exit():
                    break

            except Exception as e:
                renderer.show_error(f"오류가 발생했습니다: {str(e)}")
                session_manager.log_error(e)

        # 종료 메시지
        renderer.show_goodbye()
        return 0

    except Exception as e:
        console.print(f"❌ 치명적 오류: {str(e)}", style="bold red")
        return 1

    finally:
        # 리소스 정리
        await session_manager.close()


async def analyze_stock_interactive(
    user_input: str,
    adapter: CoreAdapter,
    renderer: TUIRenderer,
    input_handler: InputHandler,
    session: SessionManager
) -> None:
    """주식 분석 인터랙티브 플로우"""

    # 1. 종목 정보 검색
    stock_info = await adapter.search_stock(user_input)
    if not stock_info:
        renderer.show_error("종목을 찾을 수 없습니다.")
        return

    # 2. 분석 실행 (진행률 표시)
    renderer.show_analysis_start(stock_info)

    result = await adapter.analyze(
        company_code=stock_info.code,
        company_name=stock_info.name,
        progress_callback=renderer.update_progress
    )

    # 3. 결과 표시
    renderer.show_analysis_result(result)

    # 4. 보고서 저장 확인
    save_report = await input_handler.confirm(
        "💾 투자 보고서를 저장하시겠습니까?"
    )

    if save_report:
        report_path = await adapter.save_report(result)
        renderer.show_success(f"보고서 저장: {report_path}")

    # 5. Q&A 세션 (선택)
    await qa_session(result, input_handler, renderer)

    # 6. 세션 이력 저장
    session.add_history(
        stock_code=stock_info.code,
        stock_name=stock_info.name,
        report_path=report_path if save_report else None,
        result=result
    )


async def qa_session(
    result: 'AnalysisResult',
    input_handler: InputHandler,
    renderer: TUIRenderer
) -> None:
    """Q&A 세션"""
    from tui.qa_agent import QAAgent

    qa_agent = QAAgent()

    renderer.show_info("💬 궁금한 점이 있으신가요? (Enter로 건너뛰기)")

    while True:
        question = await input_handler.get_input(
            "💬 질문",
            allow_empty=True
        )

        if not question.strip():
            break

        # Claude에게 질문
        answer = await qa_agent.ask(
            question=question,
            analysis_context=result.full_report
        )

        renderer.show_qa_answer(answer)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

---

## 📄 `tui/renderer.py` - UI 렌더링

### 책임
- Rich를 이용한 터미널 출력
- 프로그레스 바 표시
- 구조화된 분석 결과 렌더링

### 주요 클래스

```python
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from typing import Optional

from tui.models import AnalysisResult, StockInfo
from tui.config import TUIConfig


class TUIRenderer:
    """TUI 렌더링 엔진"""

    def __init__(self, console: Console, config: TUIConfig):
        self.console = console
        self.config = config
        self.current_progress: Optional[Progress] = None

    def show_welcome(self) -> None:
        """환영 메시지 표시"""
        welcome_text = """
╭───────────────────────────────────────────────────────────────╮
│                                                               │
│   ██████╗ ██████╗ ██╗███████╗███╗   ███╗    ████████╗██╗   ██╗│
│   ██╔══██╗██╔══██╗██║██╔════╝████╗ ████║    ╚══██╔══╝██║   ██║│
│   ██████╔╝██████╔╝██║███████╗██╔████╔██║       ██║   ██║   ██║│
│   ██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║       ██║   ██║   ██║│
│   ██║     ██║  ██║██║███████║██║ ╚═╝ ██║       ██║   ╚██████╔╝│
│   ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝       ╚═╝    ╚═════╝ │
│                                                               │
│              AI-Powered Stock Analysis Terminal              │
│                     v1.0.0 | 2025-11-09                      │
╰───────────────────────────────────────────────────────────────╯
        """
        self.console.print(welcome_text, style="bold cyan")

        info_panel = Panel(
            "[bold]🤖 AI 모델:[/bold] GPT-5, Claude Sonnet 4.5\n"
            "[bold]📊 데이터:[/bold] 한국거래소, WiseReport, Perplexity\n"
            "[bold]⚡ 모드:[/bold] 대화형 TUI",
            title="시스템 정보",
            border_style="blue"
        )
        self.console.print(info_panel)
        self.console.print()

        # 사용법
        help_table = Table(show_header=False, box=None)
        help_table.add_column(style="cyan")
        help_table.add_column()
        help_table.add_row("💡 사용법:", "")
        help_table.add_row("  •", "종목코드(예: 005930) 또는 종목명(예: 삼성전자) 입력")
        help_table.add_row("  •", "/help : 명령어 도움말")
        help_table.add_row("  •", "/exit : 프로그램 종료")
        self.console.print(help_table)
        self.console.print()

    def show_analysis_start(self, stock_info: StockInfo) -> None:
        """분석 시작 메시지"""
        panel = Panel(
            f"[bold]{stock_info.name} ({stock_info.code})[/bold]\n"
            f"현재가: {stock_info.current_price:,}원",
            title="🔍 분석 시작",
            border_style="green"
        )
        self.console.print(panel)

    def update_progress(
        self,
        current_agent: str,
        progress: float,
        elapsed_time: str
    ) -> None:
        """진행 상황 업데이트"""
        if self.current_progress is None:
            self.current_progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )
            self.current_progress.start()
            self.task_id = self.current_progress.add_task(
                description="분석 중...",
                total=100
            )

        self.current_progress.update(
            self.task_id,
            completed=progress,
            description=f"🤖 {current_agent} | ⏱️  {elapsed_time}"
        )

        if progress >= 100:
            self.current_progress.stop()
            self.current_progress = None

    def show_analysis_result(self, result: AnalysisResult) -> None:
        """분석 결과 표시"""
        self.console.rule("[bold green]✅ 분석 완료")
        self.console.print()

        # 각 섹션별 렌더링
        self._render_summary(result.summary)
        self._render_technical_analysis(result.technical_analysis)
        self._render_trading_flow(result.trading_flow)
        self._render_financial_analysis(result.financial_analysis)
        self._render_industry_analysis(result.industry_analysis)
        self._render_news_analysis(result.news_analysis)
        self._render_market_analysis(result.market_analysis)
        self._render_investment_strategy(result.investment_strategy)
        self._render_ai_opinion(result.ai_opinion)

    def _render_summary(self, summary: str) -> None:
        """요약 렌더링"""
        panel = Panel(
            Markdown(summary),
            title="📌 핵심 투자 포인트",
            border_style="yellow"
        )
        self.console.print(panel)
        self.console.print()

    def _render_ai_opinion(self, opinion: dict) -> None:
        """AI 투자 의견 렌더링"""
        buy_score = opinion.get('buy_score', 0)
        target_price = opinion.get('target_price', 0)
        stop_loss = opinion.get('stop_loss', 0)

        # 점수 바
        bar_length = 10
        filled = int(buy_score)
        bar = "█" * filled + "░" * (bar_length - filled)

        content = (
            f"[bold]매수 점수:[/bold] {bar} {buy_score}/10\n"
            f"[bold]목표가:[/bold] {target_price:,}원\n"
            f"[bold]손절가:[/bold] {stop_loss:,}원\n\n"
            f"{opinion.get('reasoning', '')}"
        )

        panel = Panel(
            content,
            title="💰 AI 투자 의견 (GPT-5)",
            border_style="magenta"
        )
        self.console.print(panel)
        self.console.print()

    def show_qa_answer(self, answer: str) -> None:
        """Q&A 답변 표시"""
        panel = Panel(
            Markdown(answer),
            title="🤖 Claude Sonnet 4.5",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()

    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        self.console.print(f"❌ {message}", style="bold red")

    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        self.console.print(f"✅ {message}", style="bold green")

    def show_info(self, message: str) -> None:
        """정보 메시지 표시"""
        self.console.print(f"ℹ️  {message}", style="bold blue")

    def confirm_exit(self) -> bool:
        """종료 확인"""
        from rich.prompt import Confirm
        return Confirm.ask("정말 종료하시겠습니까?")

    def show_goodbye(self) -> None:
        """종료 메시지"""
        panel = Panel(
            "[bold]PRISM-INSIGHT TUI를 이용해주셔서 감사합니다![/bold]\n"
            "성공적인 투자 되세요! 📈",
            title="👋 Goodbye",
            border_style="cyan"
        )
        self.console.print(panel)
```

---

## 📄 `tui/input_handler.py` - 입력 처리

### 책임
- prompt_toolkit 기반 입력 처리
- 자동완성 제공
- 입력 히스토리 관리

### 구현

```python
from typing import Optional, List
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console


class InputHandler:
    """사용자 입력 처리"""

    def __init__(self, console: Console):
        self.console = console
        self.session = PromptSession(
            history=FileHistory('.tui_history')
        )

        # 명령어 자동완성
        self.command_completer = WordCompleter([
            '/help', '/history', '/last', '/clear', '/config', '/exit', '/quit'
        ])

    async def get_input(
        self,
        prompt: str = ">",
        allow_empty: bool = False
    ) -> str:
        """사용자 입력 받기"""
        while True:
            user_input = await self.session.prompt_async(
                f"{prompt}: ",
                completer=self.command_completer
            )

            if user_input.strip() or allow_empty:
                return user_input.strip()

            if not allow_empty:
                self.console.print("❌ 입력이 비어있습니다.", style="red")

    async def confirm(self, message: str) -> bool:
        """Yes/No 확인"""
        while True:
            response = await self.get_input(f"{message} (y/n)")
            if response.lower() in ['y', 'yes', 'ㅛ']:
                return True
            elif response.lower() in ['n', 'no', 'ㅜ']:
                return False
            else:
                self.console.print("❌ y 또는 n을 입력하세요.", style="red")
```

---

## 📄 `tui/adapter.py` - Cores 래퍼

### 책임
- cores/analysis.py 호출
- PDF/텔레그램 기능 제거
- 진행 상황 콜백 제공

### 구현

```python
import asyncio
from typing import Callable, Optional
from pykrx import stock as pykrx_stock

from cores.analysis import analyze_stock
from tui.models import StockInfo, AnalysisResult


class CoreAdapter:
    """Cores 모듈 어댑터"""

    async def search_stock(self, query: str) -> Optional[StockInfo]:
        """종목 검색"""
        try:
            # 종목코드로 검색
            if query.isdigit() and len(query) == 6:
                name = pykrx_stock.get_market_ticker_name(query)
                if name:
                    price = pykrx_stock.get_market_cap_by_ticker(
                        date="20251109",  # 현재 날짜
                        ticker=query
                    )
                    return StockInfo(
                        code=query,
                        name=name,
                        current_price=price
                    )

            # 종목명으로 검색
            tickers = pykrx_stock.get_market_ticker_list(market="ALL")
            for ticker in tickers:
                ticker_name = pykrx_stock.get_market_ticker_name(ticker)
                if query in ticker_name:
                    return StockInfo(
                        code=ticker,
                        name=ticker_name,
                        current_price=0  # 나중에 조회
                    )

            return None

        except Exception:
            return None

    async def analyze(
        self,
        company_code: str,
        company_name: str,
        progress_callback: Optional[Callable] = None
    ) -> AnalysisResult:
        """주식 분석 실행"""

        # cores/analysis.py의 analyze_stock 호출
        # (진행 상황을 콜백으로 전달하도록 수정 필요)
        report_dict = await analyze_stock(
            company_code=company_code,
            company_name=company_name,
            progress_callback=progress_callback  # 추가 필요
        )

        # AnalysisResult로 변환
        return AnalysisResult.from_dict(report_dict)

    async def save_report(
        self,
        result: AnalysisResult,
        output_dir: str = "reports/tui"
    ) -> str:
        """보고서 저장 (마크다운만)"""
        import os
        from datetime import datetime

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.stock_code}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.full_report)

        return filepath
```

---

## 📄 `tui/qa_agent.py` - Q&A 에이전트

### 책임
- Claude Sonnet 4.5 API 호출
- 대화 히스토리 관리
- 분석 결과를 컨텍스트로 제공

### 구현

```python
import anthropic
from typing import List, Dict


class QAAgent:
    """Claude 기반 Q&A 에이전트"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.conversation_history: List[Dict] = []
        self.model = "claude-sonnet-4-5-20250929"

    async def ask(
        self,
        question: str,
        analysis_context: str
    ) -> str:
        """질문에 대한 답변 생성"""

        # 시스템 프롬프트
        system_prompt = f"""
당신은 주식 투자 전문가입니다.
다음은 AI가 분석한 주식 보고서입니다:

{analysis_context}

사용자의 질문에 대해 이 보고서를 기반으로 답변해주세요.
답변은 간결하고 명확하게 작성하며, 근거를 명시해주세요.
"""

        # 대화 히스토리에 추가
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        # API 호출
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=self.conversation_history
        )

        answer = response.content[0].text

        # 답변을 히스토리에 추가
        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        return answer

    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
```

---

## 📄 `tui/session.py` - 세션 관리

### 책임
- 분석 이력 저장 (SQLite)
- 로깅
- 통계 추적

### 구현

```python
import aiosqlite
from datetime import datetime
from typing import List, Optional
import logging
from pathlib import Path

from tui.models import AnalysisResult, SessionHistory


class SessionManager:
    """세션 관리자"""

    def __init__(self, db_path: str = "logs/tui_sessions.db"):
        self.db_path = db_path
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.history: List[SessionHistory] = []

        # 로깅 설정
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            filename=f"logs/tui_session_{self.session_id}.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # DB 초기화
        asyncio.create_task(self._init_db())

    async def _init_db(self):
        """DB 초기화"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    stock_code TEXT,
                    stock_name TEXT,
                    analyzed_at TEXT,
                    report_path TEXT,
                    buy_score REAL
                )
            """)
            await db.commit()

    def add_history(
        self,
        stock_code: str,
        stock_name: str,
        report_path: Optional[str],
        result: AnalysisResult
    ):
        """이력 추가"""
        history = SessionHistory(
            session_id=self.session_id,
            stock_code=stock_code,
            stock_name=stock_name,
            analyzed_at=datetime.now(),
            report_path=report_path,
            buy_score=result.ai_opinion.get('buy_score', 0)
        )

        self.history.append(history)

        # DB 저장
        asyncio.create_task(self._save_to_db(history))

        # 로깅
        self.logger.info(
            f"분석 완료: {stock_name}({stock_code}) - "
            f"매수 점수: {history.buy_score}"
        )

    async def _save_to_db(self, history: SessionHistory):
        """DB에 저장"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO analysis_history
                (session_id, stock_code, stock_name, analyzed_at, report_path, buy_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    history.session_id,
                    history.stock_code,
                    history.stock_name,
                    history.analyzed_at.isoformat(),
                    history.report_path,
                    history.buy_score
                )
            )
            await db.commit()

    async def get_history(self, limit: int = 10) -> List[SessionHistory]:
        """이력 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT stock_code, stock_name, analyzed_at, report_path, buy_score
                FROM analysis_history
                WHERE session_id = ?
                ORDER BY analyzed_at DESC
                LIMIT ?
                """,
                (self.session_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    SessionHistory(
                        session_id=self.session_id,
                        stock_code=row[0],
                        stock_name=row[1],
                        analyzed_at=datetime.fromisoformat(row[2]),
                        report_path=row[3],
                        buy_score=row[4]
                    )
                    for row in rows
                ]

    def log_error(self, error: Exception):
        """에러 로깅"""
        self.logger.error(f"Error: {str(error)}", exc_info=True)

    async def close(self):
        """리소스 정리"""
        self.logger.info(f"세션 종료: {len(self.history)}개 종목 분석 완료")
```

---

## 📄 `tui/models.py` - 데이터 모델

### 데이터 클래스 정의

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class StockInfo:
    """종목 정보"""
    code: str
    name: str
    current_price: int


@dataclass
class AnalysisResult:
    """분석 결과"""
    stock_code: str
    stock_name: str
    summary: str
    technical_analysis: str
    trading_flow: str
    financial_analysis: str
    industry_analysis: str
    news_analysis: str
    market_analysis: str
    investment_strategy: str
    ai_opinion: Dict
    full_report: str

    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisResult':
        """딕셔너리에서 생성"""
        return cls(
            stock_code=data['company_code'],
            stock_name=data['company_name'],
            summary=data.get('summary', ''),
            technical_analysis=data.get('technical_analysis', ''),
            trading_flow=data.get('trading_flow', ''),
            financial_analysis=data.get('financial_analysis', ''),
            industry_analysis=data.get('industry_analysis', ''),
            news_analysis=data.get('news_analysis', ''),
            market_analysis=data.get('market_analysis', ''),
            investment_strategy=data.get('investment_strategy', ''),
            ai_opinion=data.get('ai_opinion', {}),
            full_report=data.get('full_report', '')
        )


@dataclass
class SessionHistory:
    """세션 이력"""
    session_id: str
    stock_code: str
    stock_name: str
    analyzed_at: datetime
    report_path: Optional[str]
    buy_score: float
```

---

## 📄 `tui/commands.py` - 명령어 핸들러

### 구현

```python
from rich.table import Table
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tui.renderer import TUIRenderer
    from tui.session import SessionManager
    from tui.adapter import CoreAdapter


class CommandHandler:
    """명령어 처리"""

    def __init__(
        self,
        renderer: 'TUIRenderer',
        session: 'SessionManager',
        adapter: 'CoreAdapter'
    ):
        self.renderer = renderer
        self.session = session
        self.adapter = adapter
        self.last_result = None

    async def handle(self, command: str):
        """명령어 실행"""
        cmd = command.lower().strip()

        if cmd == '/help':
            self._show_help()
        elif cmd == '/history':
            await self._show_history()
        elif cmd == '/last':
            self._show_last_result()
        elif cmd == '/clear':
            self._clear_screen()
        elif cmd == '/config':
            self._show_config()
        else:
            self.renderer.show_error(f"알 수 없는 명령어: {command}")

    def _show_help(self):
        """도움말 표시"""
        help_text = """
# 📖 PRISM-INSIGHT TUI 사용 가이드

## 주식 분석
- 종목코드 입력 (예: 005930)
- 종목명 입력 (예: 삼성전자)

## 명령어
- /help      : 이 도움말 표시
- /history   : 분석 이력 조회
- /last      : 마지막 분석 결과 재표시
- /clear     : 화면 클리어
- /config    : AI 모델 설정 확인
- /exit      : 프로그램 종료

## 단축키
- Ctrl+C     : 분석 중단 / 종료 확인
- ↑/↓        : 입력 히스토리 탐색
"""
        self.renderer.console.print(help_text)

    async def _show_history(self):
        """이력 표시"""
        history = await self.session.get_history()

        if not history:
            self.renderer.show_info("분석 이력이 없습니다.")
            return

        table = Table(title="📊 분석 이력")
        table.add_column("종목코드", style="cyan")
        table.add_column("종목명", style="green")
        table.add_column("분석 시간", style="yellow")
        table.add_column("매수 점수", style="magenta")

        for h in history:
            table.add_row(
                h.stock_code,
                h.stock_name,
                h.analyzed_at.strftime("%Y-%m-%d %H:%M:%S"),
                f"{h.buy_score}/10"
            )

        self.renderer.console.print(table)

    def _show_last_result(self):
        """마지막 결과 재표시"""
        if self.last_result:
            self.renderer.show_analysis_result(self.last_result)
        else:
            self.renderer.show_info("분석 결과가 없습니다.")

    def _clear_screen(self):
        """화면 클리어"""
        self.renderer.console.clear()

    def _show_config(self):
        """설정 표시"""
        from tui.config import TUIConfig
        config = TUIConfig.load()

        config_table = Table(title="⚙️  설정")
        config_table.add_column("항목", style="cyan")
        config_table.add_column("값", style="yellow")

        config_table.add_row("분석 에이전트 AI", "GPT-4.1")
        config_table.add_row("매수 전문가 AI", "GPT-5")
        config_table.add_row("Q&A 에이전트 AI", "Claude Sonnet 4.5")
        config_table.add_row("테마", config.theme)

        self.renderer.console.print(config_table)
```

---

## 3. 의존성 관리

### 3.1 의존성 주입 패턴

```python
# 의존성 주입을 통한 결합도 감소
class TUIApp:
    def __init__(
        self,
        renderer: TUIRenderer,
        input_handler: InputHandler,
        adapter: CoreAdapter,
        session: SessionManager
    ):
        self.renderer = renderer
        self.input_handler = input_handler
        self.adapter = adapter
        self.session = session
```

### 3.2 인터페이스 정의

```python
from abc import ABC, abstractmethod

class IRenderer(ABC):
    """렌더러 인터페이스"""

    @abstractmethod
    def show_welcome(self) -> None:
        pass

    @abstractmethod
    def show_analysis_result(self, result: AnalysisResult) -> None:
        pass

class IAdapter(ABC):
    """어댑터 인터페이스"""

    @abstractmethod
    async def analyze(
        self,
        company_code: str,
        company_name: str
    ) -> AnalysisResult:
        pass
```

---

## 4. 에러 처리 전략

### 4.1 에러 계층 구조

```python
class TUIError(Exception):
    """TUI 기본 에러"""
    pass

class StockNotFoundError(TUIError):
    """종목 없음 에러"""
    pass

class AnalysisError(TUIError):
    """분석 실패 에러"""
    pass

class APIError(TUIError):
    """API 호출 실패 에러"""
    pass
```

### 4.2 에러 핸들링 패턴

```python
async def safe_analyze(adapter, stock_code):
    """안전한 분석 실행"""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            return await adapter.analyze(stock_code)
        except APIError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 지수 백오프
                await asyncio.sleep(wait_time)
            else:
                raise
```

---

## 5. 성능 최적화

### 5.1 비동기 처리

```python
# UI 업데이트와 분석을 동시에 실행
async def analyze_with_progress(adapter, renderer, stock_code):
    # 분석 태스크
    analysis_task = asyncio.create_task(
        adapter.analyze(stock_code)
    )

    # 진행률 표시 태스크
    progress_task = asyncio.create_task(
        renderer.animate_progress()
    )

    # 분석 완료 대기
    result = await analysis_task

    # 진행률 표시 종료
    progress_task.cancel()

    return result
```

### 5.2 캐싱

```python
from functools import lru_cache

class CoreAdapter:
    @lru_cache(maxsize=100)
    def search_stock(self, query: str) -> Optional[StockInfo]:
        """종목 검색 (캐싱)"""
        # 검색 로직
```

---

## 6. 보안 고려사항

### 6.1 API 키 관리

```python
from tui.config import TUIConfig

class SecureConfig:
    """보안 설정"""

    @staticmethod
    def load_api_keys():
        """환경 변수에서 API 키 로드"""
        import os

        return {
            'openai_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_key': os.getenv('ANTHROPIC_API_KEY'),
            'firecrawl_key': os.getenv('FIRECRAWL_API_KEY'),
        }
```

### 6.2 입력 검증

```python
def validate_stock_code(code: str) -> bool:
    """종목 코드 검증"""
    return code.isdigit() and len(code) == 6
```

---

## 7. 테스트 전략

### 7.1 단위 테스트

```python
import pytest
from tui.adapter import CoreAdapter

@pytest.mark.asyncio
async def test_search_stock():
    adapter = CoreAdapter()
    result = await adapter.search_stock("005930")

    assert result is not None
    assert result.code == "005930"
    assert result.name == "삼성전자"
```

### 7.2 통합 테스트

```python
@pytest.mark.asyncio
async def test_full_analysis_flow():
    # Given
    adapter = CoreAdapter()
    renderer = TUIRenderer(Console(), TUIConfig())

    # When
    result = await adapter.analyze("005930", "삼성전자")

    # Then
    assert result.stock_code == "005930"
    assert result.summary != ""
```

---

## 8. 배포 체크리스트

- [ ] 모든 의존성 설치 확인 (requirements-tui.txt)
- [ ] MCP 서버 설정 완료
- [ ] API 키 환경 변수 설정
- [ ] 로그 디렉토리 생성 (logs/)
- [ ] 보고서 디렉토리 생성 (reports/tui/)
- [ ] 단위 테스트 통과
- [ ] 사용자 가이드 검토
- [ ] 라이선스 확인

---

**문서 끝**
