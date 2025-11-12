# 🎨 모던 테마 적용 가이드

## 변경 사항

`examples/streamlit/app_modern.py`의 `apply_custom_styles()` 메서드를 교체하여 다크/라이트 테마를 지원합니다.

---

## 📝 수정 방법

`app_modern.py` 파일에서 **93줄부터 479줄까지**의 `apply_custom_styles()` 메서드를 아래 코드로 교체하세요.

### 교체할 코드:

```python
    def apply_custom_styles(self):
        """모던한 다크/라이트 테마 대응 디자인 스타일 적용"""
        # CSS 파일 경로
        css_file = Path(__file__).parent / "modern_theme.css"

        # CSS 파일 읽기
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()

            # CSS 적용
            st.markdown(f"""
            <style>
            {css_content}
            </style>
            """, unsafe_allow_html=True)

        except FileNotFoundError:
            st.warning("⚠️ CSS 테마 파일을 찾을 수 없습니다. 기본 스타일을 사용합니다.")
```

---

## ✨ 새로운 기능

### 1. **자동 다크/라이트 테마 전환**
   - 시스템 설정에 따라 자동으로 테마가 전환됩니다
   - `prefers-color-scheme` CSS 미디어 쿼리 활용

### 2. **CSS 변수 기반 테마 시스템**
   - 모든 색상이 CSS 변수로 관리됩니다
   - 테마 간 매끄러운 전환 애니메이션

### 3. **모던 디자인 요소**
   - 🎴 Glass morphism 효과 (카드, 버튼)
   - ✨ 그라데이션 배경 및 텍스트
   - 🌊 부드러운 호버 애니메이션
   - 💫 Backdrop blur 효과

### 4. **개선된 접근성**
   - 향상된 포커스 아웃라인
   - 명확한 색상 대비
   - 키보드 네비게이션 지원

---

## 🎨 테마 색상 팔레트

### 라이트 모드
- **Primary**: #0EA5E9 (Sky Blue)
- **Background**: #FFFFFF → #F8FAFC (Gradient)
- **Text**: #0F172A (Dark Slate)

### 다크 모드
- **Primary**: #38BDF8 (Bright Sky Blue)
- **Background**: #0F172A → #1E293B (Gradient)
- **Text**: #F8FAFC (Light Slate)

---

## 🔧 커스터마이징

`modern_theme.css` 파일을 직접 수정하여 색상, 간격, 애니메이션 등을 커스터마이징할 수 있습니다.

### CSS 변수 수정 예시:

```css
:root {
    --primary: #your-color-here;
    --bg-primary: #your-bg-here;
    /* ... */
}
```

---

## 📦 파일 구조

```
examples/streamlit/
├── app_modern.py           # 메인 애플리케이션 (수정됨)
├── modern_theme.css        # 새로운 테마 CSS 파일
└── APPLY_NEW_THEME.md      # 이 파일
```

---

## ✅ 확인 사항

1. ✅ `modern_theme.css` 파일이 `examples/streamlit/` 디렉토리에 있는지 확인
2. ✅ `app_modern.py` 파일 상단에 `from pathlib import Path` import 추가
3. ✅ `apply_custom_styles()` 메서드 교체
4. ✅ Streamlit 앱 재시작

---

## 🚀 실행

```bash
streamlit run examples/streamlit/app_modern.py
```

---

## 💡 테마 전환 테스트

1. **시스템 설정으로 테스트**:
   - macOS: 시스템 환경설정 → 일반 → 외관 모드
   - Windows: 설정 → 개인 설정 → 색

2. **브라우저 개발자 도구로 테스트**:
   - F12 → 설정 → Emulate CSS media feature → `prefers-color-scheme: dark`

---

**⚠️ 주의**: 기존 cores/ 관련 기능은 **절대 수정하지 않았습니다**. 포트폴리오 관리 UI 디자인만 개선되었습니다.
