# 주식 매매 일지 및 통계 기능 PRD

## 문서 정보
- **작성일**: 2025-11-09
- **최종 수정일**: 2025-11-09
- **버전**: 1.2.0
- **담당**: PRISM-INSIGHT Streamlit 개발팀
- **상태**: 승인됨

### 변경 이력
- **v1.2.0** (2025-11-09):
  - **AI 의견 선택사항 명시**: AI 분석 요청 버튼을 클릭한 경우에만 AI 의견 저장
  - **직접 입력 시 빈값**: 사용자가 직접 매수/매도 일지를 작성하는 경우 AI 의견은 NULL
  - F-TJ-001, F-TJ-002: AI 분석 연동이 선택사항임을 명확히 표시
  - F-TJ-007: AI 분석 완료 후에만 사용 가능함을 강조
  - UI 예시 업데이트: AI 의견 추가 섹션 분리 및 선택사항 표시
- **v1.1.0** (2025-11-09):
  - F-TJ-006 추가: 매매 기록 수정 기능 (자동 재계산 포함)
  - F-TJ-007 추가: AI 분석 결과 바로 적용 기능 (원클릭 일지 작성)
- **v1.0.0** (2025-11-09): 초안 작성

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

3. **AI 분석 연동 (선택사항)**:
   - **"🤖 AI 분석 요청" 버튼 클릭 시에만**:
     - 기존 `cores/analysis.py` 호출하여 분석 보고서 생성
     - 투자 전략 섹션에서 매수 의견 추출하여 저장
     - 분석 요약본 저장
   - **버튼을 클릭하지 않은 경우**:
     - `ai_buy_opinion`: NULL (빈값)
     - `ai_report_summary`: NULL (빈값)
   - **사용자가 직접 입력한 경우** (F-TJ-007 미사용):
     - AI 의견 없이 매수 기록만 저장

4. **저장 처리**:
   - 입력값 검증 (필수 항목: 종목코드, 수량, 가격, 날짜)
   - AI 의견은 선택사항 (없어도 저장 가능)
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

5. **AI 분석 연동 (선택사항)**:
   - **"🤖 AI 매도 의견 요청" 버튼 클릭 시에만**:
     - 현재 시점 분석 (cores/analysis.py 호출)
     - 투자 전략 섹션에서 매도 의견 추출하여 저장
   - **버튼을 클릭하지 않은 경우**:
     - `ai_sell_opinion`: NULL (빈값)
   - **사용자가 직접 입력한 경우** (F-TJ-007 미사용):
     - AI 의견 없이 매도 기록만 저장

6. **저장 처리**:
   - 입력값 검증 (필수 항목: 매도 수량, 가격, 날짜)
   - AI 의견은 선택사항 (없어도 저장 가능)
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

### 3.6 매매 기록 수정 기능 (F-TJ-006)

#### 3.6.1 기록 수정
**우선순위**: P0 (필수)

**사용자 스토리**:
> 사용자로서, 매수/매도 시 입력한 금액이나 수량이 실제와 다를 경우 이를 수정하여 정확한 손익을 추적하고 싶다.

**배경**:
- 실제 매매 시 체결가가 예상과 다를 수 있음 (시장가 주문, 부분 체결 등)
- 수수료, 세금을 포함한 실제 체결 금액이 다를 수 있음
- 분할 매수/매도로 평균 단가가 변경될 수 있음
- 입력 실수를 수정해야 할 필요

**기능 상세**:

1. **수정 가능 필드**:
   - ✅ 매수 수량 (buy_quantity)
   - ✅ 매수 단가 (buy_price)
   - ✅ 매수 일시 (buy_date)
   - ✅ 매도 수량 (sell_quantity)
   - ✅ 매도 단가 (sell_price)
   - ✅ 매도 일시 (sell_date)
   - ✅ 사용자 메모 (notes)
   - ❌ 기술적 지표 (자동 재계산됨)
   - ❌ AI 의견 (재요청 필요)

2. **수정 UI 접근**:
   - **방법 1**: 매매 내역 탭에서 행 클릭 → "✏️ 수정" 버튼
   - **방법 2**: 보유 중 종목 상세 보기 → "✏️ 수정" 버튼

3. **수정 프로세스**:
   ```
   사용자가 수정 버튼 클릭
      ↓
   팝업 또는 확장 영역에 현재 데이터 표시
      ↓
   사용자가 값 변경 (수량, 가격, 날짜 등)
      ↓
   "💾 저장" 버튼 클릭
      ↓
   [자동 처리]
   1. 매수/매도 총액 재계산 (가격 × 수량)
   2. 손익금/수익률 재계산
   3. 보유 일수 재계산
   4. 날짜 변경 시 기술적 지표 재계산
   5. 월별 통계 캐시 무효화 및 재계산
      ↓
   DB UPDATE
      ↓
   성공 메시지 + 변경 사항 요약 표시
   ```

4. **자동 재계산 로직**:
   ```python
   def update_record(record_id: int, updated_data: dict):
       """매매 기록 수정 및 자동 재계산"""

       # 1. 기본 값 재계산
       if 'buy_price' in updated_data or 'buy_quantity' in updated_data:
           updated_data['buy_amount'] = updated_data.get('buy_price', old_buy_price) * \
                                        updated_data.get('buy_quantity', old_buy_quantity)

       if 'sell_price' in updated_data or 'sell_quantity' in updated_data:
           updated_data['sell_amount'] = updated_data.get('sell_price', old_sell_price) * \
                                        updated_data.get('sell_quantity', old_sell_quantity)

       # 2. 손익 재계산
       if 'buy_price' in updated_data or 'sell_price' in updated_data or \
          'buy_quantity' in updated_data or 'sell_quantity' in updated_data:
           buy_price = updated_data.get('buy_price', old_buy_price)
           sell_price = updated_data.get('sell_price', old_sell_price)
           quantity = updated_data.get('sell_quantity', old_sell_quantity)

           updated_data['profit_amount'] = (sell_price - buy_price) * quantity
           updated_data['profit_rate'] = ((sell_price - buy_price) / buy_price) * 100

       # 3. 보유 일수 재계산
       if 'buy_date' in updated_data or 'sell_date' in updated_data:
           buy_date = updated_data.get('buy_date', old_buy_date)
           sell_date = updated_data.get('sell_date', old_sell_date)
           updated_data['holding_days'] = (sell_date - buy_date).days

       # 4. 날짜 변경 시 기술적 지표 재계산
       if 'buy_date' in updated_data:
           indicators = calculate_technical_indicators(stock_code, updated_data['buy_date'])
           updated_data.update({f'buy_{k}': v for k, v in indicators.items()})

       if 'sell_date' in updated_data:
           indicators = calculate_technical_indicators(stock_code, updated_data['sell_date'])
           updated_data.update({f'sell_{k}': v for k, v in indicators.items()})

       # 5. DB 업데이트
       db.update_record(record_id, updated_data)

       # 6. 통계 캐시 무효화
       invalidate_monthly_stats_cache()
   ```

5. **수정 이력 추적** (선택사항):
   - 수정 전/후 값 로깅
   - `updated_at` 타임스탬프 자동 갱신
   - 변경 사항 요약 표시:
     ```
     ✅ 매매 기록이 수정되었습니다.

     변경 사항:
     • 매수 단가: 72,000원 → 72,500원 (+500원)
     • 매수 수량: 10주 → 8주 (-2주)
     • 매수 총액: 720,000원 → 580,000원
     • 수익금: +50,000원 → +40,000원 (재계산됨)
     • 수익률: +6.9% → +6.9% (재계산됨)
     ```

6. **검증 규칙**:
   - 매도 수량 ≤ 매수 수량
   - 매도일 ≥ 매수일
   - 가격 > 0, 수량 > 0
   - 날짜는 미래일 수 없음

**UI 예시**:
```python
# 매매 내역 상세 보기
with st.expander(f"📝 {row['stock_name']} 상세 정보"):
    if st.button("✏️ 수정", key=f"edit_{row['id']}"):
        st.session_state['editing_record'] = row['id']

    if st.session_state.get('editing_record') == row['id']:
        # 수정 폼
        with st.form(f"edit_form_{row['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                new_buy_quantity = st.number_input("매수 수량", value=row['buy_quantity'])
                new_buy_price = st.number_input("매수 단가", value=row['buy_price'])
                new_buy_date = st.date_input("매수일", value=row['buy_date'])

            with col2:
                new_sell_quantity = st.number_input("매도 수량", value=row['sell_quantity'])
                new_sell_price = st.number_input("매도 단가", value=row['sell_price'])
                new_sell_date = st.date_input("매도일", value=row['sell_date'])

            new_notes = st.text_area("메모", value=row['notes'])

            submitted = st.form_submit_button("💾 저장")
            if submitted:
                update_record(row['id'], {
                    'buy_quantity': new_buy_quantity,
                    'buy_price': new_buy_price,
                    # ...
                })
                st.success("✅ 수정되었습니다!")
```

**데이터 무결성 보장**:
- 트랜잭션 사용 (SQLite BEGIN/COMMIT)
- 수정 전 백업 (롤백 가능)
- Cascade 업데이트 (관련 통계 자동 갱신)

---

### 3.7 AI 분석 결과 바로 적용 기능 (F-TJ-007)

#### 3.7.1 원클릭 매매 일지 작성
**우선순위**: P0 (필수)

**사용자 스토리**:
> 사용자로서, AI 주식 분석을 실행한 후 그 결과를 기반으로 매수/매도 일지에 바로 반영하여 중복 입력을 줄이고 싶다.

**배경**:
- 사용자가 AI 분석 탭에서 종목 분석 후, 매수/매도 일지에 동일 정보를 다시 입력해야 하는 불편함
- AI 분석 결과(투자 의견)를 수동으로 복사/붙여넣기 하는 번거로움
- 분석 직후 매매 기록을 남기고 싶을 때 빠른 작성 필요

**중요**:
- ⚠️ **이 기능은 AI 분석 완료 후에만 사용 가능**
- ⚠️ **AI 의견은 이 기능을 통해서만 자동 입력됨**
- ⚠️ **일반적으로 직접 입력하는 경우 AI 의견 필드는 NULL (빈값)**

**기능 상세**:

1. **트리거 위치**:
   - AI 주식 분석 탭에서 분석 완료 후
   - 분석 결과 하단에 버튼 표시:
     ```
     ┌──────────────────────────────────────┐
     │  AI 분석 완료!                        │
     ├──────────────────────────────────────┤
     │  [📝 매수 일지에 추가]  [📊 매도 일지에 추가]  │
     └──────────────────────────────────────┘
     ```

2. **매수 일지에 추가 프로세스**:
   ```
   사용자가 "📝 매수 일지에 추가" 버튼 클릭
      ↓
   사이드바 "매수 일지" 탭으로 자동 전환
      ↓
   분석한 종목 정보 자동 입력:
   - 종목코드: AI 분석한 종목 (예: 005930)
   - 종목명: 삼성전자
   - AI 의견: 투자 전략 섹션 자동 추출
   - 분석 요약: 핵심 투자 포인트 자동 추출
      ↓
   사용자가 추가 정보 입력:
   - 매수 수량
   - 매수 단가
   - 매수일
      ↓
   "💾 저장" 버튼 클릭 → DB 저장
   ```

3. **자동 입력 필드**:
   | 필드 | 자동 입력 내용 | 출처 |
   |------|--------------|------|
   | stock_code | 종목코드 | AI 분석 입력값 |
   | stock_name | 종목명 | AI 분석 입력값 |
   | ai_buy_opinion | 매수 의견 | 투자 전략 섹션 파싱 |
   | ai_report_summary | 분석 요약 | 핵심 투자 포인트 섹션 |
   | buy_current_price | 현재가 | 분석 시점 종가 |
   | buy_close_price | 종가 | pykrx 조회 |

4. **AI 의견 추출 로직**:
   ```python
   def extract_buy_opinion(analysis_result: str) -> str:
       """투자 전략 섹션에서 매수 의견 추출"""

       # 투자 전략 섹션 찾기
       strategy_section = extract_section(analysis_result, '투자 전략 및 의견')

       # 매수 관련 키워드 추출
       buy_keywords = [
           '매수', '진입', '비중 확대', '매수 고려',
           '매수 포인트', '목표가', '상승 여력'
       ]

       # 매수 관련 문장 추출
       buy_sentences = []
       for line in strategy_section.split('\n'):
           if any(keyword in line for keyword in buy_keywords):
               buy_sentences.append(line.strip())

       # 최대 3개 문장으로 제한
       return '\n'.join(buy_sentences[:3])

   def extract_summary(analysis_result: str) -> str:
       """핵심 투자 포인트 섹션 추출"""
       return extract_section(analysis_result, '핵심 투자 포인트')
   ```

5. **매도 일지에 추가 프로세스**:
   ```
   사용자가 "📊 매도 일지에 추가" 버튼 클릭
      ↓
   보유 중인 해당 종목 자동 검색
      ↓
   [Case 1] 보유 중인 기록이 있는 경우:
      → 사이드바 "매도 일지" 탭으로 전환
      → 해당 종목 자동 선택
      → AI 매도 의견 자동 입력
      → 현재가로 매도 단가 자동 입력
      → 사용자가 매도 수량, 일시 입력 후 저장

   [Case 2] 보유 중인 기록이 없는 경우:
      → 경고 메시지 표시:
        "⚠️ 현재 보유 중인 {종목명} 기록이 없습니다.
         먼저 매수 일지에 기록을 추가해주세요."
      → "매수 일지에 추가하기" 버튼 제공
   ```

6. **UI 구현 예시**:
   ```python
   # AI 분석 탭 (personal_analyzer.py)
   if 'last_analysis_result' in st.session_state:
       result = st.session_state['last_analysis_result']

       st.markdown("---")
       st.subheader("📝 매매 일지 바로 작성")

       col1, col2 = st.columns(2)

       with col1:
           if st.button("📝 매수 일지에 추가", use_container_width=True):
               # 매수 일지 데이터 준비
               st.session_state['prefill_buy'] = {
                   'stock_code': result['company_code'],
                   'stock_name': result['company_name'],
                   'ai_opinion': extract_buy_opinion(result['full_report']),
                   'ai_summary': extract_summary(result['full_report']),
                   'current_price': get_current_price(result['company_code'])
               }
               st.session_state['active_sidebar'] = 'buy_journal'
               st.success("✅ 매수 일지로 이동합니다!")
               st.rerun()

       with col2:
           if st.button("📊 매도 일지에 추가", use_container_width=True):
               # 보유 중인 기록 확인
               holdings = get_holdings_by_stock(result['company_code'])

               if holdings:
                   st.session_state['prefill_sell'] = {
                       'stock_code': result['company_code'],
                       'stock_name': result['company_name'],
                       'ai_opinion': extract_sell_opinion(result['full_report']),
                       'current_price': get_current_price(result['company_code'])
                   }
                   st.session_state['active_sidebar'] = 'sell_journal'
                   st.success("✅ 매도 일지로 이동합니다!")
                   st.rerun()
               else:
                   st.warning(f"⚠️ 보유 중인 {result['company_name']} 기록이 없습니다.")
                   if st.button("매수 일지에 먼저 추가하기"):
                       st.session_state['active_sidebar'] = 'buy_journal'
                       st.rerun()
   ```

7. **사이드바 자동 입력 처리**:
   ```python
   # 매수 일지 사이드바
   st.sidebar.header("📝 매수 일지")

   # Prefill 데이터 확인
   prefill = st.session_state.get('prefill_buy', {})

   # 자동 입력된 필드 (수정 가능)
   stock_input = st.sidebar.text_input(
       "종목코드/종목명",
       value=prefill.get('stock_code', ''),
       disabled=bool(prefill)  # prefill 시 비활성화
   )

   # AI 의견 표시 (읽기 전용)
   if prefill.get('ai_opinion'):
       st.sidebar.info(f"🤖 AI 매수 의견:\n{prefill['ai_opinion']}")

   # 현재가 자동 입력
   buy_price = st.sidebar.number_input(
       "매수 단가 (원)",
       value=prefill.get('current_price', 0),
       min_value=1,
       step=100
   )

   # 사용자가 입력해야 하는 필드
   buy_quantity = st.sidebar.number_input("매수 수량", min_value=1, step=1)
   buy_date = st.sidebar.date_input("매수일", value=datetime.now())

   if st.sidebar.button("💾 매수 기록 저장", type="primary"):
       # 저장 로직
       save_buy_record({
           'stock_code': prefill['stock_code'],
           'stock_name': prefill['stock_name'],
           'buy_quantity': buy_quantity,
           'buy_price': buy_price,
           'buy_date': buy_date,
           'ai_buy_opinion': prefill['ai_opinion'],
           'ai_report_summary': prefill['ai_summary'],
           # ...
       })

       # prefill 데이터 초기화
       del st.session_state['prefill_buy']
       st.success("✅ 매수 기록이 저장되었습니다!")
   ```

8. **Prefill 표시 방식**:
   ```
   ┌─────────────────────────────────────────┐
   │  📝 매수 일지                            │
   ├─────────────────────────────────────────┤
   │  🎯 AI 분석 결과 자동 입력됨             │
   │  ┌───────────────────────────────────┐  │
   │  │ 종목: 삼성전자 (005930) 🔒        │  │
   │  │ 현재가: 72,500원                  │  │
   │  └───────────────────────────────────┘  │
   │                                          │
   │  🤖 AI 매수 의견:                        │
   │  • 기술적 반등 시그널 포착               │
   │  • 72,000원 지지선 안정적                │
   │  • 단기 목표가 75,000원                  │
   │                                          │
   │  ✏️ 추가 입력 필요:                      │
   │  매수 수량: [____] 주                    │
   │  매수 단가: [72,500] 원                  │
   │  매수일: [2025-01-09] 📅                │
   │  메모: [________________]                │
   │                                          │
   │  [💾 매수 기록 저장]  [🔄 초기화]        │
   └─────────────────────────────────────────┘
   ```

9. **데이터 흐름**:
   ```
   [AI 분석 탭]
       analyze_stock(code, name)
           ↓
       분석 결과 저장 (st.session_state['last_analysis_result'])
           ↓
       "매수 일지에 추가" 버튼 표시
           ↓
   [사용자 클릭]
       extract_buy_opinion() 실행
       extract_summary() 실행
       get_current_price() 실행
           ↓
       prefill 데이터 생성 (st.session_state['prefill_buy'])
           ↓
       사이드바 탭 전환 (st.session_state['active_sidebar'] = 'buy_journal')
           ↓
       st.rerun()
           ↓
   [매수 일지 사이드바]
       prefill 데이터 확인
           ↓
       자동 입력 필드 표시 (종목, AI 의견, 현재가)
           ↓
       사용자 추가 입력 (수량, 날짜)
           ↓
       "저장" 클릭
           ↓
       DB INSERT
           ↓
       prefill 초기화
   ```

**장점**:
- ✅ 중복 입력 제거 (종목코드, AI 의견 등)
- ✅ 빠른 매매 기록 작성
- ✅ AI 분석 결과와 실제 매매 기록 연동
- ✅ 사용자 편의성 대폭 향상

**주의사항**:
- prefill 데이터는 세션 상태로 관리 (페이지 새로고침 시 초기화)
- 사용자는 언제든지 자동 입력값을 수정 가능
- AI 의견은 참고용이며, 최종 결정은 사용자 책임

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

# 매수 정보 (필수)
buy_quantity = st.sidebar.number_input("매수 수량", min_value=1, step=1)
buy_price = st.sidebar.number_input("매수 단가 (원)", min_value=1, step=100)
buy_date = st.sidebar.date_input("매수일", value=datetime.now())

# AI 분석 요청 (선택사항)
st.sidebar.markdown("---")
st.sidebar.caption("🤖 AI 의견 추가 (선택사항)")

if st.sidebar.button("🤖 AI 분석 요청"):
    # 분석 실행 및 의견 저장
    # ai_buy_opinion, ai_report_summary 필드에 값 입력
    pass

# AI 의견이 있는 경우 표시
if 'ai_opinion' in st.session_state:
    st.sidebar.info(f"AI 의견: {st.session_state['ai_opinion'][:100]}...")

st.sidebar.markdown("---")

# 메모 (선택사항)
notes = st.sidebar.text_area("메모 (선택사항)")

# 저장 버튼
if st.sidebar.button("💾 매수 기록 저장", type="primary"):
    # 저장 로직
    # AI 의견이 없어도 저장 가능 (ai_buy_opinion=NULL)
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

# 매도 정보 (필수)
sell_quantity = st.sidebar.number_input("매도 수량", min_value=1, max_value=selected_holding['quantity'])
sell_price = st.sidebar.number_input("매도 단가 (원)", min_value=1, step=100)
sell_date = st.sidebar.date_input("매도일", value=datetime.now())

# 예상 손익 표시
expected_profit = calculate_profit(selected_holding, sell_quantity, sell_price)
st.sidebar.metric("예상 손익", f"{expected_profit:,}원")

# AI 매도 의견 요청 (선택사항)
st.sidebar.markdown("---")
st.sidebar.caption("🤖 AI 매도 의견 추가 (선택사항)")

if st.sidebar.button("🤖 AI 매도 의견 요청"):
    # 분석 실행 및 매도 의견 저장
    # ai_sell_opinion 필드에 값 입력
    pass

# AI 의견이 있는 경우 표시
if 'ai_sell_opinion' in st.session_state:
    st.sidebar.info(f"AI 매도 의견: {st.session_state['ai_sell_opinion'][:100]}...")

st.sidebar.markdown("---")

# 저장 버튼
if st.sidebar.button("💰 매도 기록 저장", type="primary"):
    # 저장 로직
    # AI 의견이 없어도 저장 가능 (ai_sell_opinion=NULL)
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

### Phase 3: 매수/매도 일지 UI (2일)
- [ ] 매수 일지 사이드바 구현
- [ ] 매도 일지 사이드바 구현
- [ ] AI 분석 연동 (기존 코드 호출)
- [ ] **AI 분석 결과 바로 적용 기능 (F-TJ-007)**:
  - [ ] 분석 완료 후 "매수 일지에 추가" 버튼
  - [ ] 분석 완료 후 "매도 일지에 추가" 버튼
  - [ ] AI 의견 자동 추출 로직 (extract_buy_opinion, extract_sell_opinion)
  - [ ] Prefill 데이터 세션 관리
  - [ ] 사이드바 자동 전환 및 자동 입력
- [ ] 입력 검증 및 에러 핸들링

### Phase 4: 매매 내역 조회 및 수정 (1일)
- [ ] 매매 내역 목록 테이블
- [ ] 필터링 기능
- [ ] 상세 보기 확장
- [ ] **매매 기록 수정 기능 (F-TJ-006)**:
  - [ ] 수정 UI (폼 또는 팝업)
  - [ ] 자동 재계산 로직 (총액, 손익, 보유일수)
  - [ ] 날짜 변경 시 기술적 지표 재계산
  - [ ] 통계 캐시 무효화
  - [ ] 변경 사항 요약 표시
  - [ ] 데이터 검증 (매도수량 ≤ 매수수량 등)
- [ ] 삭제 기능

### Phase 5: 통계 대시보드 (1.5일)
- [ ] 월별 KPI 카드
- [ ] 월별 손익 추이 차트
- [ ] 수익/손실 비율 파이 차트
- [ ] 종목별 TOP 5 차트
- [ ] CSV 다운로드 기능

### Phase 6: 테스트 및 최적화 (0.5일)
- [ ] 전체 기능 통합 테스트
- [ ] 수정 기능 엣지 케이스 테스트
- [ ] AI 바로 적용 기능 플로우 테스트
- [ ] 성능 최적화 (쿼리, 캐싱)
- [ ] UI/UX 개선
- [ ] 문서화

**총 예상 기간**: 6일 (기능 추가로 +1일)

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
