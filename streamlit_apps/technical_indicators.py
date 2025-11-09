"""
기술적 지표 계산 모듈

pykrx를 사용하여 한국 주식의 기술적 지표를 계산합니다.
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- MA (Moving Average)
- 거래량 지표
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import numpy as np
import logging
from functools import lru_cache

from pykrx import stock

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
        """
        RSI (Relative Strength Index) 계산

        Args:
            prices: 종가 시리즈
            period: 기간 (기본 14일)

        Returns:
            Optional[float]: RSI 값 (0~100), 계산 불가 시 None
        """
        try:
            if len(prices) < period + 1:
                return None

            # 가격 변화량 계산
            delta = prices.diff()

            # 상승분과 하락분 분리
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 평균 상승/하락 계산 (EMA 방식)
            avg_gain = gain.ewm(span=period, adjust=False).mean()
            avg_loss = loss.ewm(span=period, adjust=False).mean()

            # RS와 RSI 계산
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return round(float(rsi.iloc[-1]), 2)

        except Exception as e:
            logger.error(f"RSI 계산 실패: {e}")
            return None

    @staticmethod
    def calculate_macd(prices: pd.Series) -> Dict[str, Optional[float]]:
        """
        MACD (Moving Average Convergence Divergence) 계산

        Args:
            prices: 종가 시리즈

        Returns:
            Dict: {
                'macd': MACD 값,
                'signal': Signal Line,
                'histogram': Histogram
            }
        """
        try:
            if len(prices) < 35:  # 26 + 9
                return {'macd': None, 'signal': None, 'histogram': None}

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
                'macd': round(float(macd.iloc[-1]), 2),
                'signal': round(float(signal.iloc[-1]), 2),
                'histogram': round(float(histogram.iloc[-1]), 2)
            }

        except Exception as e:
            logger.error(f"MACD 계산 실패: {e}")
            return {'macd': None, 'signal': None, 'histogram': None}

    @staticmethod
    def calculate_ma(prices: pd.Series, period: int) -> Optional[float]:
        """
        이동평균 (Moving Average) 계산

        Args:
            prices: 종가 시리즈
            period: 기간

        Returns:
            Optional[float]: 이동평균 값, 계산 불가 시 None
        """
        try:
            if len(prices) < period:
                return None

            ma = prices.rolling(window=period).mean()
            return round(float(ma.iloc[-1]), 2)

        except Exception as e:
            logger.error(f"MA({period}) 계산 실패: {e}")
            return None

    @staticmethod
    def calculate_volume_indicators(df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        거래량 지표 계산

        Args:
            df: OHLCV 데이터프레임

        Returns:
            Dict: {
                'volume': 당일 거래량,
                'volume_ma_20': 20일 평균 거래량
            }
        """
        try:
            volume = df['거래량'].iloc[-1] if '거래량' in df.columns else None
            volume_ma_20 = df['거래량'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None

            return {
                'volume': int(volume) if volume else None,
                'volume_ma_20': round(float(volume_ma_20), 2) if volume_ma_20 else None
            }

        except Exception as e:
            logger.error(f"거래량 지표 계산 실패: {e}")
            return {'volume': None, 'volume_ma_20': None}

    @staticmethod
    @lru_cache(maxsize=100)
    def get_stock_data(stock_code: str, date: str, days: int = 150) -> Optional[pd.DataFrame]:
        """
        pykrx를 사용하여 주식 데이터 조회 (캐싱)

        Args:
            stock_code: 종목 코드 (예: "005930")
            date: 기준일 (YYYYMMDD)
            days: 조회할 과거 일수 (기본 150일)

        Returns:
            Optional[pd.DataFrame]: OHLCV 데이터프레임 또는 None
        """
        try:
            # 시작일 계산
            end_date = datetime.strptime(date, "%Y%m%d")
            start_date = end_date - timedelta(days=days)

            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = date

            # pykrx로 데이터 조회
            df = stock.get_market_ohlcv_by_date(
                fromdate=start_date_str,
                todate=end_date_str,
                ticker=stock_code
            )

            if df.empty:
                logger.warning(f"데이터가 없습니다: {stock_code}, {date}")
                return None

            return df

        except Exception as e:
            logger.error(f"주식 데이터 조회 실패: {stock_code}, {date} - {e}")
            return None

    @staticmethod
    def get_current_price(stock_code: str, date: Optional[str] = None) -> Optional[int]:
        """
        현재가 또는 특정일 종가 조회

        Args:
            stock_code: 종목 코드
            date: 날짜 (YYYYMMDD), None이면 최근 영업일

        Returns:
            Optional[int]: 종가 또는 None
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            # 해당 날짜 데이터 조회
            for i in range(10):  # 최대 10일 전까지 확인 (휴장일 대응)
                check_date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=i)).strftime("%Y%m%d")

                df = stock.get_market_ohlcv_by_date(
                    fromdate=check_date,
                    todate=check_date,
                    ticker=stock_code
                )

                if not df.empty:
                    return int(df.iloc[-1]['종가'])

            logger.warning(f"현재가 조회 실패: {stock_code}, {date}")
            return None

        except Exception as e:
            logger.error(f"현재가 조회 중 오류: {stock_code}, {date} - {e}")
            return None

    @classmethod
    def get_all_indicators(cls, stock_code: str, date: str) -> Dict:
        """
        모든 기술적 지표 계산

        Args:
            stock_code: 종목 코드
            date: 기준일 (YYYYMMDD)

        Returns:
            Dict: 모든 지표가 포함된 딕셔너리
        """
        try:
            # 데이터 가져오기 (150일)
            df = cls.get_stock_data(stock_code, date, days=150)

            if df is None or df.empty:
                return cls._get_empty_indicators()

            prices = df['종가']

            # 모든 지표 계산
            indicators = {
                # RSI
                'rsi_14': cls.calculate_rsi(prices, 14),
                'rsi_16': cls.calculate_rsi(prices, 16),

                # MACD
                'macd_value': None,
                'macd_signal': None,
                'macd_histogram': None,

                # 이동평균
                'ma_20': cls.calculate_ma(prices, 20),
                'ma_60': cls.calculate_ma(prices, 60),
                'ma_90': cls.calculate_ma(prices, 90),
                'ma_120': cls.calculate_ma(prices, 120),

                # 거래량
                'volume': None,
                'volume_ma_20': None,

                # 종가
                'close_price': int(prices.iloc[-1]) if len(prices) > 0 else None
            }

            # MACD 계산
            macd_result = cls.calculate_macd(prices)
            indicators['macd_value'] = macd_result['macd']
            indicators['macd_signal'] = macd_result['signal']
            indicators['macd_histogram'] = macd_result['histogram']

            # 거래량 계산
            volume_result = cls.calculate_volume_indicators(df)
            indicators['volume'] = volume_result['volume']
            indicators['volume_ma_20'] = volume_result['volume_ma_20']

            logger.info(f"지표 계산 완료: {stock_code}, {date}")
            return indicators

        except Exception as e:
            logger.error(f"지표 계산 중 오류: {stock_code}, {date} - {e}")
            return cls._get_empty_indicators()

    @staticmethod
    def _get_empty_indicators() -> Dict:
        """빈 지표 딕셔너리 반환"""
        return {
            'rsi_14': None,
            'rsi_16': None,
            'macd_value': None,
            'macd_signal': None,
            'macd_histogram': None,
            'ma_20': None,
            'ma_60': None,
            'ma_90': None,
            'ma_120': None,
            'volume': None,
            'volume_ma_20': None,
            'close_price': None
        }


# 편의 함수
def get_indicators_for_buy(stock_code: str, buy_date: str) -> Dict:
    """
    매수 시점 지표 조회

    Args:
        stock_code: 종목 코드
        buy_date: 매수일 (YYYYMMDD 또는 YYYY-MM-DD)

    Returns:
        Dict: buy_ 접두사가 붙은 지표 딕셔너리
    """
    # 날짜 형식 통일
    if '-' in buy_date:
        buy_date = buy_date.replace('-', '')

    indicators = TechnicalIndicators.get_all_indicators(stock_code, buy_date)

    # buy_ 접두사 추가
    return {f'buy_{k}': v for k, v in indicators.items() if k != 'close_price'}


def get_indicators_for_sell(stock_code: str, sell_date: str) -> Dict:
    """
    매도 시점 지표 조회

    Args:
        stock_code: 종목 코드
        sell_date: 매도일 (YYYYMMDD 또는 YYYY-MM-DD)

    Returns:
        Dict: sell_ 접두사가 붙은 지표 딕셔너리
    """
    # 날짜 형식 통일
    if '-' in sell_date:
        sell_date = sell_date.replace('-', '')

    indicators = TechnicalIndicators.get_all_indicators(stock_code, sell_date)

    # sell_ 접두사 추가
    return {f'sell_{k}': v for k, v in indicators.items() if k != 'close_price'}
