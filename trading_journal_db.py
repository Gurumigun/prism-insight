#!/usr/bin/env python3
"""
Trading Journal Database Module
매매 기록 및 보유 종목 관리를 위한 데이터베이스 모듈
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# pykrx import
try:
    from pykrx import stock
except ImportError:
    stock = None

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
        # 먼저 마이그레이션 체크 (기존 테이블이 잘못된 스키마를 가진 경우)
        self._migrate_remove_unique_constraint()

        # stock_holdings 테이블 생성 (여러 번 매수 가능하도록 id 추가)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                current_price REAL,
                last_updated TEXT,
                scenario TEXT,
                rsi REAL,
                macd REAL,
                adr REAL,
                market_kospi_adr REAL,
                market_kosdaq_adr REAL,
                is_sold INTEGER DEFAULT 0,
                sell_price REAL,
                sell_date TEXT
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

        # 마이그레이션 후 다시 한 번 체크 (혹시 모를 문제 대비)
        self._validate_schema()

    def _migrate_remove_unique_constraint(self):
        """
        기존 stock_holdings 테이블의 ticker UNIQUE 제약 제거
        (여러 번 매수를 지원하기 위해)
        """
        try:
            # 테이블이 존재하는지 확인
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_holdings'")
            table_exists = self.cursor.fetchone()

            if not table_exists:
                logger.info("stock_holdings 테이블이 없어서 마이그레이션을 건너뜁니다.")
                return

            # 기존 테이블 스키마 확인
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_holdings'")
            result = self.cursor.fetchone()

            if not result:
                logger.info("테이블 스키마를 가져올 수 없어서 마이그레이션을 건너뜁니다.")
                return

            current_schema = result[0]
            logger.info(f"현재 테이블 스키마: {current_schema}")

            # UNIQUE 제약 확인 (CREATE TABLE 문이나 인덱스 확인)
            has_unique_constraint = 'UNIQUE' in current_schema.upper()

            # 인덱스에서도 UNIQUE 제약 확인
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stock_holdings'")
            indexes = self.cursor.fetchall()
            for idx in indexes:
                if idx[0] and 'UNIQUE' in idx[0].upper():
                    has_unique_constraint = True
                    logger.info(f"UNIQUE 인덱스 발견: {idx[0]}")
                    break

            # id 컬럼이 없는 경우에도 마이그레이션 필요
            has_id_column = 'id INTEGER PRIMARY KEY AUTOINCREMENT' in current_schema

            needs_migration = has_unique_constraint or not has_id_column

            if not needs_migration:
                logger.info("마이그레이션이 필요하지 않습니다. (UNIQUE 제약 없음)")
                return

            logger.info("⚠️  UNIQUE 제약 또는 잘못된 스키마가 발견되어 마이그레이션을 시작합니다...")

            # 기존 데이터 백업
            self.cursor.execute("""
                CREATE TEMP TABLE stock_holdings_backup AS
                SELECT * FROM stock_holdings
            """)
            backup_count = self.cursor.execute("SELECT COUNT(*) FROM stock_holdings_backup").fetchone()[0]
            logger.info(f"📦 기존 데이터 {backup_count}건 백업 완료")

            # 기존 인덱스 삭제
            for idx in indexes:
                if idx[0]:
                    try:
                        idx_name = idx[0].split('CREATE')[1].split('INDEX')[1].split('ON')[0].strip()
                        self.cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
                    except:
                        pass

            # 기존 테이블 삭제
            self.cursor.execute("DROP TABLE stock_holdings")
            logger.info("🗑️  기존 테이블 삭제 완료")

            # 새 테이블 생성 (UNIQUE 제약 없이)
            self.cursor.execute("""
                CREATE TABLE stock_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    buy_price REAL NOT NULL,
                    buy_date TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    current_price REAL,
                    last_updated TEXT,
                    scenario TEXT,
                    rsi REAL,
                    macd REAL,
                    adr REAL,
                    market_kospi_adr REAL,
                    market_kosdaq_adr REAL,
                    is_sold INTEGER DEFAULT 0,
                    sell_price REAL,
                    sell_date TEXT
                )
            """)
            logger.info("✨ 새 테이블 생성 완료 (UNIQUE 제약 제거됨)")

            # 백업 테이블의 컬럼 확인
            self.cursor.execute("PRAGMA table_info(stock_holdings_backup)")
            backup_columns = [col[1] for col in self.cursor.fetchall()]

            # 새 테이블의 컬럼 확인
            self.cursor.execute("PRAGMA table_info(stock_holdings)")
            new_columns = [col[1] for col in self.cursor.fetchall()]

            # 공통 컬럼만 복사 (id는 자동 생성되므로 제외)
            common_columns = [col for col in backup_columns if col in new_columns and col != 'id']
            columns_str = ', '.join(common_columns)

            # 데이터 복원
            if common_columns:
                self.cursor.execute(f"""
                    INSERT INTO stock_holdings ({columns_str})
                    SELECT {columns_str} FROM stock_holdings_backup
                """)
                restored_count = self.cursor.execute("SELECT COUNT(*) FROM stock_holdings").fetchone()[0]
                logger.info(f"📥 데이터 {restored_count}건 복원 완료")

            # 임시 테이블 삭제
            self.cursor.execute("DROP TABLE stock_holdings_backup")

            self.conn.commit()
            logger.info("✅ 마이그레이션 완료: UNIQUE 제약이 제거되었습니다. 이제 같은 종목을 여러 번 매수할 수 있습니다!")

        except Exception as e:
            logger.error(f"❌ 마이그레이션 중 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 마이그레이션 실패 시 롤백
            try:
                self.conn.rollback()
            except:
                pass

    def _validate_schema(self):
        """
        테이블 스키마가 올바른지 검증
        """
        try:
            # stock_holdings 테이블 스키마 확인
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_holdings'")
            result = self.cursor.fetchone()

            if not result:
                logger.warning("⚠️  stock_holdings 테이블을 찾을 수 없습니다.")
                return

            current_schema = result[0]

            # 필수 요구사항 체크
            has_id_pk = 'id INTEGER PRIMARY KEY AUTOINCREMENT' in current_schema
            has_unique = 'UNIQUE' in current_schema.upper()

            # UNIQUE 인덱스 체크
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stock_holdings'")
            indexes = self.cursor.fetchall()
            for idx in indexes:
                if idx[0] and 'UNIQUE' in idx[0].upper():
                    has_unique = True

            if not has_id_pk:
                logger.error("❌ stock_holdings 테이블에 id PRIMARY KEY가 없습니다!")
                logger.error("   데이터베이스 파일을 삭제하고 다시 시도하거나 관리자에게 문의하세요.")

            if has_unique:
                logger.error("❌ stock_holdings 테이블에 UNIQUE 제약이 여전히 존재합니다!")
                logger.error("   데이터베이스 파일을 삭제하고 다시 시도하거나 관리자에게 문의하세요.")

            if has_id_pk and not has_unique:
                logger.info("✅ 테이블 스키마 검증 완료: 올바른 스키마입니다.")

        except Exception as e:
            logger.warning(f"스키마 검증 중 오류 (무시 가능): {str(e)}")

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """
        pykrx를 사용하여 실시간 현재가 조회

        Args:
            ticker: 종목코드

        Returns:
            현재가 (실패 시 None)
        """
        if stock is None:
            logger.warning("pykrx 모듈을 불러올 수 없습니다.")
            return None

        try:
            # 오늘 날짜와 최근 7일 데이터 가져오기
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            df = stock.get_market_ohlcv_by_date(
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
                ticker
            )

            if df.empty:
                logger.warning(f"{ticker} 종목의 가격 정보를 가져올 수 없습니다.")
                return None

            # 가장 최근 종가 반환
            current_price = df.iloc[-1]['종가']
            return float(current_price)

        except Exception as e:
            logger.error(f"{ticker} 종목 현재가 조회 실패: {str(e)}")
            return None

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        현재 보유 중인 종목 목록 조회 (미매도 포지션만)

        Returns:
            보유 종목 정보 리스트 (개별 매수 건별)
        """
        try:
            # is_sold가 0인 것만 조회
            self.cursor.execute("""
                SELECT
                    id,
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    quantity,
                    current_price,
                    rsi,
                    macd,
                    adr,
                    market_kospi_adr,
                    market_kosdaq_adr,
                    scenario,
                    last_updated
                FROM stock_holdings
                WHERE is_sold = 0 OR is_sold IS NULL
                ORDER BY buy_date DESC
            """)

            rows = self.cursor.fetchall()

            if not rows:
                logger.info("보유 중인 종목이 없습니다.")
                return []

            positions = []
            for row in rows:
                row_dict = dict(row)

                # 실시간 현재가 조회
                ticker = row_dict.get('ticker')
                current_price = self._get_current_price(ticker)

                # 현재가를 가져오지 못한 경우 DB에 저장된 값 사용
                if current_price is None:
                    current_price = row_dict.get('current_price', 0)
                else:
                    # 실시간 현재가를 row_dict에 업데이트
                    row_dict['current_price'] = current_price

                # 수익률 계산
                buy_price = row_dict.get('buy_price', 0)

                if buy_price > 0 and current_price > 0:
                    profit_rate = ((current_price - buy_price) / buy_price) * 100
                else:
                    profit_rate = 0.0

                row_dict['profit_rate'] = profit_rate
                positions.append(row_dict)

            logger.info(f"보유 종목 {len(positions)}개 조회 완료")
            return positions

        except Exception as e:
            logger.error(f"매수 기록 조회 실패: {str(e)}")
            return []

    def get_aggregated_positions(self) -> List[Dict[str, Any]]:
        """
        종목별로 합산된 보유 정보 조회

        Returns:
            종목별 합산 정보 [{
                'ticker': 종목코드,
                'company_name': 종목명,
                'total_quantity': 총 수량,
                'avg_buy_price': 평균 매수가,
                'total_cost': 총 매수 금액,
                'current_price': 현재가,
                'total_value': 평가 금액,
                'profit_rate': 수익률,
                'buy_count': 매수 횟수
            }, ...]
        """
        try:
            # 최신 레코드의 current_price를 명시적으로 가져오도록 수정
            self.cursor.execute("""
                SELECT
                    ticker,
                    MAX(company_name) as company_name,
                    SUM(quantity) as total_quantity,
                    SUM(buy_price * quantity) / SUM(quantity) as avg_buy_price,
                    SUM(buy_price * quantity) as total_cost,
                    MAX(current_price) as current_price,
                    COUNT(*) as buy_count
                FROM stock_holdings
                WHERE is_sold = 0 OR is_sold IS NULL
                GROUP BY ticker
                ORDER BY ticker
            """)

            rows = self.cursor.fetchall()

            aggregated = []
            for row in rows:
                row_dict = dict(row)

                # 실시간 현재가 조회
                ticker = row_dict.get('ticker')
                current_price = self._get_current_price(ticker)

                # 현재가를 가져오지 못한 경우 DB에 저장된 값 또는 평균 매수가 사용
                if current_price is None:
                    current_price = row_dict.get('current_price', row_dict['avg_buy_price'])
                else:
                    # 실시간 현재가를 row_dict에 업데이트
                    row_dict['current_price'] = current_price

                total_quantity = row_dict['total_quantity']
                avg_buy_price = row_dict['avg_buy_price']

                total_value = current_price * total_quantity
                total_cost = row_dict['total_cost']

                if total_cost > 0:
                    profit_rate = ((total_value - total_cost) / total_cost) * 100
                else:
                    profit_rate = 0.0

                row_dict['total_value'] = total_value
                row_dict['profit_rate'] = profit_rate

                aggregated.append(row_dict)

            return aggregated

        except Exception as e:
            logger.error(f"합산 정보 조회 실패: {str(e)}")
            return []

    def get_position_details_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """
        특정 종목의 개별 매수 내역 조회

        Args:
            ticker: 종목 코드

        Returns:
            개별 매수 내역 리스트
        """
        try:
            self.cursor.execute("""
                SELECT
                    id,
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    quantity,
                    current_price,
                    rsi,
                    macd,
                    adr,
                    market_kospi_adr,
                    market_kosdaq_adr,
                    scenario,
                    last_updated
                FROM stock_holdings
                WHERE ticker = ? AND (is_sold = 0 OR is_sold IS NULL)
                ORDER BY buy_date DESC
            """, (ticker,))

            rows = self.cursor.fetchall()

            # 실시간 현재가를 한 번만 조회 (같은 ticker이므로)
            current_price_live = self._get_current_price(ticker)

            details = []
            for row in rows:
                row_dict = dict(row)

                # 실시간 현재가 사용, 가져오지 못한 경우 DB 값 사용
                if current_price_live is not None:
                    current_price = current_price_live
                    row_dict['current_price'] = current_price
                else:
                    current_price = row_dict.get('current_price', 0)

                buy_price = row_dict.get('buy_price', 0)

                if buy_price > 0 and current_price > 0:
                    profit_rate = ((current_price - buy_price) / buy_price) * 100
                else:
                    profit_rate = 0.0

                row_dict['profit_rate'] = profit_rate
                details.append(row_dict)

            return details

        except Exception as e:
            logger.error(f"{ticker} 종목 상세 조회 실패: {str(e)}")
            return []

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """
        모든 거래 내역 조회 (매수 + 매도)

        Returns:
            전체 거래 내역 (매수/매도 포함)
        """
        try:
            transactions = []

            # 미매도 매수 내역
            self.cursor.execute("""
                SELECT
                    id,
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    quantity,
                    current_price,
                    rsi,
                    macd,
                    adr,
                    market_kospi_adr,
                    market_kosdaq_adr,
                    scenario,
                    'HOLDING' as status
                FROM stock_holdings
                WHERE is_sold = 0 OR is_sold IS NULL

                UNION ALL

                SELECT
                    id,
                    ticker,
                    company_name,
                    buy_price,
                    buy_date,
                    quantity,
                    sell_price as current_price,
                    rsi,
                    macd,
                    adr,
                    market_kospi_adr,
                    market_kosdaq_adr,
                    scenario,
                    'SOLD' as status
                FROM stock_holdings
                WHERE is_sold = 1

                ORDER BY buy_date DESC
            """)

            rows = self.cursor.fetchall()

            for row in rows:
                row_dict = dict(row)

                buy_price = row_dict.get('buy_price', 0)
                current_price = row_dict.get('current_price', 0)
                quantity = row_dict.get('quantity', 0)

                if buy_price > 0 and current_price > 0:
                    profit_rate = ((current_price - buy_price) / buy_price) * 100
                    net_profit = (current_price - buy_price) * quantity
                else:
                    profit_rate = 0.0
                    net_profit = 0.0

                row_dict['profit_rate'] = profit_rate
                row_dict['net_profit'] = net_profit
                transactions.append(row_dict)

            return transactions

        except Exception as e:
            logger.error(f"전체 거래 내역 조회 실패: {str(e)}")
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
        market_kospi_adr: Optional[float] = None,
        market_kosdaq_adr: Optional[float] = None,
        scenario: Optional[str] = None
    ) -> bool:
        """
        매수 기록 추가 (동일 종목 여러 번 매수 가능)

        Args:
            ticker: 종목 코드
            company_name: 종목명
            buy_price: 매수가
            buy_date: 매수일 (YYYY-MM-DD HH:MM:SS 형식)
            quantity: 수량 (기본값 1)
            rsi: RSI 지표
            macd: MACD 지표
            adr: ADR 지표
            market_kospi_adr: 코스피 시장 ADR
            market_kosdaq_adr: 코스닥 시장 ADR
            scenario: 시나리오 정보 (JSON 문자열)

        Returns:
            성공 여부
        """
        try:
            # 신규 컬럼 추가 (기존 테이블 대응)
            columns_to_add = [
                ("market_kospi_adr", "REAL"),
                ("market_kosdaq_adr", "REAL"),
                ("is_sold", "INTEGER DEFAULT 0"),
                ("sell_price", "REAL"),
                ("sell_date", "TEXT"),
                ("id", "INTEGER")  # 기존 테이블에 id 없는 경우 대응
            ]

            for col_name, col_type in columns_to_add:
                try:
                    self.cursor.execute(f"ALTER TABLE stock_holdings ADD COLUMN {col_name} {col_type}")
                    self.conn.commit()
                except:
                    pass

            # INSERT (여러 번 매수 가능하도록 REPLACE 제거)
            self.cursor.execute("""
                INSERT INTO stock_holdings
                (ticker, company_name, buy_price, buy_date, quantity, current_price,
                 rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, scenario, last_updated, is_sold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                market_kospi_adr,
                market_kosdaq_adr,
                scenario,
                buy_date
            ))

            self.conn.commit()
            logger.info(f"매수 기록 저장 완료: {company_name}({ticker}) {quantity}주")
            return True

        except Exception as e:
            logger.error(f"매수 기록 저장 실패: {str(e)}")
            return False

    def update_current_price(self, ticker: str, new_price: float) -> bool:
        """
        특정 종목의 현재가를 수동으로 업데이트

        Args:
            ticker: 종목코드
            new_price: 새로운 현재가

        Returns:
            성공 여부
        """
        try:
            # 해당 종목의 모든 미매도 포지션의 current_price 업데이트
            self.cursor.execute("""
                UPDATE stock_holdings
                SET current_price = ?, last_updated = ?
                WHERE ticker = ? AND (is_sold = 0 OR is_sold IS NULL)
            """, (new_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticker))

            updated_count = self.cursor.rowcount
            self.conn.commit()

            logger.info(f"{ticker} 종목의 현재가 업데이트 완료: {new_price}원 ({updated_count}건)")
            return True

        except Exception as e:
            logger.error(f"현재가 업데이트 실패: {str(e)}")
            return False

    def update_all_current_prices_from_pykrx(self) -> Dict[str, Any]:
        """
        모든 보유 종목의 현재가를 pykrx로 한번에 업데이트

        Returns:
            업데이트 결과 {"success": 성공 개수, "failed": 실패 개수, "details": [...]}
        """
        result = {
            "success": 0,
            "failed": 0,
            "details": []
        }

        try:
            # 미매도 종목 목록 조회 (중복 제거)
            self.cursor.execute("""
                SELECT DISTINCT ticker, company_name
                FROM stock_holdings
                WHERE is_sold = 0 OR is_sold IS NULL
            """)

            tickers = self.cursor.fetchall()

            for row in tickers:
                ticker = row['ticker']
                company_name = row['company_name']

                # pykrx로 현재가 조회
                current_price = self._get_current_price(ticker)

                if current_price is not None:
                    # 현재가 업데이트
                    if self.update_current_price(ticker, current_price):
                        result["success"] += 1
                        result["details"].append({
                            "ticker": ticker,
                            "company_name": company_name,
                            "price": current_price,
                            "status": "success"
                        })
                    else:
                        result["failed"] += 1
                        result["details"].append({
                            "ticker": ticker,
                            "company_name": company_name,
                            "status": "update_failed"
                        })
                else:
                    result["failed"] += 1
                    result["details"].append({
                        "ticker": ticker,
                        "company_name": company_name,
                        "status": "price_fetch_failed"
                    })

            return result

        except Exception as e:
            logger.error(f"일괄 현재가 업데이트 실패: {str(e)}")
            return result

    def sell_position(
        self,
        position_id: int,
        sell_quantity: int,
        sell_price: float,
        sell_date: str
    ) -> bool:
        """
        포지션 매도 (전체 또는 부분)

        Args:
            position_id: 매도할 포지션 ID
            sell_quantity: 매도 수량
            sell_price: 매도 가격
            sell_date: 매도 날짜

        Returns:
            성공 여부
        """
        try:
            # position_id 유효성 검증
            if position_id is None:
                logger.error("❌ 포지션 ID가 None입니다. 데이터베이스 스키마에 id 컬럼이 없을 수 있습니다.")
                logger.error("   해결 방법: 데이터베이스 파일을 삭제하고 앱을 다시 시작하세요.")
                return False

            # 해당 포지션 조회
            self.cursor.execute("""
                SELECT id, ticker, company_name, buy_price, buy_date, quantity,
                       rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, scenario
                FROM stock_holdings
                WHERE id = ? AND (is_sold = 0 OR is_sold IS NULL)
            """, (position_id,))

            position = self.cursor.fetchone()
            if not position:
                logger.error(f"포지션을 찾을 수 없습니다: ID {position_id}")
                logger.error("   보유 종목 목록을 다시 확인해주세요.")
                return False

            position_dict = dict(position)
            current_quantity = position_dict['quantity']

            if sell_quantity > current_quantity:
                logger.error(f"매도 수량({sell_quantity})이 보유 수량({current_quantity})보다 많습니다.")
                return False

            if sell_quantity == current_quantity:
                # 전체 매도: is_sold=1로 설정
                self.cursor.execute("""
                    UPDATE stock_holdings
                    SET is_sold = 1, sell_price = ?, sell_date = ?, current_price = ?
                    WHERE id = ?
                """, (sell_price, sell_date, sell_price, position_id))

                logger.info(f"전체 매도 완료: {position_dict['company_name']} {sell_quantity}주")

            else:
                # 부분 매도
                # 1. 원래 레코드의 수량 차감
                remaining_quantity = current_quantity - sell_quantity
                self.cursor.execute("""
                    UPDATE stock_holdings
                    SET quantity = ?
                    WHERE id = ?
                """, (remaining_quantity, position_id))

                # 2. 매도된 부분을 새 레코드로 추가
                self.cursor.execute("""
                    INSERT INTO stock_holdings
                    (ticker, company_name, buy_price, buy_date, quantity, current_price,
                     rsi, macd, adr, market_kospi_adr, market_kosdaq_adr, scenario,
                     is_sold, sell_price, sell_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """, (
                    position_dict['ticker'],
                    position_dict['company_name'],
                    position_dict['buy_price'],
                    position_dict['buy_date'],
                    sell_quantity,
                    sell_price,
                    position_dict.get('rsi'),
                    position_dict.get('macd'),
                    position_dict.get('adr'),
                    position_dict.get('market_kospi_adr'),
                    position_dict.get('market_kosdaq_adr'),
                    position_dict.get('scenario'),
                    sell_price,
                    sell_date,
                    sell_date
                ))

                logger.info(f"부분 매도 완료: {position_dict['company_name']} {sell_quantity}주 (잔여: {remaining_quantity}주)")

            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"매도 처리 실패: {str(e)}")
            self.conn.rollback()
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
