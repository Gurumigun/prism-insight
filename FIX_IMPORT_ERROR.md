# UnboundLocalError 해결 방법

## 문제 상황
```
UnboundLocalError: cannot access local variable 'stock' where it is not associated with a value
```

## 원인
`app_modern.py` 파일에 필수 import 구문이 누락되어 있습니다.

## 해결 방법

### 방법 1: 강제로 최신 코드 받기 (권장)

Windows PowerShell 또는 Git Bash에서 다음 명령어를 실행하세요:

```bash
# 1. 현재 변경사항 임시 저장 (혹시 모를 작업 내용 보호)
git stash

# 2. 최신 코드 강제로 받기
git fetch origin claude/feature-custom-work-011CV22frb7e1BaZG8khgQBr
git reset --hard origin/claude/feature-custom-work-011CV22frb7e1BaZG8khgQBr

# 3. 임시 저장한 내용 확인 (필요시 복원)
git stash list
```

### 방법 2: 파일 직접 수정

`C:\Users\worms\gurumi-prism\examples\streamlit\app_modern.py` 파일을 열어서 수정하세요.

**찾아야 할 부분:**
```python
from queue import Queue
from threading import Thread
import uuid
```

**이 바로 아래에 다음을 추가:**
```python
# TradingJournalDB import
try:
    from trading_journal_db import TradingJournalDB
except ImportError:
    TradingJournalDB = None

# pykrx import
try:
    from pykrx import stock
except ImportError:
    stock = None
```

**⚠️ 주의:** `from email_sender import send_email` 이 있다면 **삭제**하세요.

### 방법 3: 파일 내용 전체 확인

파일 상단(1-40줄)이 다음과 같아야 합니다:

```python
import streamlit as st
from datetime import datetime, timedelta
import re
from pathlib import Path
import markdown
import base64
import sys
import os
import pandas as pd
import json
import plotly.graph_objects as go

# 현재 파일의 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if current_dir not in sys.path:
    sys.path.append(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from queue import Queue
from threading import Thread
import uuid

# TradingJournalDB import
try:
    from trading_journal_db import TradingJournalDB
except ImportError:
    TradingJournalDB = None

# pykrx import
try:
    from pykrx import stock
except ImportError:
    stock = None

# 보고서 저장 디렉토리 설정
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
```

## 수정 후 확인

1. Streamlit 서버 재시작
2. 브라우저 캐시 클리어 (Ctrl + Shift + R)
3. 앱 실행: `streamlit run examples/streamlit/app_modern.py`

## 여전히 오류가 발생한다면

다음을 확인하세요:
- [ ] pykrx 설치: `pip install pykrx`
- [ ] trading_journal_db.py 파일이 프로젝트 루트에 있는지
- [ ] Python 버전 확인: `python --version` (3.8 이상 권장)
