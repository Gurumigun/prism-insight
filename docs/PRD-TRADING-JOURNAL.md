# 주식 매매 일지 및 통계 기능 PRD

## 문서 정보
- **작성일**: 2025-11-09
- **버전**: 1.0.0
- **담당**: PRISM-INSIGHT Streamlit 개발팀
- **상태**: 초안

---

## 1. 개요

### 1.1 목적
개인 투자자가 주식 매매 내역을 체계적으로 기록하고, AI 분석 결과와 기술적 지표를 함께 저장하여 투자 성과를 분석하고 개선할 수 있는 매매 일지 시스템을 구축한다.

### 1.2 핵심 가치
- **데이터 기반 투자**: 매매 내역과 AI 분석 결과를 함께 저장하여 투자 의사결정 근거 확보
- **성과 추적**: 월별/종목별 수익률 통계로 투자 성과 객관적 평가
- **학습 도구**: 과거 매매 패턴 분석을 통한 투자 전략 개선
- **기술적 분석 기록**: RSI, MACD 등 주요 지표를 매매 시점에 기록하여 기술적 분석 학습

### 1.3 절대 원칙
- ✅ **기존 코드 수정 금지**: `cores/`, `examples/`, `pdf_converter.py`, `telegram_*.py` 등 기존 코드는 절대 수정하지 않음
- ✅ **Read-Only Import**: 기존 모듈은 읽기 전용으로만 import
- ✅ **로컬 저장**: SQLite를 사용한 로컬 데이터베이스 (클라우드 연동 없음)
- ✅ **개인정보 보호**: 모든 데이터는 사용자 로컬 환경에만 저장

---

## 2. 데이터베이스 설계

### 2.1 기술 스택
- **데이터베이스**: SQLite3 (파일 기반, 설치 불필요)
- **ORM**: 없음 (순수 SQL 사용으로 경량화)
- **저장 위치**: `streamlit_apps/trading_journal.db`

### 2.2 테이블 설계

#### 2.2.1 매매 기록 테이블 (trading_records)
```sql
CREATE TABLE IF NOT EXISTS trading_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 주식 기본 정보
    stock_code TEXT NOT NULL,              -- 종목코드 (예: 005930)
    stock_name TEXT NOT NULL,              -- 종목명 (예: 삼성전자)

    -- 매수 정보
    buy_quantity INTEGER NOT NULL,         -- 구매 수량
    buy_price REAL NOT NULL,               -- 구매 단가 (원)
    buy_amount REAL NOT NULL,              -- 구매 총액 (원)
    buy_date DATETIME NOT NULL,            -- 구매 일시
    buy_current_price REAL,                -- 매수 당시 현재가
    buy_close_price REAL,                  -- 매수일 종가

    -- 매도 정보
    sell_quantity INTEGER,                 -- 매도 수량 (NULL = 미매도)
    sell_price REAL,                       -- 매도 단가 (원)
    sell_amount REAL,                      -- 매도 총액 (원)
    sell_date DATETIME,                    -- 매도 일시
    sell_current_price REAL,               -- 매도 당시 현재가
    sell_close_price REAL,                 -- 매도일 종가

    -- 손익 정보
    profit_amount REAL,                    -- 수익금 (원)
    profit_rate REAL,                      -- 수익률 (%)
    holding_days INTEGER,                  -- 보유 일수

    -- AI 분석 정보
    ai_buy_opinion TEXT,                   -- AI 매수 의견
    ai_sell_opinion TEXT,                  -- AI 매도 의견
    ai_report_summary TEXT,                -- AI 분석 요약

    -- 기술적 지표 (매수 시점)
    buy_rsi_14 REAL,                       -- RSI(14)
    buy_rsi_16 REAL,                       -- RSI(16)
    buy_macd_value REAL,                   -- MACD 값
    buy_macd_signal REAL,                  -- MACD 시그널
    buy_macd_histogram REAL,               -- MACD 히스토그램
    buy_ma_20 REAL,                        -- 20일 이동평균
    buy_ma_60 REAL,                        -- 60일 이동평균
    buy_ma_90 REAL,                        -- 90일 이동평균
    buy_ma_120 REAL,                       -- 120일 이동평균
    buy_volume REAL,                       -- 거래량
    buy_volume_ma_20 REAL,                 -- 20일 평균 거래량

    -- 기술적 지표 (매도 시점)
    sell_rsi_14 REAL,                      -- RSI(14)
    sell_rsi_16 REAL,                      -- RSI(16)
    sell_macd_value REAL,                  -- MACD 값
    sell_macd_signal REAL,                 -- MACD 시그널
    sell_macd_histogram REAL,              -- MACD 히스토그램
    sell_ma_20 REAL,                       -- 20일 이동평균
    sell_ma_60 REAL,                       -- 60일 이동평균
    sell_ma_90 REAL,                       -- 90일 이동평균
    sell_ma_120 REAL,                      -- 120일 이동평균
    sell_volume REAL,                      -- 거래량
    sell_volume_ma_20 REAL,                -- 20일 평균 거래량

    -- 메타 정보
    notes TEXT,                            -- 사용자 메모
    tags TEXT,                             -- 태그 (쉼표 구분)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_stock_code ON trading_records(stock_code);
CREATE INDEX IF NOT EXISTS idx_buy_date ON trading_records(buy_date);
CREATE INDEX IF NOT EXISTS idx_sell_date ON trading_records(sell_date);
```

#### 2.2.2 월별 통계 캐시 테이블 (monthly_stats)
```sql
CREATE TABLE IF NOT EXISTS monthly_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month TEXT NOT NULL UNIQUE,       -- YYYY-MM 형식

    -- 손익 통계
    total_profit REAL,                     -- 총 수익금
    total_loss REAL,                       -- 총 손실금
    net_profit REAL,                       -- 순이익 (수익금 - 손실금)
    avg_profit_rate REAL,                  -- 평균 수익률

    -- 거래 통계
    total_trades INTEGER,                  -- 총 거래 건수
    buy_count INTEGER,                     -- 매수 건수
    sell_count INTEGER,                    -- 매도 건수
    holding_count INTEGER,                 -- 보유 중 건수

    -- 승률 통계
    win_count INTEGER,                     -- 수익 건수
    loss_count INTEGER,                    -- 손실 건수
    win_rate REAL,                         -- 승률 (%)

    -- 메타 정보
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. 기능 요구사항

### 3.1 매수 일지 기능 (F-TJ-001)

#### 3.1.1 매수 기록 입력
**우선순위**: P0 (필수)

**사용자 스토리**:
> 사용자로서, 주식을 매수했을 때 종목 정보와 매수 가격, 수량을 입력하고 AI 분석 결과와 기술적 지표를 함께 저장하여 매수 근거를 기록하고 싶다.

**기능 상세**:
1. **입력 폼**:
   - 종목코드 또는 종목명 입력 (자동완성)
   - 매수 수량 입력
   - 매수 단가 입력 (또는 현재가 자동 입력)
   - 매수 일시 선택 (기본값: 현재 시간)
   - 사용자 메모 입력 (선택)

2. **자동 수집 정보**:
   - 매수 당시 현재가 (FinanceDataReader)
   - 매수일 종가
   - 기술적 지표 자동 계산:
     - RSI(14), RSI(16)
     - MACD (12, 26, 9)
     - 이동평균선 (20일, 60일, 90일, 120일)
     - 거래량, 평균 거래량

3. **AI 분석 연동**:
   - "AI 분석 요청" 버튼 클릭 시
   - 기존 `cores/analysis.py` 호출하여 분석 보고서 생성
   - 투자 전략 섹션에서 매수 의견 추출하여 저장
   - 분석 요약본 저장

4. **저장 처리**:
   - 입력값 검증 (필수 항목 확인)
   - 중복 체크 (동일 종목/날짜 경고)
   - DB에 INSERT
   - 성공 메시지 표시

**UI 위치**: 사이드바 → "📝 매수 일지" 탭

---

### 3.2 매도 일지 기능 (F-TJ-002)

#### 3.2.1 매도 기록 입력
**우선순위**: P0 (필수)

**사용자 스토리**:
> 사용자로서, 보유 중인 주식을 매도했을 때 매도 정보를 입력하고 손익을 자동으로 계산하여 기록하고 싶다.

**기능 상세**:
1. **매도 대상 선택**:
   - 보유 중인 종목 목록 표시 (매도일이 NULL인 레코드)
   - 종목 선택 (라디오 버튼 또는 selectbox)

2. **입력 폼**:
   - 매도 수량 입력 (보유 수량 이하)
   - 매도 단가 입력 (또는 현재가 자동 입력)
   - 매도 일시 선택 (기본값: 현재 시간)
   - 사용자 메모 추가

3. **자동 수집 정보**:
   - 매도 당시 현재가
   - 매도일 종가
   - 기술적 지표 자동 계산 (매수 시점과 동일한 지표)

4. **손익 자동 계산**:
   - 수익금 = (매도가 - 매수가) × 수량
   - 수익률 = (매도가 - 매수가) / 매수가 × 100
   - 보유 일수 = 매도일 - 매수일

5. **AI 분석 연동**:
   - "AI 매도 의견 요청" 버튼
   - 현재 시점 분석 후 매도 의견 추출

6. **저장 처리**:
   - 기존 레코드 UPDATE (매도 정보 추가)
   - 월별 통계 캐시 업데이트

**UI 위치**: 사이드바 → "📊 매도 일지" 탭

---

### 3.3 매매 내역 조회 (F-TJ-003)

#### 3.3.1 전체 내역 보기
**우선순위**: P0 (필수)

**기능 상세**:
1. **필터링 옵션**:
   - 기간 선택 (날짜 범위)
   - 종목 선택 (전체/특정 종목)
   - 상태 선택 (전체/보유 중/매도 완료)
   - 수익 구분 (전체/수익/손실)

2. **목록 표시**:
   - 테이블 형식으로 표시
   - 컬럼: 종목명, 매수일, 매도일, 수량, 매수가, 매도가, 수익률, 수익금
   - 정렬 기능 (날짜순, 수익률순 등)
   - 페이지네이션 (10건씩)

3. **상세 보기**:
   - 행 클릭 시 상세 정보 확장
   - AI 분석 의견 표시
   - 기술적 지표 차트 표시
   - 수정/삭제 버튼

**UI 위치**: 메인 페이지 → "📋 매매 내역" 탭

---

### 3.4 통계 대시보드 (F-TJ-004)

#### 3.4.1 월별 통계
**우선순위**: P0 (필수)

**사용자 스토리**:
> 사용자로서, 월별 투자 성과를 한눈에 파악하여 투자 전략을 평가하고 개선하고 싶다.

**기능 상세**:
1. **기간 선택**:
   - 월 선택 (YYYY-MM)
   - 기본값: 현재 월
   - 이전/다음 월 이동 버튼

2. **주요 지표 (KPI 카드)**:
   ```
   ┌─────────────┬─────────────┬─────────────┬─────────────┐
   │  순이익     │  수익금     │  손실금     │  수익률     │
   │ +1,234,500원│ +2,500,000원│  -1,265,500원│  +12.5%    │
   └─────────────┴─────────────┴─────────────┴─────────────┘

   ┌─────────────┬─────────────┬─────────────┬─────────────┐
   │  매도건수   │  승률       │  평균수익률 │  보유건수   │
   │     15건    │   73.3%     │   +8.2%     │     5건     │
   └─────────────┴─────────────┴─────────────┴─────────────┘
   ```

3. **차트 시각화**:
   - **월별 손익 추이 (라인 차트)**:
     - X축: 월
     - Y축: 순이익
     - 최근 12개월

   - **수익/손실 비율 (파이 차트)**:
     - 수익 건수 vs 손실 건수

   - **종목별 수익 TOP 5 (바 차트)**:
     - 가장 수익이 높은 종목 5개

   - **종목별 손실 TOP 5 (바 차트)**:
     - 가장 손실이 큰 종목 5개

4. **상세 목록**:
   - 해당 월 전체 거래 내역 테이블
   - 정렬 가능
   - CSV 다운로드 기능

**UI 위치**: 메인 페이지 → "📈 통계" 탭

#### 3.4.2 종목별 통계
**우선순위**: P1 (중요)

**기능 상세**:
1. **종목 선택**
2. **종목 거래 이력**:
   - 총 매수 횟수
   - 총 매도 횟수
   - 평균 매수가
   - 평균 매도가
   - 총 수익률

3. **매매 타이밍 분석**:
   - 수익 거래의 평균 보유 기간
   - 손실 거래의 평균 보유 기간
   - 수익 시 평균 RSI
   - 손실 시 평균 RSI

---

### 3.5 기술적 지표 자동 계산 (F-TJ-005)

#### 3.5.1 지표 계산 엔진
**우선순위**: P0 (필수)

**지표 목록**:
1. **RSI (Relative Strength Index)**:
   - RSI(14): 14일 기준
   - RSI(16): 16일 기준

2. **MACD (Moving Average Convergence Divergence)**:
   - MACD Value: 12일 EMA - 26일 EMA
   - Signal Line: MACD의 9일 EMA
   - Histogram: MACD - Signal

3. **이동평균선 (Moving Average)**:
   - MA(20): 20일 단순 이동평균
   - MA(60): 60일 단순 이동평균
   - MA(90): 90일 단순 이동평균
   - MA(120): 120일 단순 이동평균

4. **거래량 지표**:
   - 당일 거래량
   - 20일 평균 거래량

**데이터 소스**:
- FinanceDataReader 사용
- 실시간 데이터가 아닌 일봉 데이터 기준

**계산 타이밍**:
- 매수/매도 기록 저장 시 자동 계산
- 백그라운드에서 계산하여 성능 최적화

---

## 4. UI/UX 설계

### 4.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│  🏠 PRISM-INSIGHT 개인 주식 분석기                            │
├─────────────────────────────────────────────────────────────┤
│  [사이드바]                 │  [메인 영역]                    │
│  ┌──────────────────┐      │  ┌───────────────────────────┐ │
│  │ 🔍 AI 주식 분석   │      │  │  탭1: 📋 매매 내역         │ │
│  ├──────────────────┤      │  │  탭2: 📈 통계              │ │
│  │ 📝 매수 일지      │◀─────┼─▶│  탭3: 🤖 AI Q&A           │ │
│  ├──────────────────┤      │  └───────────────────────────┘ │
│  │ 📊 매도 일지      │      │                                │
│  ├──────────────────┤      │  [선택된 탭 내용 표시]          │
│  │ ⚙️ 설정          │      │                                │
│  └──────────────────┘      │                                │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 매수 일지 UI

```python
# 사이드바 - 매수 일지
st.sidebar.header("📝 매수 일지")

# 종목 입력
stock_input = st.sidebar.text_input("종목코드/종목명", placeholder="005930 또는 삼성전자")

# 매수 정보
buy_quantity = st.sidebar.number_input("매수 수량", min_value=1, step=1)
buy_price = st.sidebar.number_input("매수 단가 (원)", min_value=1, step=100)
buy_date = st.sidebar.date_input("매수일", value=datetime.now())

# AI 분석 요청
if st.sidebar.button("🤖 AI 분석 요청"):
    # 분석 실행 및 의견 저장
    pass

# 메모
notes = st.sidebar.text_area("메모 (선택사항)")

# 저장 버튼
if st.sidebar.button("💾 매수 기록 저장", type="primary"):
    # 저장 로직
    pass
```

### 4.3 매도 일지 UI

```python
# 사이드바 - 매도 일지
st.sidebar.header("📊 매도 일지")

# 보유 종목 선택
holdings = get_holdings()  # 보유 중인 종목 가져오기
selected_holding = st.sidebar.selectbox(
    "매도할 종목 선택",
    options=holdings,
    format_func=lambda x: f"{x['stock_name']} ({x['quantity']}주)"
)

# 매도 정보
sell_quantity = st.sidebar.number_input("매도 수량", min_value=1, max_value=selected_holding['quantity'])
sell_price = st.sidebar.number_input("매도 단가 (원)", min_value=1, step=100)
sell_date = st.sidebar.date_input("매도일", value=datetime.now())

# 예상 손익 표시
expected_profit = calculate_profit(selected_holding, sell_quantity, sell_price)
st.sidebar.metric("예상 손익", f"{expected_profit:,}원")

# 저장 버튼
if st.sidebar.button("💰 매도 기록 저장", type="primary"):
    # 저장 로직
    pass
```

### 4.4 통계 탭 UI

```python
# 메인 - 통계 탭
st.header("📈 투자 성과 통계")

# 월 선택
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("◀ 이전 월"):
        # 이전 월로 이동
        pass
with col2:
    selected_month = st.selectbox("월 선택", options=get_months())
with col3:
    if st.button("다음 월 ▶"):
        # 다음 월로 이동
        pass

# KPI 카드
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("순이익", "+1,234,500원", "+15.2%")
with col2:
    st.metric("수익금", "+2,500,000원")
with col3:
    st.metric("손실금", "-1,265,500원")
with col4:
    st.metric("수익률", "+12.5%")

# 차트
st.subheader("월별 손익 추이")
st.line_chart(monthly_data)

st.subheader("수익/손실 비율")
st.plotly_chart(pie_chart)
```

---

## 5. 기술 구현

### 5.1 파일 구조

```
streamlit_apps/
├── trading_journal.db          # SQLite DB 파일
├── db_manager.py               # DB 관리 모듈 (NEW)
├── technical_indicators.py     # 기술적 지표 계산 (NEW)
├── personal_analyzer.py        # 메인 앱 (수정)
├── qa_agent.py                 # Q&A 에이전트
├── utils.py                    # 유틸리티 함수
├── config_manager.py           # 설정 관리
└── __init__.py
```

### 5.2 핵심 모듈

#### 5.2.1 db_manager.py
```python
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class TradingJournalDB:
    """매매 일지 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "streamlit_apps/trading_journal.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화"""
        # 테이블 생성
        pass

    def add_buy_record(self, record: Dict) -> int:
        """매수 기록 추가"""
        pass

    def update_sell_record(self, record_id: int, sell_data: Dict) -> bool:
        """매도 정보 업데이트"""
        pass

    def get_holdings(self) -> List[Dict]:
        """보유 중인 종목 조회"""
        pass

    def get_monthly_stats(self, year_month: str) -> Dict:
        """월별 통계 조회"""
        pass

    def get_all_records(self, filters: Dict = None) -> List[Dict]:
        """전체 매매 내역 조회"""
        pass
```

#### 5.2.2 technical_indicators.py
```python
import FinanceDataReader as fdr
import pandas as pd
import numpy as np

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        pass

    @staticmethod
    def calculate_macd(prices: pd.Series) -> Dict[str, float]:
        """MACD 계산"""
        pass

    @staticmethod
    def calculate_ma(prices: pd.Series, period: int) -> float:
        """이동평균 계산"""
        pass

    @staticmethod
    def get_all_indicators(stock_code: str, date: str) -> Dict:
        """모든 지표 계산"""
        # 데이터 가져오기
        df = fdr.DataReader(stock_code, start=..., end=date)

        # 각 지표 계산
        indicators = {
            'rsi_14': calculate_rsi(df['Close'], 14),
            'rsi_16': calculate_rsi(df['Close'], 16),
            'macd': calculate_macd(df['Close']),
            # ...
        }
        return indicators
```

---

## 6. 개발 로드맵

### Phase 1: 데이터베이스 구축 (1일)
- [ ] SQLite DB 스키마 설계 및 생성
- [ ] `db_manager.py` 기본 CRUD 구현
- [ ] 테스트 데이터 입력 및 검증

### Phase 2: 기술적 지표 엔진 (1일)
- [ ] `technical_indicators.py` 구현
- [ ] RSI, MACD, MA 계산 함수
- [ ] FinanceDataReader 연동
- [ ] 단위 테스트

### Phase 3: 매수/매도 일지 UI (1.5일)
- [ ] 매수 일지 사이드바 구현
- [ ] 매도 일지 사이드바 구현
- [ ] AI 분석 연동 (기존 코드 호출)
- [ ] 입력 검증 및 에러 핸들링

### Phase 4: 매매 내역 조회 (0.5일)
- [ ] 매매 내역 목록 테이블
- [ ] 필터링 기능
- [ ] 상세 보기 확장
- [ ] 수정/삭제 기능

### Phase 5: 통계 대시보드 (1.5일)
- [ ] 월별 KPI 카드
- [ ] 월별 손익 추이 차트
- [ ] 수익/손실 비율 파이 차트
- [ ] 종목별 TOP 5 차트
- [ ] CSV 다운로드 기능

### Phase 6: 테스트 및 최적화 (0.5일)
- [ ] 전체 기능 통합 테스트
- [ ] 성능 최적화 (쿼리, 캐싱)
- [ ] UI/UX 개선
- [ ] 문서화

**총 예상 기간**: 5일

---

## 7. 비기능 요구사항

### 7.1 성능
- DB 쿼리 응답 시간: < 100ms
- 기술적 지표 계산: < 2초
- 통계 차트 렌더링: < 1초

### 7.2 데이터 정합성
- 매도 수량 ≤ 매수 수량
- 매도일 ≥ 매수일
- 수익률/수익금 자동 계산 검증

### 7.3 사용성
- 입력 필드 자동완성
- 오류 메시지 친화적
- 도움말 툴팁 제공

### 7.4 보안
- SQL Injection 방지 (parameterized query)
- 로컬 저장 (외부 전송 없음)

---

## 8. 향후 확장 계획

### 8.1 단기 (1-2개월)
- 포트폴리오 분석 기능
- 배당금 기록 및 추적
- 엑셀 가져오기/내보내기

### 8.2 중기 (3-6개월)
- 매매 패턴 AI 분석
- 자동 매매 신호 생성
- 백테스팅 기능

### 8.3 장기 (6개월 이상)
- 모바일 앱 연동
- 클라우드 백업 (선택적)
- 커뮤니티 공유 기능

---

## 9. 참고 문서
- [PRISM-INSIGHT Streamlit PRD](./PRD-STREAMLIT-STOCK-ANALYZER.md)
- [Streamlit 아키텍처](./STREAMLIT-ARCHITECTURE.md)
- [SQLite 공식 문서](https://www.sqlite.org/docs.html)
- [FinanceDataReader 문서](https://github.com/FinanceData/FinanceDataReader)
