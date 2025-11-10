#!/usr/bin/env python3
"""
Trading Journal Database Module
매매 기록 및 보유 종목 관리를 위한 데이터베이스 모듈
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradingJournalDB:
    """매매 기록 데이터베이스 클래스"""

    def __init__(self, db_path: str = "stock_tracking_db.sqlite"):
        """
        초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._initialize_db()

    def _initialize_db(self):
        """데이터베이스 연결 초기화 및 테이블 생성"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            # 테이블 자동 생성
            self._create_tables()

            logger.info(f"데이터베이스 연결 성공: {self.db_path}")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {str(e)}")
            raise

    def _create_tables(self):
        """필요한 테이블들을 자동으로 생성"""
        # stock_holdings 테이블 생성
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_holdings (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                current_price REAL,
                last_updated TEXT,
                scenario TEXT,
                rsi REAL,
                macd REAL,
                adr REAL
            )
        """)

        # trading_history 테이블 생성
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                sell_price REAL NOT NULL,
                sell_date TEXT NOT NULL,
                profit_rate REAL NOT NULL,
                holding_days INTEGER NOT NULL,
                scenario TEXT
            )
        """)

        self.conn.commit()
        logger.info("데이터베이스 테이블 생성 완료")

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        현재 보유 중인 종목 목록 조회 (미체결 포지션)

        Returns:
            보유 종목 정보 리스트
            [{
                'ticker': '종목코드',
                'company_name': '종목명',
                'buy_price': 매수가,
                'buy_date': '매수일',
                'current_price': 현재가,
                'quantity': 수량 (기본값 1),
                'target_price': 목표가,
                'stop_loss': 손절가,
                'profit_rate': 수익률(%),
                'scenario': 시나리오 정보
            }, ...]
        """
        try:
            # stock_holdings 테이블에서 보유 종목 조회
            self.cursor.execute("""
                SELECT
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    quantity,
                    current_price,
                    rsi,
                    macd,
                    adr,
                    scenario,
                    last_updated
                FROM stock_holdings
                ORDER BY buy_date DESC
            """)

            rows = self.cursor.fetchall()

            if not rows:
                logger.info("보유 중인 종목이 없습니다.")
                return []

            positions = []
            for row in rows:
                # dict로 변환
                row_dict = dict(row)

                # 수익률 계산
                buy_price = row_dict.get('buy_price', 0)
                current_price = row_dict.get('current_price', 0)

                if buy_price > 0 and current_price > 0:
                    profit_rate = ((current_price - buy_price) / buy_price) * 100
                else:
                    profit_rate = 0.0

                # 수량 추가 (기본값 1, 실제로는 각 종목은 포트폴리오의 10% 비중)
                row_dict['quantity'] = 1
                row_dict['profit_rate'] = profit_rate

                positions.append(row_dict)

            logger.info(f"보유 종목 {len(positions)}개 조회 완료")
            return positions

        except Exception as e:
            logger.error(f"매수 기록 조회 실패: {str(e)}")
            # 빈 리스트 반환하여 프로그램이 계속 실행되도록 함
            return []

    def get_position_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        특정 종목의 보유 정보 조회

        Args:
            ticker: 종목 코드

        Returns:
            종목 정보 딕셔너리 또는 None
        """
        try:
            self.cursor.execute("""
                SELECT
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    current_price,
                    target_price,
                    stop_loss,
                    scenario,
                    last_updated
                FROM stock_holdings
                WHERE ticker = ?
            """, (ticker,))

            row = self.cursor.fetchone()

            if not row:
                return None

            row_dict = dict(row)

            # 수익률 계산
            buy_price = row_dict.get('buy_price', 0)
            current_price = row_dict.get('current_price', 0)

            if buy_price > 0 and current_price > 0:
                profit_rate = ((current_price - buy_price) / buy_price) * 100
            else:
                profit_rate = 0.0

            row_dict['quantity'] = 1
            row_dict['profit_rate'] = profit_rate

            return row_dict

        except Exception as e:
            logger.error(f"{ticker} 종목 조회 실패: {str(e)}")
            return None

    def get_trading_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        매매 내역 조회

        Args:
            limit: 조회할 최대 건수

        Returns:
            매매 내역 리스트
        """
        try:
            self.cursor.execute("""
                SELECT
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    sell_price,
                    sell_date,
                    profit_rate,
                    holding_days,
                    scenario
                FROM trading_history
                ORDER BY sell_date DESC
                LIMIT ?
            """, (limit,))

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"매매 내역 조회 실패: {str(e)}")
            return []

    def add_position(
        self,
        ticker: str,
        company_name: str,
        buy_price: float,
        buy_date: str,
        quantity: int = 1,
        rsi: Optional[float] = None,
        macd: Optional[float] = None,
        adr: Optional[float] = None,
        scenario: Optional[str] = None
    ) -> bool:
        """
        매수 기록 추가

        Args:
            ticker: 종목 코드
            company_name: 종목명
            buy_price: 매수가
            buy_date: 매수일 (YYYY-MM-DD HH:MM:SS 형식)
            quantity: 수량 (기본값 1)
            rsi: RSI 지표
            macd: MACD 지표
            adr: ADR 지표
            scenario: 시나리오 정보 (JSON 문자열)

        Returns:
            성공 여부
        """
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO stock_holdings
                (ticker, company_name, buy_price, buy_date, quantity, current_price,
                 rsi, macd, adr, scenario, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                company_name,
                buy_price,
                buy_date,
                quantity,
                buy_price,  # 초기 현재가는 매수가와 동일
                rsi,
                macd,
                adr,
                scenario,
                buy_date
            ))

            self.conn.commit()
            logger.info(f"매수 기록 저장 완료: {company_name}({ticker}) {quantity}주")
            return True

        except Exception as e:
            logger.error(f"매수 기록 저장 실패: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        전체 매매 통계 조회

        Returns:
            통계 정보 딕셔너리
        """
        try:
            # 현재 보유 종목 수
            self.cursor.execute("SELECT COUNT(*) FROM stock_holdings")
            open_positions_count = self.cursor.fetchone()[0]

            # 총 거래 건수
            self.cursor.execute("SELECT COUNT(*) FROM trading_history")
            total_trades = self.cursor.fetchone()[0]

            # 수익 거래 건수
            self.cursor.execute("SELECT COUNT(*) FROM trading_history WHERE profit_rate > 0")
            profitable_trades = self.cursor.fetchone()[0]

            # 평균 수익률
            self.cursor.execute("SELECT AVG(profit_rate) FROM trading_history")
            avg_profit_rate = self.cursor.fetchone()[0] or 0

            # 총 누적 수익률
            self.cursor.execute("SELECT SUM(profit_rate) FROM trading_history")
            total_profit_rate = self.cursor.fetchone()[0] or 0

            # 승률 계산
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                'open_positions_count': open_positions_count,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'losing_trades': total_trades - profitable_trades,
                'win_rate': win_rate,
                'avg_profit_rate': avg_profit_rate,
                'total_profit_rate': total_profit_rate
            }

        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {}

    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info("데이터베이스 연결 종료")

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()


# 편의 함수
def get_open_positions(db_path: str = "stock_tracking_db.sqlite") -> List[Dict[str, Any]]:
    """
    보유 종목 목록을 간편하게 조회하는 함수

    Args:
        db_path: 데이터베이스 파일 경로

    Returns:
        보유 종목 정보 리스트
    """
    with TradingJournalDB(db_path) as db:
        return db.get_open_positions()


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)

    with TradingJournalDB() as db:
        # 보유 종목 조회
        positions = db.get_open_positions()
        print(f"\n보유 종목 {len(positions)}개:")
        for pos in positions:
            print(f"  - {pos['company_name']}({pos['ticker']}): "
                  f"{pos['current_price']:,.0f}원 (수익률: {pos['profit_rate']:+.2f}%)")

        # 통계 조회
        stats = db.get_statistics()
        print(f"\n매매 통계:")
        print(f"  - 보유 종목: {stats['open_positions_count']}개")
        print(f"  - 총 거래: {stats['total_trades']}건")
        print(f"  - 승률: {stats['win_rate']:.2f}%")
        print(f"  - 평균 수익률: {stats['avg_profit_rate']:+.2f}%")
        print(f"  - 누적 수익률: {stats['total_profit_rate']:+.2f}%")
