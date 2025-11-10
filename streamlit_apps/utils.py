"""
유틸리티 함수

⚠️ 주의: 기존 코드를 수정하지 않는 새로운 헬퍼 함수들입니다.
"""

from typing import Tuple, Optional
from datetime import datetime


def parse_stock_input(user_input: str) -> Tuple[Optional[str], Optional[str]]:
    """
    사용자 입력 파싱

    Args:
        user_input: 종목코드 또는 종목명

    Returns:
        (종목코드, 종목명) 튜플
    """
    try:
        from pykrx import stock as pykrx_stock

        user_input = user_input.strip()

        # 종목코드로 검색 (6자리 숫자)
        if user_input.isdigit() and len(user_input) == 6:
            try:
                name = pykrx_stock.get_market_ticker_name(user_input)
                if name:
                    return (user_input, name)
            except:
                pass

        # 종목명으로 검색
        try:
            tickers = pykrx_stock.get_market_ticker_list(market="ALL")
            for ticker in tickers:
                ticker_name = pykrx_stock.get_market_ticker_name(ticker)
                if user_input in ticker_name:
                    return (ticker, ticker_name)
        except:
            pass

        return (None, None)

    except ImportError:
        # pykrx가 없는 경우
        return (None, None)


def format_currency(value: int) -> str:
    """
    금액 포맷팅

    Args:
        value: 금액

    Returns:
        포맷된 문자열 (예: "72,500원")
    """
    if value == 0:
        return "0원"
    return f"{value:,}원"


def format_percentage(value: float) -> str:
    """
    퍼센트 포맷팅

    Args:
        value: 퍼센트 값

    Returns:
        포맷된 문자열 (예: "+1.23%")
    """
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    else:
        return "0.00%"


def get_current_timestamp() -> str:
    """
    현재 타임스탬프 반환

    Returns:
        YYYYMMDD_HHMMSS 형식 문자열
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")
