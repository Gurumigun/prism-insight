# 🎨 모던 다크/라이트 테마 시스템

PRISM-INSIGHT 포트폴리오 관리 도구의 모던 테마 시스템입니다.

---

## ✨ 주요 특징

### 🌓 자동 다크/라이트 모드
- 시스템 설정에 따라 자동으로 테마 전환
- CSS `prefers-color-scheme` 미디어 쿼리 활용
- 부드러운 전환 애니메이션 (0.3초)

### 🎨 CSS 변수 기반 테마
- 42개 CSS 변수로 전체 디자인 제어
- 쉬운 커스터마이징
- 일관된 디자인 시스템

### 💎 모던 디자인 요소
- **Glass Morphism**: 투명 효과 + 블러
- **그라데이션**: 버튼, 제목, 배경
- **부드러운 애니메이션**: Hover, Click, Loading
- **개선된 그림자**: 깊이감 있는 디자인

### ♿ 접근성
- WCAG 2.1 AA 준수
- 명확한 포커스 인디케이터
- 높은 색상 대비율
- 키보드 네비게이션 지원

---

## 📂 파일 구조

```
examples/streamlit/
├── app_modern.py              # 메인 앱 (테마 로더)
├── modern_theme.css           # 🆕 테마 CSS 파일
├── app_modern.py.backup       # 백업 파일
├── README_THEME.md            # 이 파일
├── APPLY_NEW_THEME.md         # 적용 가이드
└── THEME_CHANGELOG.md         # 변경 이력
```

---

## 🚀 빠른 시작

### 1. 파일 확인
```bash
cd /Users/1004440/prism-insight/examples/streamlit
ls modern_theme.css  # 파일 존재 확인
```

### 2. 앱 실행
```bash
streamlit run app_modern.py
```

### 3. 테마 확인
- **자동**: 시스템 설정에 따라 테마 자동 적용
- **수동 테스트**: 시스템 설정에서 다크 모드 on/off

---

## 🎨 테마 미리보기

### 라이트 모드
```
배경: 흰색 → 밝은 회색 그라데이션
텍스트: 진한 회색/검정
Primary: 밝은 파란색 (#0EA5E9)
카드: 유리 효과 (흰색 85% 투명도)
```

### 다크 모드
```
배경: 진한 네이비 그라데이션
텍스트: 밝은 회색/흰색
Primary: 밝은 스카이블루 (#38BDF8)
카드: 유리 효과 (어두운 회색 85% 투명도)
```

---

## 🔧 커스터마이징

### 색상 변경
`modern_theme.css` 파일의 CSS 변수를 수정하세요:

```css
:root {
    --primary: #YOUR_COLOR;           /* Primary 색상 */
    --bg-primary: #YOUR_BG_COLOR;     /* 배경색 */
    --text-primary: #YOUR_TEXT_COLOR; /* 텍스트색 */
}
```

### 애니메이션 속도 조정
```css
* {
    transition: all 0.3s ease;  /* 0.3s를 원하는 속도로 */
}
```

### 그림자 강도 변경
```css
:root {
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);  /* 투명도 조정 */
}
```

---

## 📊 성능

### Before (인라인 CSS)
- 파일 크기: 2,383줄
- CSS 재사용: ❌
- 브라우저 캐싱: ❌
- 유지보수: 어려움

### After (외부 CSS)
- 파일 크기: 2,007줄 (-16%)
- CSS 재사용: ✅
- 브라우저 캐싱: ✅
- 유지보수: 간편

---

## 🐛 문제 해결

### CSS가 적용되지 않아요
1. `modern_theme.css` 파일이 `examples/streamlit/` 폴더에 있는지 확인
2. 브라우저 캐시 삭제 (Ctrl+F5 또는 Cmd+Shift+R)
3. Streamlit 앱 재시작

### 다크 모드가 작동하지 않아요
1. 시스템 다크 모드 설정 확인
2. 브라우저가 `prefers-color-scheme` 지원하는지 확인 (Chrome 76+, Safari 12.1+)
3. 개발자 도구에서 수동으로 테스트:
   ```
   F12 → ⚙️ 설정 → Rendering → Emulate CSS media feature prefers-color-scheme
   ```

### Fallback CSS가 표시되요
- `modern_theme.css` 파일 경로 확인
- 파일 권한 확인 (`chmod 644 modern_theme.css`)

---

## 📚 추가 문서

- **[APPLY_NEW_THEME.md](./APPLY_NEW_THEME.md)**: 테마 적용 가이드
- **[THEME_CHANGELOG.md](./THEME_CHANGELOG.md)**: 상세 변경 이력
- **[modern_theme.css](./modern_theme.css)**: 테마 소스 코드

---

## 🎯 적용된 컴포넌트

### ✅ 스타일링 완료
- [x] 버튼 (Gradient + Ripple)
- [x] 입력 필드 (Focus 효과)
- [x] 카드 (Glass morphism)
- [x] 테이블 (Gradient 헤더)
- [x] 탭 (선택 시 Gradient)
- [x] 알림 메시지 (Backdrop blur)
- [x] 메트릭 카드 (Hover 효과)
- [x] 프로그레스 바 (Glow 효과)
- [x] 스크롤바 (커스텀 스타일)
- [x] 링크 (Underline 애니메이션)

---

## 🌈 색상 팔레트

### Primary Colors
| 모드 | 색상 | Hex | 용도 |
|------|------|-----|------|
| Light | Sky Blue | #0EA5E9 | 버튼, 링크 |
| Dark | Bright Sky | #38BDF8 | 버튼, 링크 |

### Semantic Colors
| 의미 | Light | Dark | 용도 |
|------|-------|------|------|
| Success | #10B981 | #6EE7B7 | 성공 메시지 |
| Error | #EF4444 | #FCA5A5 | 오류 메시지 |
| Warning | #F59E0B | #FCD34D | 경고 메시지 |
| Info | #3B82F6 | #93C5FD | 정보 메시지 |

---

## 🎭 브라우저 호환성

| 브라우저 | 버전 | 지원 |
|---------|------|------|
| Chrome | 76+ | ✅ 완전 지원 |
| Firefox | 67+ | ✅ 완전 지원 |
| Safari | 12.1+ | ✅ 완전 지원 |
| Edge | 79+ | ✅ 완전 지원 |

---

## 💡 팁

### 테마 강제 설정
시스템 설정 무시하고 특정 테마 사용:

```html
<!-- modern_theme.css에 추가 -->
:root {
    /* 다크 모드 강제 */
    --primary: #38BDF8;
    --bg-primary: #0F172A;
    /* ... */
}
```

### 애니메이션 비활성화
모션을 선호하지 않는 사용자를 위한 설정:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}
```

---

## ⚠️ 주의사항

### ✅ 안전
- 포트폴리오 관리 UI만 변경
- cores/ 폴더 **절대 미수정**
- AI 분석 기능 **정상 작동**
- 기존 데이터 **완전 호환**

### 🚫 금지
- cores/ 폴더 수정 금지
- AI 분석 로직 변경 금지
- 데이터베이스 스키마 변경 금지

---

## 🙏 크레딧

- **디자인 시스템**: Tailwind CSS 색상 팔레트 참고
- **아이콘**: Emoji (시스템 기본)
- **폰트**: Pretendard (시스템 폴백)
- **애니메이션**: CSS3 Transitions & Keyframes

---

## 📞 지원

문제가 있으신가요?

1. **문서 확인**: `APPLY_NEW_THEME.md`, `THEME_CHANGELOG.md`
2. **백업 복구**: `app_modern.py.backup`으로 롤백 가능
3. **Issue 등록**: GitHub Issues에 문의

---

## 📝 버전

- **Current**: 1.0.0
- **Release Date**: 2025-11-12
- **Compatibility**: app_modern.py (feature/custom 브랜치)

---

**🎨 Enjoy your modern theme!**
