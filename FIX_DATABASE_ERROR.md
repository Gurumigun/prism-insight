# 데이터베이스 오류 해결 가이드

## 발생 가능한 오류

### 1. UNIQUE constraint failed: stock_holdings.ticker
```
매수 기록 저장 실패: UNIQUE constraint failed: stock_holdings.ticker
```

### 2. 포지션을 찾을 수 없습니다: ID None
```
포지션을 찾을 수 없습니다: ID None
```

## 원인

이 오류들은 데이터베이스 스키마가 구버전일 때 발생합니다:
- 구버전: `ticker` 컬럼에 UNIQUE 제약이 있음 → 동일 종목 여러 번 매수 불가
- 신버전: `id` 컬럼을 PRIMARY KEY로 사용 → 동일 종목 여러 번 매수 가능

## 해결 방법

### 방법 1: 데이터베이스 파일 삭제 (권장)

가장 확실한 방법은 기존 데이터베이스를 삭제하고 새로 생성하는 것입니다.

**⚠️ 주의: 이 방법은 기존 매매 기록을 모두 삭제합니다!**

#### Windows PowerShell 또는 Git Bash:
```bash
# 1. 프로젝트 루트로 이동
cd /path/to/prism-insight

# 2. 데이터베이스 파일 삭제
rm stock_tracking_db.sqlite

# 3. Streamlit 앱 재시작
streamlit run examples/streamlit/app_modern.py
```

#### 또는 파일 탐색기에서:
1. `prism-insight` 폴더를 엽니다
2. `stock_tracking_db.sqlite` 파일을 찾아 삭제합니다
3. Streamlit 앱을 다시 시작합니다

### 방법 2: 최신 코드로 자동 마이그레이션

최신 코드는 자동 마이그레이션 기능이 포함되어 있습니다.

```bash
# 1. 최신 코드 가져오기
git fetch origin claude/feature-custom-work-011CV22frb7e1BaZG8khgQBr
git pull origin claude/feature-custom-work-011CV22frb7e1BaZG8khgQBr

# 2. Streamlit 앱 재시작
streamlit run examples/streamlit/app_modern.py
```

앱을 시작하면 자동으로 데이터베이스 마이그레이션이 실행됩니다:
- ✅ 기존 데이터 백업
- ✅ UNIQUE 제약 제거
- ✅ id 컬럼 추가
- ✅ 데이터 복원

**로그 확인:**
터미널에서 다음 메시지를 확인하세요:
```
⚠️  UNIQUE 제약 또는 잘못된 스키마가 발견되어 마이그레이션을 시작합니다...
📦 기존 데이터 X건 백업 완료
🗑️  기존 테이블 삭제 완료
✨ 새 테이블 생성 완료 (UNIQUE 제약 제거됨)
📥 데이터 X건 복원 완료
✅ 마이그레이션 완료: UNIQUE 제약이 제거되었습니다.
✅ 테이블 스키마 검증 완료: 올바른 스키마입니다.
```

## 마이그레이션 실패 시

마이그레이션이 실패하면 다음 오류 메시지가 표시됩니다:
```
❌ stock_holdings 테이블에 id PRIMARY KEY가 없습니다!
❌ stock_holdings 테이블에 UNIQUE 제약이 여전히 존재합니다!
```

이 경우 **방법 1**을 사용하여 데이터베이스를 삭제하고 다시 생성하세요.

## 데이터 백업 (선택사항)

데이터베이스를 삭제하기 전에 백업하고 싶다면:

```bash
# 백업 생성
cp stock_tracking_db.sqlite stock_tracking_db.backup_$(date +%Y%m%d).sqlite

# 데이터 확인 (SQLite 설치 필요)
sqlite3 stock_tracking_db.sqlite "SELECT * FROM stock_holdings;"
```

## 동일 종목 여러 번 매수 테스트

수정 후 다음과 같이 테스트해보세요:

1. **매수 기록** 탭에서 종목 추가 (예: 삼성전자 005930)
2. 매수 정보 입력 후 저장
3. 같은 종목을 다시 조회하여 매수 (다른 가격, 다른 수량)
4. **보유 종목 조회** 탭에서 2개의 매수 내역이 표시되는지 확인
5. **매도 기록** 탭에서 각각의 매수 건을 선택하여 부분/전체 매도 가능

## 여전히 문제가 발생한다면

1. 데이터베이스 파일 위치 확인:
   ```bash
   find /home/user/prism-insight -name "*.sqlite*"
   ```

2. Python 로그 확인:
   - Streamlit 터미널에서 오류 메시지 확인
   - `logger.error()` 메시지 찾기

3. GitHub Issue 생성:
   - 오류 메시지 전체 복사
   - 사용 환경 (OS, Python 버전) 명시
   - 재현 단계 설명

## 관련 파일

- `/home/user/prism-insight/trading_journal_db.py` - 데이터베이스 로직
- `/home/user/prism-insight/examples/streamlit/app_modern.py` - Streamlit UI
- `/home/user/prism-insight/stock_tracking_db.sqlite` - 데이터베이스 파일 (생성됨)
