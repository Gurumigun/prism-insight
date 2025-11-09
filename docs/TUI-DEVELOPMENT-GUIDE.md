# PRISM-INSIGHT TUI 개발자 가이드

## 📚 목차

1. [개발 환경 설정](#1-개발-환경-설정)
2. [프로젝트 구조](#2-프로젝트-구조)
3. [개발 워크플로우](#3-개발-워크플로우)
4. [구현 가이드](#4-구현-가이드)
5. [테스트](#5-테스트)
6. [디버깅](#6-디버깅)
7. [배포](#7-배포)
8. [기여 가이드](#8-기여-가이드)

---

## 1. 개발 환경 설정

### 1.1 필수 요구사항

**시스템**:
- OS: Linux, macOS, Windows (WSL)
- Python: 3.10 이상
- Git: 2.0 이상
- Node.js: 18 이상 (MCP 서버용)

**개발 도구**:
- VS Code (권장) 또는 PyCharm
- Python Extension for VS Code
- Black (코드 포맷터)
- Pylint (린터)

### 1.2 저장소 설정

#### Step 1: 저장소 클론
```bash
git clone https://github.com/yourusername/prism-insight.git
cd prism-insight
```

#### Step 2: 브랜치 생성
```bash
# TUI 개발용 브랜치 생성
git checkout -b feature/tui-development
```

#### Step 3: 가상 환경 설정
```bash
# 가상 환경 생성
python -m venv venv

# 활성화
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### Step 4: 의존성 설치
```bash
# 기존 의존성
pip install -r requirements.txt

# TUI 전용 의존성
pip install -r requirements-tui.txt

# 개발 의존성
pip install -r requirements-dev.txt
```

### 1.3 개발 의존성 설정

**requirements-dev.txt 생성**:
```txt
# 테스트
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# 코드 품질
black==23.12.0
pylint==3.0.3
mypy==1.7.1
isort==5.13.2

# 문서
sphinx==7.2.6
sphinx-rtd-theme==2.0.0

# 디버깅
ipython==8.18.1
ipdb==0.13.13
```

**설치**:
```bash
pip install -r requirements-dev.txt
```

### 1.4 MCP 서버 설정

#### kospi_kosdaq 서버
```bash
pip install kospi-kosdaq-stock-server
```

#### firecrawl 서버
```bash
npm install -g firecrawl-mcp
```

#### perplexity 서버
```bash
git clone https://github.com/perplexity/perplexity-ask-mcp.git
cd perplexity-ask-mcp
npm install
npm run build
```

#### sqlite 서버
```bash
pip install mcp-server-sqlite
```

#### time 서버
```bash
pip install mcp-server-time
```

### 1.5 설정 파일 준비

```bash
# MCP 설정
cp mcp_agent.config.yaml.example mcp_agent.config.yaml
cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml

# 환경 변수
cp .env.example .env
```

**.env 편집**:
```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
FIRECRAWL_API_KEY=fc-your-firecrawl-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key
```

**mcp_agent.secrets.yaml 편집**:
```yaml
openai:
  api_key: "sk-your-openai-key"

anthropic:
  api_key: "sk-ant-your-anthropic-key"
```

### 1.6 VS Code 설정

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.rulers": [88],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

**.vscode/launch.json** (디버깅용):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "TUI Debug",
      "type": "python",
      "request": "launch",
      "module": "tui.main",
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "DEBUG": "1"
      }
    }
  ]
}
```

---

## 2. 프로젝트 구조

### 2.1 디렉토리 구조

```
prism-insight/
├── tui/                          # ✨ TUI 모듈 (새로 생성)
│   ├── __init__.py
│   ├── main.py                   # 메인 진입점
│   ├── renderer.py               # UI 렌더링
│   ├── input_handler.py          # 입력 처리
│   ├── commands.py               # 명령어 핸들러
│   ├── session.py                # 세션 관리
│   ├── adapter.py                # Cores 래퍼
│   ├── qa_agent.py               # Q&A 에이전트
│   ├── models.py                 # 데이터 모델
│   ├── config.py                 # 설정 관리
│   └── utils.py                  # 유틸리티
│
├── tests/                        # 테스트
│   ├── __init__.py
│   ├── test_tui/                 # TUI 테스트
│   │   ├── __init__.py
│   │   ├── test_renderer.py
│   │   ├── test_adapter.py
│   │   └── test_qa_agent.py
│   └── conftest.py               # pytest 설정
│
├── cores/                        # 기존 코드 (수정 불가)
│   ├── analysis.py
│   ├── agents/
│   └── ...
│
├── reports/tui/                  # TUI 보고서
├── logs/                         # 로그
├── docs/                         # 문서
├── requirements-tui.txt          # TUI 의존성
├── requirements-dev.txt          # 개발 의존성
├── run_tui.py                    # 실행 스크립트
├── setup.py                      # 패키지 설정
└── pyproject.toml                # 프로젝트 메타데이터
```

### 2.2 파일별 역할

| 파일 | 책임 | 주요 클래스/함수 |
|------|------|------------------|
| `main.py` | 프로그램 진입점, 메인 루프 | `main()`, `analyze_stock_interactive()` |
| `renderer.py` | Rich 기반 UI 렌더링 | `TUIRenderer` |
| `input_handler.py` | prompt_toolkit 입력 처리 | `InputHandler` |
| `commands.py` | 슬래시 명령어 처리 | `CommandHandler` |
| `session.py` | 세션 관리, 로깅 | `SessionManager` |
| `adapter.py` | cores/ 래퍼 | `CoreAdapter` |
| `qa_agent.py` | Claude Q&A | `QAAgent` |
| `models.py` | 데이터 모델 | `StockInfo`, `AnalysisResult` |
| `config.py` | 설정 관리 | `TUIConfig` |
| `utils.py` | 유틸리티 함수 | 헬퍼 함수들 |

---

## 3. 개발 워크플로우

### 3.1 개발 사이클

```
1. Issue 생성 (GitHub)
   ↓
2. 브랜치 생성 (feature/*)
   ↓
3. 코드 작성
   ↓
4. 테스트 작성 및 실행
   ↓
5. 코드 리뷰 (Self-review)
   ↓
6. 커밋 및 푸시
   ↓
7. Pull Request 생성
   ↓
8. 코드 리뷰
   ↓
9. 병합 (Merge)
```

### 3.2 브랜치 전략

**브랜치 명명 규칙**:
```
feature/tui-{기능명}      # 새 기능
bugfix/tui-{버그명}        # 버그 수정
refactor/tui-{리팩토링명}  # 리팩토링
docs/tui-{문서명}          # 문서
```

**예시**:
```bash
git checkout -b feature/tui-qa-agent
git checkout -b bugfix/tui-progress-bar
git checkout -b refactor/tui-renderer
git checkout -b docs/tui-user-guide
```

### 3.3 커밋 메시지 규칙

**형식**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 새 기능
- `fix`: 버그 수정
- `refactor`: 리팩토링
- `docs`: 문서
- `test`: 테스트
- `style`: 코드 스타일
- `chore`: 기타

**예시**:
```bash
git commit -m "feat(tui): Add Q&A agent with Claude Sonnet 4.5"
git commit -m "fix(tui): Fix progress bar rendering issue"
git commit -m "docs(tui): Add development guide"
```

---

## 4. 구현 가이드

### 4.1 Phase 1: 기본 TUI 구조 (1주차)

#### Task 1-1: 프로젝트 구조 생성
```bash
# 디렉토리 생성
mkdir -p tui
mkdir -p tests/test_tui
mkdir -p reports/tui
mkdir -p logs

# 파일 생성
touch tui/__init__.py
touch tui/main.py
touch tui/renderer.py
touch tui/input_handler.py
touch tui/commands.py
touch tui/session.py
touch tui/adapter.py
touch tui/qa_agent.py
touch tui/models.py
touch tui/config.py
touch tui/utils.py
```

#### Task 1-2: requirements-tui.txt 작성
```txt
# TUI 프레임워크
rich==13.9.4
prompt_toolkit==3.0.48

# 기존 의존성 재사용
mcp-agent>=0.1.10
openai~=1.64.0
anthropic~=0.64.0
pykrx==1.0.48
aiosqlite>=0.17.0
matplotlib~=3.10.1
```

**설치**:
```bash
pip install -r requirements-tui.txt
```

#### Task 1-3: tui/__init__.py 구현
```python
"""PRISM-INSIGHT TUI - AI-Powered Stock Analysis Terminal"""

__version__ = "1.0.0"
__author__ = "PRISM-INSIGHT Team"
__license__ = "MIT"

from tui.main import main

__all__ = ["main"]
```

#### Task 1-4: tui/config.py 구현
```python
"""TUI 설정 관리"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TUIConfig:
    """TUI 설정"""

    # 테마
    theme: str = "PRISM Dark"

    # AI 모델
    analysis_model: str = "gpt-4.1"
    buy_model: str = "gpt-5"
    qa_model: str = "claude-sonnet-4-5-20250929"

    # 디렉토리
    report_dir: str = "reports/tui"
    log_dir: str = "logs"

    # API 키
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    @classmethod
    def load(cls) -> "TUIConfig":
        """환경 변수에서 설정 로드"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    def validate(self) -> bool:
        """설정 검증"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return True
```

#### Task 1-5: tui/models.py 구현
```python
"""데이터 모델"""

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
    def from_dict(cls, data: dict) -> "AnalysisResult":
        """딕셔너리에서 생성"""
        return cls(
            stock_code=data.get("company_code", ""),
            stock_name=data.get("company_name", ""),
            summary=data.get("summary", ""),
            technical_analysis=data.get("technical_analysis", ""),
            trading_flow=data.get("trading_flow", ""),
            financial_analysis=data.get("financial_analysis", ""),
            industry_analysis=data.get("industry_analysis", ""),
            news_analysis=data.get("news_analysis", ""),
            market_analysis=data.get("market_analysis", ""),
            investment_strategy=data.get("investment_strategy", ""),
            ai_opinion=data.get("ai_opinion", {}),
            full_report=data.get("full_report", ""),
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

#### Task 1-6: run_tui.py 작성 (편의 스크립트)
```python
#!/usr/bin/env python
"""PRISM-INSIGHT TUI 실행 스크립트"""

import asyncio
from tui.main import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

**실행 권한 부여**:
```bash
chmod +x run_tui.py
```

#### Task 1-7: 기본 실행 테스트
```bash
# 환영 메시지만 표시하고 종료
python -m tui.main
```

### 4.2 Phase 2: AI 분석 통합 (2주차)

#### Task 2-1: cores/analysis.py 분석

**기존 함수 시그니처 확인**:
```python
# cores/analysis.py
async def analyze_stock(
    company_code: str,
    company_name: str
) -> dict:
    """주식 분석"""
    # ...
```

**문제점**: 진행 상황 콜백 없음

**해결 방법**:
1. **옵션 A**: cores/analysis.py 수정 (❌ 제약 위반)
2. **옵션 B**: Polling 방식으로 진행률 추정 (✅)
3. **옵션 C**: 로그 파일 모니터링 (✅)

#### Task 2-2: tui/adapter.py 구현
```python
"""Cores 모듈 어댑터"""

import asyncio
from typing import Callable, Optional
from pykrx import stock as pykrx_stock
from datetime import datetime

from cores.analysis import analyze_stock
from tui.models import StockInfo, AnalysisResult


class CoreAdapter:
    """Cores 모듈 어댑터"""

    ANALYSIS_STEPS = [
        ("Technical Analyst", 0.14),
        ("Trading Flow Analyst", 0.28),
        ("Financial Analyst", 0.42),
        ("Industry Analyst", 0.56),
        ("Information Analyst", 0.70),
        ("Market Analyst", 0.84),
        ("Investment Strategist", 1.0),
    ]

    async def search_stock(self, query: str) -> Optional[StockInfo]:
        """종목 검색"""
        try:
            # 종목코드로 검색
            if query.isdigit() and len(query) == 6:
                name = pykrx_stock.get_market_ticker_name(query)
                if name:
                    today = datetime.now().strftime("%Y%m%d")
                    df = pykrx_stock.get_market_cap_by_ticker(
                        date=today, ticker=query
                    )
                    return StockInfo(
                        code=query, name=name, current_price=int(df["종가"])
                    )

            # 종목명으로 검색
            tickers = pykrx_stock.get_market_ticker_list(market="ALL")
            for ticker in tickers:
                ticker_name = pykrx_stock.get_market_ticker_name(ticker)
                if query in ticker_name:
                    return StockInfo(code=ticker, name=ticker_name, current_price=0)

            return None

        except Exception:
            return None

    async def analyze(
        self,
        company_code: str,
        company_name: str,
        progress_callback: Optional[Callable] = None,
    ) -> AnalysisResult:
        """주식 분석 실행"""

        # 진행률 업데이트 태스크
        if progress_callback:
            progress_task = asyncio.create_task(
                self._update_progress(progress_callback)
            )
        else:
            progress_task = None

        try:
            # cores/analysis.py 호출
            report_dict = await analyze_stock(
                company_code=company_code, company_name=company_name
            )

            # AnalysisResult로 변환
            return AnalysisResult.from_dict(report_dict)

        finally:
            if progress_task:
                progress_task.cancel()

    async def _update_progress(self, callback: Callable):
        """진행률 업데이트 (추정)"""
        import time

        start_time = time.time()

        for agent_name, progress in self.ANALYSIS_STEPS:
            elapsed = time.time() - start_time
            elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))

            await callback(
                current_agent=agent_name,
                progress=progress * 100,
                elapsed_time=elapsed_str,
            )

            # 각 단계별 대기 (추정)
            await asyncio.sleep(15)

    async def save_report(
        self, result: AnalysisResult, output_dir: str = "reports/tui"
    ) -> str:
        """보고서 저장 (마크다운)"""
        import os
        from datetime import datetime

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.stock_code}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.full_report)

        return filepath
```

#### Task 2-3: tui/renderer.py 구현

**TUI-ARCHITECTURE.md 참조**하여 구현

#### Task 2-4: 통합 테스트
```bash
# 실제 분석 실행
python -m tui.main
> 005930
```

### 4.3 Phase 3: Q&A 에이전트 (3주차)

#### Task 3-1: tui/qa_agent.py 구현

**TUI-ARCHITECTURE.md 참조**

#### Task 3-2: Q&A 테스트
```python
# tests/test_tui/test_qa_agent.py
import pytest
from tui.qa_agent import QAAgent


@pytest.mark.asyncio
async def test_qa_agent():
    agent = QAAgent()

    answer = await agent.ask(
        question="지금 매수하기 적절한가요?",
        analysis_context="삼성전자 분석 결과...",
    )

    assert answer != ""
    assert len(answer) > 50
```

### 4.4 Phase 4: 세션 관리 및 보고서 (4주차)

#### Task 4-1: tui/session.py 구현

**TUI-ARCHITECTURE.md 참조**

#### Task 4-2: SQLite 스키마 설계
```sql
CREATE TABLE analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,
    report_path TEXT,
    buy_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_id ON analysis_history(session_id);
CREATE INDEX idx_analyzed_at ON analysis_history(analyzed_at);
```

### 4.5 Phase 5: 고급 기능 (5주차)

#### Task 5-1: tui/commands.py 구현

**TUI-ARCHITECTURE.md 참조**

#### Task 5-2: 자동완성 추가
```python
# tui/input_handler.py
from prompt_toolkit.completion import WordCompleter

# 종목명 자동완성
stock_completer = WordCompleter(
    ["삼성전자", "SK하이닉스", "NAVER", "카카오", ...]
)
```

### 4.6 Phase 6: 문서화 및 배포 (6주차)

#### Task 6-1: 문서 작성
- [x] PRD-TUI-STOCK-ANALYZER.md
- [x] TUI-ARCHITECTURE.md
- [x] TUI-USER-GUIDE.md
- [x] TUI-DEVELOPMENT-GUIDE.md (본 문서)

#### Task 6-2: README.md 업데이트
```markdown
# PRISM-INSIGHT TUI

## 빠른 시작
\`\`\`bash
git clone https://github.com/yourusername/prism-insight.git
cd prism-insight
pip install -r requirements-tui.txt
python -m tui.main
\`\`\`

## 문서
- [사용자 가이드](docs/TUI-USER-GUIDE.md)
- [개발자 가이드](docs/TUI-DEVELOPMENT-GUIDE.md)
```

---

## 5. 테스트

### 5.1 테스트 구조

```
tests/
├── __init__.py
├── conftest.py                   # pytest 설정
├── test_tui/
│   ├── __init__.py
│   ├── test_main.py              # 메인 로직
│   ├── test_renderer.py          # UI 렌더링
│   ├── test_input_handler.py     # 입력 처리
│   ├── test_adapter.py           # Cores 어댑터
│   ├── test_qa_agent.py          # Q&A 에이전트
│   ├── test_session.py           # 세션 관리
│   └── test_commands.py          # 명령어 핸들러
└── fixtures/                     # 테스트 데이터
    └── sample_analysis_result.json
```

### 5.2 conftest.py 설정

```python
"""pytest 설정"""

import pytest
import asyncio
from rich.console import Console

from tui.config import TUIConfig
from tui.models import AnalysisResult


@pytest.fixture
def console():
    """Console fixture"""
    return Console()


@pytest.fixture
def config():
    """TUIConfig fixture"""
    return TUIConfig(
        openai_api_key="test-key",
        anthropic_api_key="test-key",
    )


@pytest.fixture
def sample_analysis_result():
    """Sample AnalysisResult"""
    return AnalysisResult(
        stock_code="005930",
        stock_name="삼성전자",
        summary="테스트 요약",
        technical_analysis="기술적 분석",
        trading_flow="거래 동향",
        financial_analysis="재무 분석",
        industry_analysis="산업 분석",
        news_analysis="뉴스 분석",
        market_analysis="시장 분석",
        investment_strategy="투자 전략",
        ai_opinion={"buy_score": 8.5, "target_price": 85000},
        full_report="전체 보고서",
    )


@pytest.fixture(scope="session")
def event_loop():
    """Async event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### 5.3 단위 테스트 예시

#### test_adapter.py
```python
import pytest
from tui.adapter import CoreAdapter


@pytest.mark.asyncio
async def test_search_stock_by_code():
    """종목코드로 검색"""
    adapter = CoreAdapter()
    result = await adapter.search_stock("005930")

    assert result is not None
    assert result.code == "005930"
    assert "삼성전자" in result.name


@pytest.mark.asyncio
async def test_search_stock_by_name():
    """종목명으로 검색"""
    adapter = CoreAdapter()
    result = await adapter.search_stock("삼성전자")

    assert result is not None
    assert result.code == "005930"


@pytest.mark.asyncio
async def test_search_stock_not_found():
    """존재하지 않는 종목"""
    adapter = CoreAdapter()
    result = await adapter.search_stock("999999")

    assert result is None
```

#### test_renderer.py
```python
from tui.renderer import TUIRenderer
from tui.models import StockInfo


def test_show_welcome(console, config):
    """환영 메시지 표시"""
    renderer = TUIRenderer(console, config)
    renderer.show_welcome()
    # 출력 확인 (수동)


def test_show_analysis_start(console, config):
    """분석 시작 메시지"""
    renderer = TUIRenderer(console, config)
    stock_info = StockInfo(code="005930", name="삼성전자", current_price=72500)
    renderer.show_analysis_start(stock_info)
```

### 5.4 통합 테스트

#### test_main.py
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from tui.adapter import CoreAdapter


@pytest.mark.asyncio
async def test_full_analysis_flow(sample_analysis_result):
    """전체 분석 플로우"""
    # Given
    adapter = CoreAdapter()
    adapter.analyze = AsyncMock(return_value=sample_analysis_result)

    # When
    result = await adapter.analyze("005930", "삼성전자")

    # Then
    assert result.stock_code == "005930"
    assert result.stock_name == "삼성전자"
    assert result.summary != ""
```

### 5.5 테스트 실행

```bash
# 전체 테스트
pytest

# TUI 테스트만
pytest tests/test_tui/

# 커버리지 포함
pytest --cov=tui --cov-report=html

# 특정 테스트
pytest tests/test_tui/test_adapter.py::test_search_stock_by_code

# 마커별 실행
pytest -m asyncio
```

### 5.6 커버리지 목표

- **전체 커버리지**: 70% 이상
- **핵심 모듈**: 80% 이상
  - adapter.py
  - qa_agent.py
  - session.py

---

## 6. 디버깅

### 6.1 로깅 설정

#### tui/utils.py
```python
"""유틸리티 함수"""

import logging
from pathlib import Path


def setup_logging(debug: bool = False):
    """로깅 설정"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(f"logs/tui_debug.log"),
            logging.StreamHandler(),
        ],
    )
```

### 6.2 디버그 모드

```bash
# 환경 변수로 활성화
DEBUG=1 python -m tui.main

# 또는 코드에서
import os
if os.getenv("DEBUG"):
    import pdb; pdb.set_trace()
```

### 6.3 VS Code 디버깅

**F5**를 눌러 디버깅 시작 (launch.json 설정 필요)

**브레이크포인트 설정**:
- tui/main.py의 `analyze_stock_interactive()` 함수
- tui/adapter.py의 `analyze()` 메서드

### 6.4 일반적인 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: No module named 'tui'` | PYTHONPATH 미설정 | `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` |
| `MCP 서버 연결 실패` | MCP 설정 오류 | `mcp_agent.config.yaml` 확인 |
| `API 키 오류` | 환경 변수 미설정 | `.env` 파일 확인 |
| `터미널 색상 깨짐` | 터미널 미지원 | 256색 이상 지원 터미널 사용 |

---

## 7. 배포

### 7.1 패키지 설정

#### setup.py
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="prism-insight-tui",
    version="1.0.0",
    author="PRISM-INSIGHT Team",
    author_email="team@prism-insight.com",
    description="AI-Powered Stock Analysis Terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/prism-insight",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.9.4",
        "prompt_toolkit>=3.0.48",
        "mcp-agent>=0.1.10",
        "openai~=1.64.0",
        "anthropic~=0.64.0",
        "pykrx==1.0.48",
        "aiosqlite>=0.17.0",
    ],
    entry_points={
        "console_scripts": [
            "prism-tui=tui.main:main",
        ],
    },
)
```

#### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "prism-insight-tui"
version = "1.0.0"
description = "AI-Powered Stock Analysis Terminal"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

[tool.black]
line-length = 88
target-version = ['py310']

[tool.pylint]
max-line-length = 88
disable = ["C0111", "C0103"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 7.2 빌드

```bash
# 빌드
python -m build

# 결과물
# dist/prism_insight_tui-1.0.0-py3-none-any.whl
# dist/prism-insight-tui-1.0.0.tar.gz
```

### 7.3 설치

```bash
# wheel 파일로 설치
pip install dist/prism_insight_tui-1.0.0-py3-none-any.whl

# 실행
prism-tui
```

### 7.4 배포 체크리스트

- [ ] 모든 테스트 통과
- [ ] 커버리지 70% 이상
- [ ] 문서 완성 (4종)
- [ ] 버전 번호 업데이트
- [ ] CHANGELOG.md 작성
- [ ] 라이선스 확인
- [ ] README.md 최신화
- [ ] GitHub Release 생성
- [ ] PyPI 배포 (선택)

---

## 8. 기여 가이드

### 8.1 기여 방법

1. **Fork** 저장소
2. **브랜치** 생성 (`feature/amazing-feature`)
3. **커밋** (`git commit -m 'feat: Add amazing feature'`)
4. **푸시** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 8.2 코드 스타일

**Black** 포맷터 사용:
```bash
black tui/
```

**Pylint** 검사:
```bash
pylint tui/
```

**Type Hints**:
```python
def analyze(self, code: str, name: str) -> AnalysisResult:
    """주식 분석"""
```

### 8.3 Pull Request 템플릿

```markdown
## 변경 사항
- [ ] 새 기능
- [ ] 버그 수정
- [ ] 리팩토링
- [ ] 문서

## 설명
무엇을 변경했는지 설명

## 테스트
- [ ] 테스트 추가
- [ ] 모든 테스트 통과

## 스크린샷
(필요시 추가)

## 체크리스트
- [ ] Black 포맷팅 완료
- [ ] Pylint 검사 통과
- [ ] 문서 업데이트
```

---

## 9. 부록

### 9.1 유용한 명령어

```bash
# 개발 서버 실행
python -m tui.main

# 테스트
pytest

# 커버리지
pytest --cov=tui --cov-report=html

# 코드 포맷팅
black tui/

# 린팅
pylint tui/

# 타입 체크
mypy tui/

# 빌드
python -m build
```

### 9.2 트러블슈팅

**문제**: `rich` 출력이 깨짐
```bash
# 터미널 확인
echo $TERM

# 256색 지원 확인
tput colors

# True Color 지원 확인
python -c "from rich.console import Console; c=Console(); c.print('[red]Test[/red]')"
```

**문제**: `asyncio` 에러
```bash
# Python 버전 확인
python --version  # 3.10 이상 필요

# asyncio 디버그 모드
PYTHONASYNCIODEBUG=1 python -m tui.main
```

### 9.3 추천 도구

- **터미널**: iTerm2 (macOS), Windows Terminal (Windows), Alacritty (Linux)
- **폰트**: Hack Nerd Font, FiraCode Nerd Font
- **에디터**: VS Code, PyCharm Professional
- **디버거**: ipdb, VS Code Debugger

---

**문서 끝**

더 자세한 정보는 다음 문서를 참조하세요:
- [PRD](PRD-TUI-STOCK-ANALYZER.md) - 제품 요구사항
- [아키텍처](TUI-ARCHITECTURE.md) - 시스템 설계
- [사용자 가이드](TUI-USER-GUIDE.md) - 사용자용 가이드
