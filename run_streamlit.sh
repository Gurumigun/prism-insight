#!/bin/bash

# PRISM-INSIGHT Streamlit 실행 스크립트

cd "$(dirname "$0")"

echo "🚀 PRISM-INSIGHT Streamlit 앱을 시작합니다..."
echo "📍 브라우저에서 http://localhost:8501 로 접속하세요"
echo ""

streamlit run streamlit_apps/personal_analyzer.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
