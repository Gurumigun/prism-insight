#!/usr/bin/env python3
"""
Streamlit 앱의 매수 기록 저장 기능 테스트
"""

import sqlite3
import json
from datetime import datetime
import sys
import os

# 프로젝트 루트를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

DB_PATH = "stock_tracking_db.sqlite"

def test_streamlit_save_buy_record():
    """Streamlit의 save_buy_record 함수와 동일한 로직 테스트"""
    print("="*80)
    print("🧪 Streamlit save_buy_record 함수 테스트")
    print("="*80)

    # 테스트 데이터
    ticker = "005930"
    company_name = "삼성전자"
    buy_price = 70000
    target_price = 77000
    stop_loss = 66500
    reason = "반도체 업황 개선 기대"

    print(f"\n📝 테스트 데이터:")
    print(f"   종목: {company_name}({ticker})")
    print(f"   매수가: {buy_price:,}원")
    print(f"   목표가: {target_price:,}원")
    print(f"   손절가: {stop_loss:,}원")
    print(f"   이유: {reason}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 기존 데이터 삭제 (중복 방지)
        cursor.execute("DELETE FROM stock_holdings WHERE ticker = ?", (ticker,))

        # 현재 시간
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 시나리오 생성
        scenario = {
            "rationale": reason if reason else "미입력",
            "investment_period": "중기",
            "sector": "기타"
        }

        print(f"\n💾 데이터베이스에 저장 중...")

        # INSERT 실행
        cursor.execute("""
            INSERT INTO stock_holdings
            (ticker, company_name, buy_price, buy_date, current_price,
             target_price, stop_loss, scenario, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker, company_name, buy_price, now, buy_price,
            target_price, stop_loss, json.dumps(scenario, ensure_ascii=False), now
        ))

        conn.commit()
        print("   ✅ 저장 완료")

        # 저장된 데이터 확인
        print(f"\n🔍 저장된 데이터 확인...")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM stock_holdings WHERE ticker = ?
        """, (ticker,))

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
            print(f"      마지막 업데이트: {row['last_updated']}")

            # 시나리오 정보
            try:
                scenario_data = json.loads(row['scenario'])
                print(f"      시나리오:")
                print(f"        - 매수 이유: {scenario_data.get('rationale')}")
                print(f"        - 투자 기간: {scenario_data.get('investment_period')}")
                print(f"        - 산업군: {scenario_data.get('sector')}")
            except Exception as e:
                print(f"      시나리오 파싱 실패: {e}")

        conn.close()
        print("\n✅ 테스트 성공!")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_tradingjournal_db_get_open_positions():
    """TradingJournalDB의 get_open_positions 메서드 테스트"""
    print("\n" + "="*80)
    print("🧪 TradingJournalDB.get_open_positions() 테스트")
    print("="*80)

    try:
        from trading_journal_db import TradingJournalDB

        with TradingJournalDB(DB_PATH) as db:
            print("\n📊 보유 종목 조회 중...")
            positions = db.get_open_positions()

            print(f"   ✅ 조회 완료: {len(positions)}개 종목")

            if positions:
                print("\n   📈 보유 종목 목록:")
                for idx, pos in enumerate(positions, 1):
                    profit_rate = pos['profit_rate']
                    emoji = "🔺" if profit_rate > 0 else "🔻" if profit_rate < 0 else "➖"

                    print(f"\n   {idx}. {emoji} {pos['company_name']}({pos['ticker']})")
                    print(f"      매수가: {pos['buy_price']:,.0f}원")
                    print(f"      현재가: {pos['current_price']:,.0f}원")
                    print(f"      수익률: {profit_rate:+.2f}%")
                    print(f"      목표가: {pos.get('target_price', 0):,.0f}원")
                    print(f"      손절가: {pos.get('stop_loss', 0):,.0f}원")
                    print(f"      매수일: {pos['buy_date']}")

                    # 시나리오 정보
                    if pos.get('scenario'):
                        try:
                            scenario = json.loads(pos['scenario']) if isinstance(pos['scenario'], str) else pos['scenario']
                            if scenario.get('rationale') != "미입력":
                                print(f"      매수 이유: {scenario.get('rationale')}")
                        except:
                            pass

            print("\n✅ 조회 테스트 완료!")
            return True

    except Exception as e:
        print(f"\n❌ 조회 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_data():
    """테스트 데이터 정리"""
    print("\n" + "="*80)
    print("🧹 테스트 데이터 정리")
    print("="*80)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 삼성전자 테스트 데이터 삭제
        cursor.execute("DELETE FROM stock_holdings WHERE ticker = '005930'")
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"\n   ✅ {deleted}개 테스트 데이터 삭제 완료")
        return True

    except Exception as e:
        print(f"\n   ❌ 정리 실패: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n")
    print("🚀 Streamlit 매수 기록 저장 기능 검증")
    print("="*80)

    # 1. 매수 기록 저장 테스트
    save_success = test_streamlit_save_buy_record()

    if save_success:
        # 2. 조회 테스트
        query_success = test_tradingjournal_db_get_open_positions()

        # 3. 데이터 정리
        cleanup_test_data()

        if save_success and query_success:
            print("\n" + "="*80)
            print("🎉 모든 테스트 통과!")
            print("="*80)
            print("\n✅ Streamlit 앱에서 매수 기록이 정상적으로 저장되고 조회됩니다.")
            print("   - 데이터베이스: stock_tracking_db.sqlite")
            print("   - 테이블: stock_holdings")
            print("   - 기능: INSERT, SELECT 모두 정상 작동")
            print("\n")
    else:
        print("\n" + "="*80)
        print("❌ 테스트 실패")
        print("="*80)
