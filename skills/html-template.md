# 스킬: HTML 템플릿 생성

## 개요

에피소드 콘텐츠 JSON을 읽어 인스타그램용 HTML 슬라이드를 생성한다.
각 슬라이드는 하나의 `.slide` div이며, Playwright로 개별 PNG 캡처된다.

## 기본 HTML 구조

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>/* 디자인 시스템 CSS */</style>
</head>
<body>
  <div class="slide slide-thumbnail" id="slide-1">...</div>
  <div class="slide slide-concept" id="slide-2">...</div>
  <div class="slide slide-code" id="slide-3">...</div>
  <!-- ... 총 8개 -->
</body>
</html>
```

## CSS 디자인 시스템

### 기본 리셋 + 슬라이드 컨테이너
```css
* { margin: 0; padding: 0; box-sizing: border-box; }

.slide {
  width: 1080px;
  height: 1350px;
  position: relative;
  overflow: hidden;
  font-family: 'Noto Sans KR', sans-serif;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
}
```

### 배경 그라데이션 (슬라이드 타입별)
```css
.slide-thumbnail {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}
.slide-concept {
  background: linear-gradient(160deg, #0f0f23 0%, #1a1a3e 40%, #0d1b2a 100%);
}
.slide-code {
  background: linear-gradient(160deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
}
.slide-summary {
  background: linear-gradient(160deg, #1a0a2e 0%, #16213e 50%, #0a1628 100%);
}
```

### 장식 요소 (배경 원형 데코)
```css
.slide::before,
.slide::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  opacity: 0.06;
  pointer-events: none;
}
.slide::before {
  width: 500px; height: 500px;
  background: #667eea;
  top: -150px; right: -100px;
}
.slide::after {
  width: 350px; height: 350px;
  background: #f093fb;
  bottom: -100px; left: -80px;
}
```

### 상단 바 (2~8장 공통)
```css
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40px 60px 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.series-tag {
  font-size: 26px;
  font-weight: 700;
  color: #00ADD8;
}
.ep-num {
  font-size: 26px;
  font-weight: 700;
  color: rgba(255,255,255,0.4);
}
```

### 타이포그래피
```css
.slide-title {
  font-size: 48px;
  font-weight: 900;
  color: #ffffff;
  line-height: 1.3;
  margin-bottom: 24px;
}
.slide-subtitle {
  font-size: 32px;
  font-weight: 700;
  color: #00ADD8;
  margin-bottom: 20px;
}
.body-text {
  font-size: 30px;
  font-weight: 400;
  color: #e0e0e0;
  line-height: 1.6;
}
.muted-text {
  font-size: 26px;
  color: rgba(255,255,255,0.5);
}
```

### 코드 블록 스타일
```css
.code-block {
  background: #0d1117;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 32px;
  margin: 20px 0;
  position: relative;
  z-index: 1;
}
.code-block pre {
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px;
  line-height: 1.7;
  color: #e6edf3;
  white-space: pre;
  overflow: hidden;
}

/* 코드 색상 클래스 */
.kw  { color: #ff7b72; }  /* 키워드 */
.str { color: #a5d6ff; }  /* 문자열 */
.num { color: #79c0ff; }  /* 숫자 */
.cm  { color: #8b949e; }  /* 주석 */
.tp  { color: #7ee787; }  /* 타입 */
.fn  { color: #d2a8ff; }  /* 함수명 */
.op  { color: #ffa657; }  /* 연산자 */
```

### 하단 노트
```css
.note-box {
  background: rgba(0, 173, 216, 0.1);
  border-left: 4px solid #00ADD8;
  border-radius: 0 12px 12px 0;
  padding: 20px 28px;
  margin-top: 20px;
  position: relative;
  z-index: 1;
}
.note-box p {
  font-size: 26px;
  color: #e0e0e0;
  line-height: 1.5;
}
```

## 슬라이드 타입별 레이아웃

### 1장: thumbnail
```html
<div class="slide slide-thumbnail" id="slide-1">
  <div class="thumb-content">
    <p class="thumb-series">Go 기초 문법</p>
    <p class="thumb-sub">1분 정리 ⚡</p>
    <div class="thumb-divider"></div>
    <p class="thumb-ep">EP.08</p>
    <h1 class="thumb-topic">구조체 (Struct)</h1>
    <p class="thumb-hook">나만의 데이터 타입을 만들자! 🏗️</p>
  </div>
  <div class="thumb-tags">#Golang #개발 #프로그래밍</div>
</div>
```
```css
.thumb-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 80px 60px;
  position: relative;
  z-index: 1;
}
.thumb-series { font-size: 36px; font-weight: 700; color: rgba(255,255,255,0.9); }
.thumb-sub { font-size: 48px; font-weight: 900; color: #ffffff; margin-top: 8px; }
.thumb-divider {
  width: 80px; height: 4px;
  background: rgba(255,255,255,0.5);
  margin: 40px 0;
  border-radius: 2px;
}
.thumb-ep { font-size: 64px; font-weight: 900; color: #ffffff; }
.thumb-topic { font-size: 56px; font-weight: 900; color: #ffffff; margin-top: 16px; }
.thumb-hook { font-size: 32px; color: rgba(255,255,255,0.8); margin-top: 32px; }
.thumb-tags {
  text-align: center;
  padding: 40px;
  font-size: 24px;
  color: rgba(255,255,255,0.4);
  position: relative;
  z-index: 1;
}
```

### 2장: concept
```html
<div class="slide slide-concept" id="slide-2">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">EP.08</span>
  </div>
  <div class="concept-body">
    <h2 class="slide-title">구조체란? 🤔</h2>
    <div class="concept-explain">
      <p class="body-text">여러 데이터를 하나로 묶는 타입</p>
      <p class="body-text">이름표 붙은 서랍장과 같아요! 🗄️</p>
    </div>
    <div class="concept-compare">
      <p class="muted-text">다른 언어에서는?</p>
      <p class="body-text">→ Java/C#: class</p>
      <p class="body-text">→ Python: dataclass</p>
    </div>
    <div class="concept-features">
      <p class="slide-subtitle">Go 구조체의 특징</p>
      <p class="body-text">→ type + struct로 선언 ✅</p>
      <p class="body-text">→ 클래스 대신 구조체 사용! ⭐</p>
      <p class="body-text">→ 메서드를 붙일 수 있음 💡</p>
    </div>
  </div>
</div>
```

### 3~7장: code
```html
<div class="slide slide-code" id="slide-3">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">EP.08</span>
  </div>
  <div class="code-body">
    <h2 class="slide-subtitle">구조체 선언과 생성</h2>
    <div class="code-block">
      <pre><!-- 색상 span이 적용된 코드 --></pre>
    </div>
    <div class="note-box">
      <p>💡 필드명 지정 방식을 권장해요!</p>
    </div>
  </div>
</div>
```

### 8장: summary
```html
<div class="slide slide-summary" id="slide-8">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">EP.08</span>
  </div>
  <div class="summary-body">
    <h2 class="slide-subtitle">📌 핵심 정리</h2>
    <div class="summary-points">
      <p class="body-text">✅ type으로 구조체 정의</p>
      <!-- ... -->
    </div>
    <div class="summary-tips">
      <h3 class="slide-subtitle">💡 Go만의 꿀팁</h3>
      <p class="body-text">✅ 대문자 필드 = 외부 공개</p>
      <!-- ... -->
    </div>
    <div class="summary-next">
      <p class="body-text">👉 다음 편 EP.09 포인터</p>
    </div>
    <div class="summary-cta">
      <p>💾 저장 | ❤️ 좋아요 | 👤 팔로우</p>
    </div>
  </div>
</div>
```

## 코드 구문 하이라이팅 규칙

코드를 HTML로 변환할 때 아래 규칙으로 `<span>` 태그를 적용한다:

```python
# generate_html.py 에서 사용하는 변환 로직 요약

KEYWORDS = ['func', 'var', 'const', 'if', 'else', 'for', 'range',
            'return', 'type', 'struct', 'switch', 'case', 'default',
            'defer', 'go', 'chan', 'select', 'import', 'package',
            'map', 'make', 'append', 'len', 'cap', 'delete',
            'nil', 'true', 'false', 'break', 'continue', 'fallthrough']

TYPES = ['string', 'int', 'int8', 'int16', 'int32', 'int64',
         'uint', 'uint8', 'uint16', 'uint32', 'uint64',
         'float32', 'float64', 'bool', 'byte', 'rune', 'error',
         'any', 'interface']

# 주석: // 로 시작하는 줄 전체를 .cm 으로 감싸기
# 문자열: "..." 또는 `...` 를 .str 으로 감싸기
# 숫자: 단독 숫자 리터럴을 .num 으로 감싸기
# 키워드: 단어 경계 기준으로 .kw 감싸기
# 타입: 단어 경계 기준으로 .tp 감싸기
# 함수명: func 뒤의 이름, 또는 .메서드() 패턴의 이름을 .fn 감싸기
```

## 폰트 로딩 주의사항

Playwright에서 웹폰트가 로드되기 전에 스크린샷을 찍으면 기본 폰트로 렌더링된다.
반드시 `page.wait_for_timeout(2000)` 또는 폰트 로드 완료 대기 로직을 포함해야 한다.

## 접근성 및 가독성 체크리스트

- [ ] 모든 텍스트가 배경과 충분한 대비를 가지는가?
- [ ] 코드 폰트가 26px 이상인가?
- [ ] 한 줄에 40자를 초과하는 코드가 없는가?
- [ ] 이모지가 깨지지 않고 표시되는가?
- [ ] 한글 글꼴이 정상 로드되었는가?
