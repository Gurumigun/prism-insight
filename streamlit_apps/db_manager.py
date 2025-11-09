"""
매매 일지 데이터베이스 관리 모듈

SQLite를 사용한 로컬 데이터베이스 관리
- trading_records: 매매 기록
- monthly_stats: 월별 통계 캐시
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TradingJournalDB:
    """매매 일지 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "streamlit_apps/trading_journal.db"):
        """
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn

    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 매매 기록 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- 주식 기본 정보
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,

                    -- 매수 정보
                    buy_quantity INTEGER NOT NULL,
                    buy_price REAL NOT NULL,
                    buy_amount REAL NOT NULL,
                    buy_date DATETIME NOT NULL,
                    buy_current_price REAL,
                    buy_close_price REAL,

                    -- 매도 정보
                    sell_quantity INTEGER,
                    sell_price REAL,
                    sell_amount REAL,
                    sell_date DATETIME,
                    sell_current_price REAL,
                    sell_close_price REAL,

                    -- 손익 정보
                    profit_amount REAL,
                    profit_rate REAL,
                    holding_days INTEGER,

                    -- AI 분석 정보
                    ai_buy_opinion TEXT,
                    ai_sell_opinion TEXT,
                    ai_report_summary TEXT,

                    -- 기술적 지표 (매수 시점)
                    buy_rsi_14 REAL,
                    buy_rsi_16 REAL,
                    buy_macd_value REAL,
                    buy_macd_signal REAL,
                    buy_macd_histogram REAL,
                    buy_ma_20 REAL,
                    buy_ma_60 REAL,
                    buy_ma_90 REAL,
                    buy_ma_120 REAL,
                    buy_volume REAL,
                    buy_volume_ma_20 REAL,

                    -- 기술적 지표 (매도 시점)
                    sell_rsi_14 REAL,
                    sell_rsi_16 REAL,
                    sell_macd_value REAL,
                    sell_macd_signal REAL,
                    sell_macd_histogram REAL,
                    sell_ma_20 REAL,
                    sell_ma_60 REAL,
                    sell_ma_90 REAL,
                    sell_ma_120 REAL,
                    sell_volume REAL,
                    sell_volume_ma_20 REAL,

                    -- 메타 정보
                    notes TEXT,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_code
                ON trading_records(stock_code)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_buy_date
                ON trading_records(buy_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sell_date
                ON trading_records(sell_date)
            """)

            # 월별 통계 캐시 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year_month TEXT NOT NULL UNIQUE,

                    -- 손익 통계
                    total_profit REAL,
                    total_loss REAL,
                    net_profit REAL,
                    avg_profit_rate REAL,

                    -- 거래 통계
                    total_trades INTEGER,
                    buy_count INTEGER,
                    sell_count INTEGER,
                    holding_count INTEGER,

                    -- 승률 통계
                    win_count INTEGER,
                    loss_count INTEGER,
                    win_rate REAL,

                    -- 메타 정보
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info(f"데이터베이스 초기화 완료: {self.db_path}")

        except Exception as e:
            conn.rollback()
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
        finally:
            conn.close()

    def add_buy_record(self, record: Dict) -> int:
        """
        매수 기록 추가

        Args:
            record: 매수 기록 딕셔너리
                - stock_code (필수)
                - stock_name (필수)
                - buy_quantity (필수)
                - buy_price (필수)
                - buy_date (필수)
                - ai_buy_opinion (선택)
                - ai_report_summary (선택)
                - 기타 필드들...

        Returns:
            int: 생성된 레코드 ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 매수 총액 계산
            record['buy_amount'] = record['buy_price'] * record['buy_quantity']

            # 필드 목록 생성
            fields = []
            placeholders = []
            values = []

            for key, value in record.items():
                if value is not None:
                    fields.append(key)
                    placeholders.append('?')
                    values.append(value)

            query = f"""
                INSERT INTO trading_records ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
            """

            cursor.execute(query, values)
            conn.commit()

            record_id = cursor.lastrowid
            logger.info(f"매수 기록 추가 완료: ID={record_id}, {record['stock_name']}")

            return record_id

        except Exception as e:
            conn.rollback()
            logger.error(f"매수 기록 추가 실패: {e}")
            raise
        finally:
            conn.close()

    def update_sell_record(self, record_id: int, sell_data: Dict) -> bool:
        """
        매도 정보 업데이트

        Args:
            record_id: 매수 기록 ID
            sell_data: 매도 정보 딕셔너리
                - sell_quantity (필수)
                - sell_price (필수)
                - sell_date (필수)
                - ai_sell_opinion (선택)
                - 기타 필드들...

        Returns:
            bool: 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 기존 매수 기록 조회
            cursor.execute("""
                SELECT buy_price, buy_date
                FROM trading_records
                WHERE id = ?
            """, (record_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"매수 기록을 찾을 수 없습니다: ID={record_id}")

            buy_price = row['buy_price']
            buy_date = datetime.fromisoformat(row['buy_date'])

            # 매도 총액 계산
            sell_data['sell_amount'] = sell_data['sell_price'] * sell_data['sell_quantity']

            # 손익 계산
            sell_data['profit_amount'] = (sell_data['sell_price'] - buy_price) * sell_data['sell_quantity']
            sell_data['profit_rate'] = ((sell_data['sell_price'] - buy_price) / buy_price) * 100

            # 보유 일수 계산
            sell_date = datetime.fromisoformat(sell_data['sell_date']) if isinstance(sell_data['sell_date'], str) else sell_data['sell_date']
            sell_data['holding_days'] = (sell_date - buy_date).days

            # updated_at 갱신
            sell_data['updated_at'] = datetime.now().isoformat()

            # UPDATE 쿼리 생성
            updates = []
            values = []

            for key, value in sell_data.items():
                updates.append(f"{key} = ?")
                values.append(value)

            values.append(record_id)

            query = f"""
                UPDATE trading_records
                SET {', '.join(updates)}
                WHERE id = ?
            """

            cursor.execute(query, values)
            conn.commit()

            logger.info(f"매도 기록 업데이트 완료: ID={record_id}")

            # 월별 통계 캐시 무효화
            self._invalidate_monthly_stats_cache()

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"매도 기록 업데이트 실패: {e}")
            raise
        finally:
            conn.close()

    def get_holdings(self) -> List[Dict]:
        """
        보유 중인 종목 조회 (매도일이 NULL인 레코드)

        Returns:
            List[Dict]: 보유 종목 목록
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT *
                FROM trading_records
                WHERE sell_date IS NULL
                ORDER BY buy_date DESC
            """)

            holdings = [dict(row) for row in cursor.fetchall()]
            return holdings

        except Exception as e:
            logger.error(f"보유 종목 조회 실패: {e}")
            raise
        finally:
            conn.close()

    def get_holdings_by_stock(self, stock_code: str) -> List[Dict]:
        """
        특정 종목의 보유 기록 조회

        Args:
            stock_code: 종목 코드

        Returns:
            List[Dict]: 보유 기록 목록
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT *
                FROM trading_records
                WHERE stock_code = ? AND sell_date IS NULL
                ORDER BY buy_date DESC
            """, (stock_code,))

            holdings = [dict(row) for row in cursor.fetchall()]
            return holdings

        except Exception as e:
            logger.error(f"특정 종목 보유 기록 조회 실패: {e}")
            raise
        finally:
            conn.close()

    def get_all_records(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        전체 매매 내역 조회

        Args:
            filters: 필터 조건 딕셔너리
                - start_date: 시작일
                - end_date: 종료일
                - stock_code: 종목코드
                - status: 'holding' | 'sold' | 'all'
                - profit_type: 'profit' | 'loss' | 'all'

        Returns:
            List[Dict]: 매매 내역 목록
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM trading_records WHERE 1=1"
            params = []

            if filters:
                # 기간 필터
                if filters.get('start_date'):
                    query += " AND buy_date >= ?"
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    query += " AND buy_date <= ?"
                    params.append(filters['end_date'])

                # 종목 필터
                if filters.get('stock_code'):
                    query += " AND stock_code = ?"
                    params.append(filters['stock_code'])

                # 상태 필터
                if filters.get('status') == 'holding':
                    query += " AND sell_date IS NULL"
                elif filters.get('status') == 'sold':
                    query += " AND sell_date IS NOT NULL"

                # 수익 구분 필터
                if filters.get('profit_type') == 'profit':
                    query += " AND profit_amount > 0"
                elif filters.get('profit_type') == 'loss':
                    query += " AND profit_amount < 0"

            query += " ORDER BY buy_date DESC"

            cursor.execute(query, params)

            records = [dict(row) for row in cursor.fetchall()]
            return records

        except Exception as e:
            logger.error(f"매매 내역 조회 실패: {e}")
            raise
        finally:
            conn.close()

    def update_record(self, record_id: int, updated_data: Dict) -> Tuple[bool, Dict]:
        """
        매매 기록 수정 (F-TJ-006)

        Args:
            record_id: 레코드 ID
            updated_data: 수정할 데이터 딕셔너리

        Returns:
            Tuple[bool, Dict]: (성공 여부, 변경 사항 요약)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 기존 레코드 조회
            cursor.execute("SELECT * FROM trading_records WHERE id = ?", (record_id,))
            old_record = dict(cursor.fetchone())

            changes = {}

            # 1. 매수/매도 총액 재계산
            if 'buy_price' in updated_data or 'buy_quantity' in updated_data:
                new_buy_price = updated_data.get('buy_price', old_record['buy_price'])
                new_buy_quantity = updated_data.get('buy_quantity', old_record['buy_quantity'])
                updated_data['buy_amount'] = new_buy_price * new_buy_quantity

                changes['buy_amount'] = {
                    'old': old_record['buy_amount'],
                    'new': updated_data['buy_amount']
                }

            if 'sell_price' in updated_data or 'sell_quantity' in updated_data:
                new_sell_price = updated_data.get('sell_price', old_record['sell_price'])
                new_sell_quantity = updated_data.get('sell_quantity', old_record['sell_quantity'])
                updated_data['sell_amount'] = new_sell_price * new_sell_quantity

            # 2. 손익 재계산
            if any(k in updated_data for k in ['buy_price', 'sell_price', 'buy_quantity', 'sell_quantity']):
                buy_price = updated_data.get('buy_price', old_record['buy_price'])
                sell_price = updated_data.get('sell_price', old_record['sell_price'])
                quantity = updated_data.get('sell_quantity', old_record.get('sell_quantity'))

                if sell_price and quantity:
                    updated_data['profit_amount'] = (sell_price - buy_price) * quantity
                    updated_data['profit_rate'] = ((sell_price - buy_price) / buy_price) * 100

                    changes['profit_amount'] = {
                        'old': old_record.get('profit_amount'),
                        'new': updated_data['profit_amount']
                    }
                    changes['profit_rate'] = {
                        'old': old_record.get('profit_rate'),
                        'new': updated_data['profit_rate']
                    }

            # 3. 보유 일수 재계산
            if 'buy_date' in updated_data or 'sell_date' in updated_data:
                buy_date_str = updated_data.get('buy_date', old_record['buy_date'])
                sell_date_str = updated_data.get('sell_date', old_record.get('sell_date'))

                if sell_date_str:
                    buy_date = datetime.fromisoformat(buy_date_str)
                    sell_date = datetime.fromisoformat(sell_date_str)
                    updated_data['holding_days'] = (sell_date - buy_date).days

            # updated_at 갱신
            updated_data['updated_at'] = datetime.now().isoformat()

            # UPDATE 쿼리 실행
            updates = []
            values = []

            for key, value in updated_data.items():
                updates.append(f"{key} = ?")
                values.append(value)

            values.append(record_id)

            query = f"""
                UPDATE trading_records
                SET {', '.join(updates)}
                WHERE id = ?
            """

            cursor.execute(query, values)
            conn.commit()

            logger.info(f"매매 기록 수정 완료: ID={record_id}")

            # 통계 캐시 무효화
            self._invalidate_monthly_stats_cache()

            return True, changes

        except Exception as e:
            conn.rollback()
            logger.error(f"매매 기록 수정 실패: {e}")
            raise
        finally:
            conn.close()

    def delete_record(self, record_id: int) -> bool:
        """
        매매 기록 삭제

        Args:
            record_id: 레코드 ID

        Returns:
            bool: 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM trading_records WHERE id = ?", (record_id,))
            conn.commit()

            logger.info(f"매매 기록 삭제 완료: ID={record_id}")

            # 통계 캐시 무효화
            self._invalidate_monthly_stats_cache()

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"매매 기록 삭제 실패: {e}")
            raise
        finally:
            conn.close()

    def get_monthly_stats(self, year_month: str) -> Optional[Dict]:
        """
        월별 통계 조회

        Args:
            year_month: YYYY-MM 형식

        Returns:
            Optional[Dict]: 월별 통계 또는 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM monthly_stats
                WHERE year_month = ?
            """, (year_month,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                # 캐시가 없으면 실시간 계산
                return self._calculate_monthly_stats(year_month)

        except Exception as e:
            logger.error(f"월별 통계 조회 실패: {e}")
            raise
        finally:
            conn.close()

    def _calculate_monthly_stats(self, year_month: str) -> Dict:
        """월별 통계 실시간 계산"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 해당 월의 매도 완료 기록 조회
            cursor.execute("""
                SELECT *
                FROM trading_records
                WHERE strftime('%Y-%m', sell_date) = ?
                AND sell_date IS NOT NULL
            """, (year_month,))

            records = [dict(row) for row in cursor.fetchall()]

            # 통계 계산
            total_profit = sum(r['profit_amount'] for r in records if r['profit_amount'] > 0)
            total_loss = abs(sum(r['profit_amount'] for r in records if r['profit_amount'] < 0))
            net_profit = total_profit - total_loss

            win_count = len([r for r in records if r['profit_amount'] > 0])
            loss_count = len([r for r in records if r['profit_amount'] < 0])
            win_rate = (win_count / len(records) * 100) if records else 0

            avg_profit_rate = sum(r['profit_rate'] for r in records) / len(records) if records else 0

            # 보유 중인 종목 수
            cursor.execute("SELECT COUNT(*) as count FROM trading_records WHERE sell_date IS NULL")
            holding_count = cursor.fetchone()['count']

            stats = {
                'year_month': year_month,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': net_profit,
                'avg_profit_rate': avg_profit_rate,
                'total_trades': len(records),
                'sell_count': len(records),
                'holding_count': holding_count,
                'win_count': win_count,
                'loss_count': loss_count,
                'win_rate': win_rate
            }

            return stats

        except Exception as e:
            logger.error(f"월별 통계 계산 실패: {e}")
            raise
        finally:
            conn.close()

    def _invalidate_monthly_stats_cache(self):
        """월별 통계 캐시 무효화"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM monthly_stats")
            conn.commit()
            logger.info("월별 통계 캐시 무효화 완료")

        except Exception as e:
            conn.rollback()
            logger.error(f"월별 통계 캐시 무효화 실패: {e}")
        finally:
            conn.close()

    def get_record_by_id(self, record_id: int) -> Optional[Dict]:
        """
        ID로 레코드 조회

        Args:
            record_id: 레코드 ID

        Returns:
            Optional[Dict]: 레코드 또는 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM trading_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            else:
                return None

        except Exception as e:
            logger.error(f"레코드 조회 실패: {e}")
            raise
        finally:
            conn.close()
