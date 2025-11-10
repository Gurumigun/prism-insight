@echo off
REM Streamlit Personal Stock Analyzer - Windows 실행 스크립트
REM Anaconda Prompt 또는 cmd에서 실행

echo ========================================
echo  PRISM-INSIGHT Streamlit 개인 주식 분석기
echo ========================================
echo.

REM 필요한 패키지 확인
echo [1/2] 필요한 패키지 확인 중...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [경고] streamlit이 설치되지 않았습니다.
    echo 설치를 시작합니다: pip install streamlit
    pip install streamlit
)

python -c "import anthropic" 2>nul
if errorlevel 1 (
    echo [경고] anthropic이 설치되지 않았습니다.
    echo 설치를 시작합니다: pip install anthropic
    pip install anthropic
)

echo.
echo [2/2] Streamlit 앱 실행 중...
echo.
echo 브라우저에서 자동으로 열립니다.
echo 수동으로 열려면: http://localhost:8501
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM Streamlit 실행 (매수/매도 기록 기능 포함)
streamlit run examples/streamlit/app_modern.py --server.port 8501 --server.headless false

pause
