#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
매수/매도 기록을 위한 테이블 생성
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "stock_tracking_db.sqlite"

def init_database():
    """데이터베이스 테이블 초기화"""

    print(f"📊 데이터베이스 초기화 시작: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. stock_holdings 테이블 생성 (보유 종목)
    print("\n1️⃣ stock_holdings 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_holdings (
            ticker TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            buy_price REAL NOT NULL,
            buy_date TEXT NOT NULL,
            current_price REAL,
            last_updated TEXT,
            scenario TEXT,
            target_price REAL,
            stop_loss REAL
        )
    """)
    print("   ✅ stock_holdings 테이블 생성 완료")

    # 2. trading_history 테이블 생성 (매매 내역)
    print("\n2️⃣ trading_history 테이블 생성...")
    cursor.execute("""
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
    print("   ✅ trading_history 테이블 생성 완료")

    # 3. market_condition 테이블 (시장 상태)
    print("\n3️⃣ market_condition 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_condition (
            date TEXT PRIMARY KEY,
            kospi_index REAL,
            kosdaq_index REAL,
            condition INTEGER,
            volatility REAL
        )
    """)
    print("   ✅ market_condition 테이블 생성 완료")

    # 4. watchlist_history 테이블 (관망 종목)
    print("\n4️⃣ watchlist_history 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT NOT NULL,
            current_price REAL NOT NULL,
            analyzed_date TEXT NOT NULL,
            buy_score INTEGER NOT NULL,
            min_score INTEGER NOT NULL,
            decision TEXT NOT NULL,
            skip_reason TEXT NOT NULL,
            target_price REAL,
            stop_loss REAL,
            investment_period TEXT,
            sector TEXT,
            scenario TEXT,
            portfolio_analysis TEXT,
            valuation_analysis TEXT,
            sector_outlook TEXT,
            market_condition TEXT,
            rationale TEXT
        )
    """)
    print("   ✅ watchlist_history 테이블 생성 완료")

    # 5. holding_decisions 테이블 (매도 판단 기록)
    print("\n5️⃣ holding_decisions 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holding_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            decision_date TEXT NOT NULL,
            decision_time TEXT NOT NULL,

            current_price REAL NOT NULL,
            should_sell BOOLEAN NOT NULL,
            sell_reason TEXT,
            confidence INTEGER,

            technical_trend TEXT,
            volume_analysis TEXT,
            market_condition_impact TEXT,
            time_factor TEXT,

            portfolio_adjustment_needed BOOLEAN,
            adjustment_reason TEXT,
            new_target_price REAL,
            new_stop_loss REAL,
            adjustment_urgency TEXT,

            full_json_data TEXT NOT NULL,

            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (ticker) REFERENCES stock_holdings(ticker)
        )
    """)
    print("   ✅ holding_decisions 테이블 생성 완료")

    conn.commit()

    # 테이블 확인
    print("\n📋 생성된 테이블 목록:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]}: {count}개 레코드")

    conn.close()

    print(f"\n✅ 데이터베이스 초기화 완료!")
    print(f"   파일 위치: {os.path.abspath(DB_PATH)}")


def test_insert_and_query():
    """테스트 데이터 삽입 및 조회"""
    print("\n" + "="*80)
    print("🧪 테스트: 데이터 삽입 및 조회")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 테스트 데이터 삽입
    test_ticker = "000000"
    test_company = "테스트종목"
    test_buy_price = 50000
    test_current_price = 55000
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 기존 테스트 데이터 삭제
    cursor.execute("DELETE FROM stock_holdings WHERE ticker = ?", (test_ticker,))

    print(f"\n1️⃣ 테스트 데이터 삽입...")
    print(f"   종목: {test_company}({test_ticker})")
    print(f"   매수가: {test_buy_price:,}원")

    import json
    scenario = {
        "rationale": "테스트 매수",
        "investment_period": "단기",
        "sector": "테스트"
    }

    cursor.execute("""
        INSERT INTO stock_holdings
        (ticker, company_name, buy_price, buy_date, current_price,
         target_price, stop_loss, scenario, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_ticker, test_company, test_buy_price, now, test_current_price,
        int(test_buy_price * 1.1), int(test_buy_price * 0.95),
        json.dumps(scenario, ensure_ascii=False), now
    ))

    conn.commit()
    print("   ✅ 삽입 완료")

    # 데이터 조회
    print(f"\n2️⃣ 데이터 조회...")
    cursor.execute("""
        SELECT ticker, company_name, buy_price, current_price,
               target_price, stop_loss, buy_date, scenario
        FROM stock_holdings
        WHERE ticker = ?
    """, (test_ticker,))

    row = cursor.fetchone()
    if row:
        print("   ✅ 조회 성공:")
        print(f"      종목명: {row['company_name']}")
        print(f"      종목코드: {row['ticker']}")
        print(f"      매수가: {row['buy_price']:,.0f}원")
        print(f"      현재가: {row['current_price']:,.0f}원")
        print(f"      목표가: {row['target_price']:,.0f}원")
        print(f"      손절가: {row['stop_loss']:,.0f}원")
        print(f"      매수일: {row['buy_date']}")

        profit_rate = ((row['current_price'] - row['buy_price']) / row['buy_price']) * 100
        print(f"      수익률: {profit_rate:+.2f}%")

        try:
            scenario_data = json.loads(row['scenario'])
            print(f"      매수 이유: {scenario_data.get('rationale')}")
        except:
            pass
    else:
        print("   ❌ 조회 실패")

    # 테스트 데이터 삭제
    print(f"\n3️⃣ 테스트 데이터 삭제...")
    cursor.execute("DELETE FROM stock_holdings WHERE ticker = ?", (test_ticker,))
    conn.commit()
    print("   ✅ 삭제 완료")

    conn.close()
    print("\n✅ 테스트 완료!")


def verify_tradingjournal_db():
    """TradingJournalDB 클래스 테스트"""
    print("\n" + "="*80)
    print("🧪 TradingJournalDB 클래스 테스트")
    print("="*80)

    try:
        from trading_journal_db import TradingJournalDB

        print("\n1️⃣ TradingJournalDB 인스턴스 생성...")
        with TradingJournalDB(DB_PATH) as db:
            print("   ✅ 생성 완료")

            print("\n2️⃣ get_open_positions() 메서드 호출...")
            positions = db.get_open_positions()
            print(f"   ✅ 조회 완료: {len(positions)}개 종목")

            if positions:
                for pos in positions[:3]:  # 최대 3개만 표시
                    print(f"      - {pos['company_name']}({pos['ticker']}): {pos['profit_rate']:+.2f}%")
            else:
                print("      (보유 종목 없음)")

            print("\n3️⃣ get_statistics() 메서드 호출...")
            stats = db.get_statistics()
            print("   ✅ 통계 조회 완료:")
            print(f"      - 보유 종목: {stats.get('open_positions_count', 0)}개")
            print(f"      - 총 거래: {stats.get('total_trades', 0)}건")
            print(f"      - 승률: {stats.get('win_rate', 0):.2f}%")

        print("\n✅ TradingJournalDB 테스트 완료!")

    except ImportError as e:
        print(f"   ❌ TradingJournalDB import 실패: {e}")
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*80)
    print("🚀 Stock Tracking Database 초기화")
    print("="*80)

    # 1. 데이터베이스 초기화
    init_database()

    # 2. 데이터 삽입/조회 테스트
    test_insert_and_query()

    # 3. TradingJournalDB 클래스 테스트
    verify_tradingjournal_db()

    print("\n" + "="*80)
    print("🎉 모든 테스트 완료!")
    print("="*80)
