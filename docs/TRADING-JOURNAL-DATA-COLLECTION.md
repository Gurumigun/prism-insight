# 매매 일지 데이터 수집 방식 설명서

## 1. 데이터 소스 개요

### 1.1 사용 라이브러리
- **pykrx**: 한국거래소(KRX) 공식 데이터 (무료, API 키 불필요)
  - KOSPI, KOSDAQ 전 종목 지원
  - 주가, 거래량, 시가총액, 재무제표 등

### 1.2 데이터 수집 시점
```
매수 버튼 클릭
    ↓
1. 현재가/종가 조회 (pykrx)
    ↓
2. 과거 60~120일 데이터 조회
    ↓
3. 기술적 지표 계산 (pandas/numpy)
    ↓
4. DB 저장
```

---

## 2. 수집 데이터 상세

### 2.1 기본 가격 데이터 (pykrx)

#### 함수: `get_market_ohlcv_by_date()`
```python
from pykrx import stock

# 예시: 삼성전자 최근 120일 데이터
df = stock.get_market_ohlcv_by_date(
    fromdate="20240101",  # 시작일
    todate="20250109",    # 종료일
    ticker="005930"       # 종목코드
)

# 결과 데이터프레임:
#              시가    고가    저가    종가      거래량
# 2024-01-01  71000  72500  70500  72000  15234567
# 2024-01-02  72500  73000  71500  72800  12345678
# ...
```

**수집 항목**:
- 시가 (Open)
- 고가 (High)
- 저가 (Low)
- 종가 (Close) ← **매수/매도 가격 기준**
- 거래량 (Volume)

**매매 일지 활용**:
- `buy_close_price`: 매수일의 종가
- `sell_close_price`: 매도일의 종가
- `buy_current_price`: 사용자가 입력한 실제 체결가 (또는 최신 종가)

---

### 2.2 현재가 조회 방식

#### 방법 1: 최신 종가 사용 (권장)
```python
from pykrx import stock
from datetime import datetime

def get_current_price(stock_code: str) -> int:
    """당일 종가 조회 (장 마감 후) 또는 전일 종가"""
    today = datetime.now().strftime("%Y%m%d")

    # 당일 데이터 조회
    df = stock.get_market_ohlcv_by_date(
        fromdate=today,
        todate=today,
        ticker=stock_code
    )

    if not df.empty:
        return df.iloc[-1]['종가']  # 당일 종가
    else:
        # 장 시작 전이면 전일 종가 반환
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_date(
            fromdate=yesterday,
            todate=yesterday,
            ticker=stock_code
        )
        return df.iloc[-1]['종가']
```

#### 방법 2: 사용자 입력 (체결가)
- 사용자가 실제 매수/매도한 가격을 직접 입력
- 더 정확한 손익 계산 가능

**매매 일지 UI**:
```
매수 단가: [72,500원]  ← 사용자 입력
         또는
         [최신 종가 자동 입력 버튼]
```

---

### 2.3 기술적 지표 계산

#### 2.3.1 필요한 데이터 기간
| 지표 | 최소 필요 기간 | 권장 기간 |
|------|---------------|----------|
| RSI(14) | 14일 | 30일 |
| RSI(16) | 16일 | 30일 |
| MACD(12,26,9) | 35일 | 60일 |
| MA(20) | 20일 | 40일 |
| MA(60) | 60일 | 80일 |
| MA(90) | 90일 | 110일 |
| MA(120) | 120일 | 140일 |

→ **권장 조회 기간: 150일** (충분한 여유 확보)

#### 2.3.2 RSI 계산 (Relative Strength Index)
```python
def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    RSI 계산

    Args:
        prices: 종가 시리즈 (pandas.Series)
        period: 기간 (기본 14일)

    Returns:
        float: RSI 값 (0~100)
    """
    delta = prices.diff()

    # 상승분과 하락분 분리
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 평균 상승/하락 계산
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # RS와 RSI 계산
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]  # 최신값 반환
```

**의미**:
- RSI > 70: 과매수 (매도 신호)
- RSI < 30: 과매도 (매수 신호)

#### 2.3.3 MACD 계산
```python
def calculate_macd(prices: pd.Series) -> dict:
    """
    MACD 계산

    Returns:
        dict: {
            'macd': MACD 값,
            'signal': Signal Line,
            'histogram': Histogram
        }
    """
    # EMA 계산
    ema_12 = prices.ewm(span=12, adjust=False).mean()
    ema_26 = prices.ewm(span=26, adjust=False).mean()

    # MACD Line
    macd = ema_12 - ema_26

    # Signal Line (MACD의 9일 EMA)
    signal = macd.ewm(span=9, adjust=False).mean()

    # Histogram
    histogram = macd - signal

    return {
        'macd': macd.iloc[-1],
        'signal': signal.iloc[-1],
        'histogram': histogram.iloc[-1]
    }
```

**의미**:
- MACD > Signal: 상승 추세 (매수 신호)
- MACD < Signal: 하락 추세 (매도 신호)
- Histogram: MACD와 Signal의 차이 (모멘텀)

#### 2.3.4 이동평균선 (Moving Average)
```python
def calculate_ma(prices: pd.Series, period: int) -> float:
    """이동평균 계산"""
    return prices.rolling(window=period).mean().iloc[-1]
```

**의미**:
- 현재가 > MA: 상승 추세
- 현재가 < MA: 하락 추세
- 골든크로스 (MA20 > MA60): 강세 신호
- 데드크로스 (MA20 < MA60): 약세 신호

#### 2.3.5 거래량 지표
```python
def calculate_volume_indicators(df: pd.DataFrame) -> dict:
    """거래량 지표 계산"""
    return {
        'volume': df['거래량'].iloc[-1],  # 당일 거래량
        'volume_ma_20': df['거래량'].rolling(window=20).mean().iloc[-1]  # 20일 평균 거래량
    }
```

**의미**:
- 거래량 > 평균 거래량: 강한 매매세
- 거래량 급증 + 상승: 상승 모멘텀 강화

---

## 3. 실제 구현 예시

### 3.1 매수 시점 데이터 수집
```python
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd

def collect_buy_data(stock_code: str, buy_date: str, buy_price: int, quantity: int):
    """
    매수 시점 데이터 수집

    Args:
        stock_code: 종목코드 (예: "005930")
        buy_date: 매수일 (YYYYMMDD)
        buy_price: 매수 단가
        quantity: 매수 수량
    """
    # 1. 과거 150일 데이터 조회
    start_date = (datetime.strptime(buy_date, "%Y%m%d") - timedelta(days=150)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(
        fromdate=start_date,
        todate=buy_date,
        ticker=stock_code
    )

    # 2. 매수일 종가
    buy_close_price = df.loc[buy_date, '종가'] if buy_date in df.index else None

    # 3. 기술적 지표 계산
    prices = df['종가']

    indicators = {
        # RSI
        'buy_rsi_14': calculate_rsi(prices, 14),
        'buy_rsi_16': calculate_rsi(prices, 16),

        # MACD
        **{f'buy_{k}': v for k, v in calculate_macd(prices).items()},

        # 이동평균
        'buy_ma_20': calculate_ma(prices, 20),
        'buy_ma_60': calculate_ma(prices, 60),
        'buy_ma_90': calculate_ma(prices, 90),
        'buy_ma_120': calculate_ma(prices, 120),

        # 거래량
        'buy_volume': df.loc[buy_date, '거래량'],
        'buy_volume_ma_20': df['거래량'].rolling(window=20).mean().iloc[-1]
    }

    # 4. DB 저장 데이터 구성
    record = {
        'stock_code': stock_code,
        'buy_quantity': quantity,
        'buy_price': buy_price,
        'buy_amount': buy_price * quantity,
        'buy_date': buy_date,
        'buy_current_price': buy_price,  # 사용자 입력값
        'buy_close_price': buy_close_price,  # pykrx 종가
        **indicators  # 기술적 지표 병합
    }

    return record
```

### 3.2 매도 시점 데이터 수집
```python
def collect_sell_data(stock_code: str, sell_date: str, sell_price: int,
                     buy_record: dict):
    """
    매도 시점 데이터 수집

    Args:
        stock_code: 종목코드
        sell_date: 매도일
        sell_price: 매도 단가
        buy_record: 기존 매수 기록
    """
    # 1. 매도일 기준 150일 데이터 조회
    start_date = (datetime.strptime(sell_date, "%Y%m%d") - timedelta(days=150)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(
        fromdate=start_date,
        todate=sell_date,
        ticker=stock_code
    )

    # 2. 매도일 종가
    sell_close_price = df.loc[sell_date, '종가']

    # 3. 기술적 지표 계산 (매도 시점)
    prices = df['종가']

    sell_indicators = {
        'sell_rsi_14': calculate_rsi(prices, 14),
        'sell_rsi_16': calculate_rsi(prices, 16),
        **{f'sell_{k}': v for k, v in calculate_macd(prices).items()},
        'sell_ma_20': calculate_ma(prices, 20),
        'sell_ma_60': calculate_ma(prices, 60),
        'sell_ma_90': calculate_ma(prices, 90),
        'sell_ma_120': calculate_ma(prices, 120),
        'sell_volume': df.loc[sell_date, '거래량'],
        'sell_volume_ma_20': df['거래량'].rolling(window=20).mean().iloc[-1]
    }

    # 4. 손익 계산
    buy_price = buy_record['buy_price']
    quantity = buy_record['buy_quantity']

    profit_amount = (sell_price - buy_price) * quantity
    profit_rate = ((sell_price - buy_price) / buy_price) * 100

    buy_date = datetime.strptime(buy_record['buy_date'], "%Y%m%d")
    sell_date_obj = datetime.strptime(sell_date, "%Y%m%d")
    holding_days = (sell_date_obj - buy_date).days

    # 5. 업데이트 데이터
    update_data = {
        'sell_price': sell_price,
        'sell_amount': sell_price * quantity,
        'sell_date': sell_date,
        'sell_current_price': sell_price,
        'sell_close_price': sell_close_price,
        'profit_amount': profit_amount,
        'profit_rate': profit_rate,
        'holding_days': holding_days,
        **sell_indicators
    }

    return update_data
```

---

## 4. 데이터 수집 최적화

### 4.1 캐싱 전략
```python
import functools
from datetime import datetime

@functools.lru_cache(maxsize=100)
def get_cached_ohlcv(stock_code: str, date: str):
    """pykrx 호출 결과 캐싱 (동일 요청 중복 방지)"""
    start_date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=150)).strftime("%Y%m%d")
    return stock.get_market_ohlcv_by_date(start_date, date, stock_code)
```

### 4.2 에러 처리
```python
def safe_get_price(stock_code: str, date: str) -> int:
    """안전한 가격 조회 (휴장일 대응)"""
    try:
        df = stock.get_market_ohlcv_by_date(date, date, stock_code)
        if not df.empty:
            return df.iloc[-1]['종가']
        else:
            # 휴장일인 경우 이전 영업일 조회
            for i in range(1, 10):  # 최대 10일 전까지
                prev_date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=i)).strftime("%Y%m%d")
                df = stock.get_market_ohlcv_by_date(prev_date, prev_date, stock_code)
                if not df.empty:
                    return df.iloc[-1]['종가']
    except Exception as e:
        print(f"가격 조회 실패: {e}")
        return None
```

---

## 5. 데이터 흐름 다이어그램

```
[사용자]
   │
   ├─ 매수 버튼 클릭
   │     │
   │     ├─ 종목코드: 005930
   │     ├─ 매수가: 72,500원
   │     ├─ 수량: 10주
   │     └─ 날짜: 2025-01-09
   │
   ↓
[Streamlit UI]
   │
   ↓
[technical_indicators.py]
   │
   ├─ pykrx.stock.get_market_ohlcv_by_date()
   │     │
   │     ├─ 2024-08-12 ~ 2025-01-09 (150일)
   │     └─ 결과: DataFrame (시가, 고가, 저가, 종가, 거래량)
   │
   ├─ calculate_rsi(종가, 14) → 62.5
   ├─ calculate_rsi(종가, 16) → 61.8
   ├─ calculate_macd(종가) → {macd: 1250, signal: 980, histogram: 270}
   ├─ calculate_ma(종가, 20) → 71,200
   ├─ calculate_ma(종가, 60) → 69,500
   ├─ calculate_ma(종가, 90) → 68,800
   ├─ calculate_ma(종가, 120) → 67,500
   └─ calculate_volume() → {volume: 15,234,567, ma_20: 12,500,000}
   │
   ↓
[db_manager.py]
   │
   └─ INSERT INTO trading_records
         stock_code = "005930"
         buy_price = 72500
         buy_quantity = 10
         buy_rsi_14 = 62.5
         buy_macd_value = 1250
         ...
   │
   ↓
[SQLite DB]
   └─ trading_journal.db
```

---

## 6. FAQ

### Q1: 장 시작 전에 매수 기록하면 어떻게 되나요?
A: 전일 종가를 사용하거나, 사용자가 입력한 가격을 `buy_current_price`로 저장합니다. `buy_close_price`는 NULL 또는 전일 종가로 설정됩니다.

### Q2: 휴장일에 데이터를 조회하면?
A: pykrx는 빈 데이터프레임을 반환합니다. 이 경우 이전 영업일을 찾아 재시도합니다 (최대 10일 전까지).

### Q3: 기술적 지표 계산 시간은?
A: 약 1~2초 소요됩니다.
- pykrx API 호출: 0.5~1초
- pandas 계산: 0.5~1초

### Q4: 여러 종목을 동시에 기록하면?
A: 각 종목별로 독립적으로 pykrx 호출하므로 N개 종목 = N × 2초 소요됩니다. 캐싱으로 중복 호출 방지 가능합니다.

### Q5: pykrx가 없는 해외 주식은?
A: 현재 버전은 KOSPI/KOSDAQ만 지원합니다. 향후 yfinance를 추가하여 해외 주식 지원 예정입니다.

---

## 7. 다음 단계

1. **`technical_indicators.py` 구현** → RSI, MACD, MA 계산 함수
2. **`db_manager.py` 구현** → 매수/매도 데이터 저장
3. **Streamlit UI 연동** → 사용자 입력 → 데이터 수집 → DB 저장

---

## 참고 자료
- [pykrx 공식 문서](https://github.com/sharebook-kr/pykrx)
- [RSI 계산 방법](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD 계산 방법](https://www.investopedia.com/terms/m/macd.asp)
