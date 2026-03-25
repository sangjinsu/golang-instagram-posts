#!/usr/bin/env python3
"""generate_html.py — 에피소드 JSON → HTML 슬라이드 변환

에피소드 콘텐츠 JSON 파일을 읽어 인스타그램용 HTML 슬라이드를 생성한다.
각 슬라이드는 .slide div이며, Playwright로 개별 PNG 캡처된다.

사용법:
    python scripts/generate_html.py --ep 08
    python scripts/generate_html.py --ep 08 --preview
"""

import json
import re
import os
import sys
import argparse
import webbrowser

# ============================================================
# Go 언어 토큰 정의
# ============================================================

KEYWORDS = {
    'func', 'var', 'const', 'if', 'else', 'for', 'range',
    'return', 'type', 'struct', 'switch', 'case', 'default',
    'defer', 'go', 'chan', 'select', 'import', 'package',
    'map', 'make', 'append', 'len', 'cap', 'delete',
    'nil', 'true', 'false', 'break', 'continue', 'fallthrough',
}

BUILTIN_TYPES = {
    'string', 'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64',
    'float32', 'float64', 'bool', 'byte', 'rune', 'error',
    'any', 'interface',
}

TWO_CHAR_OPS = {':=', '==', '!=', '<=', '>=', '<-', '*=', '+=', '-=', '/=', '&&', '||'}
ONE_CHAR_OPS = set('=<>+-*/%!&|^')


# ============================================================
# 유틸리티
# ============================================================

def esc(text):
    """HTML 특수문자 이스케이프"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


# ============================================================
# Go 코드 구문 하이라이팅
# ============================================================

def extract_user_types(slides):
    """코드 슬라이드에서 type X struct 패턴으로 사용자 정의 타입 추출"""
    types = set()
    for slide in slides:
        if slide['type'] == 'code':
            for m in re.finditer(r'\btype\s+(\w+)\s+struct\b', slide['content']['code']):
                types.add(m.group(1))
    return types


def highlight_line(line, all_types):
    """한 줄의 Go 코드에 구문 하이라이팅 HTML 적용"""
    stripped = line.lstrip()

    # 전체 줄 주석
    if stripped.startswith('//'):
        return f'<span class="cm">{esc(line)}</span>'

    result = []
    pos = 0
    n = len(line)

    while pos < n:
        ch = line[pos]

        # 인라인 주석
        if ch == '/' and pos + 1 < n and line[pos + 1] == '/':
            result.append(f'<span class="cm">{esc(line[pos:])}</span>')
            break

        # 문자열 리터럴 "..."
        if ch == '"':
            end = pos + 1
            while end < n:
                if line[end] == '\\' and end + 1 < n:
                    end += 2
                elif line[end] == '"':
                    end += 1
                    break
                else:
                    end += 1
            result.append(f'<span class="str">{esc(line[pos:end])}</span>')
            pos = end
            continue

        # 백틱 문자열 `...`
        if ch == '`':
            end = line.find('`', pos + 1)
            end = (end + 1) if end != -1 else n
            result.append(f'<span class="str">{esc(line[pos:end])}</span>')
            pos = end
            continue

        # 식별자 / 키워드 / 타입 / 함수명
        if ch.isalpha() or ch == '_':
            m = re.match(r'[a-zA-Z_]\w*', line[pos:])
            word = m.group()
            word_end = pos + len(word)

            if word in KEYWORDS:
                result.append(f'<span class="kw">{word}</span>')
            elif word in all_types:
                result.append(f'<span class="tp">{word}</span>')
            elif word_end < n and line[word_end] == '(':
                result.append(f'<span class="fn">{word}</span>')
            else:
                result.append(esc(word))

            pos = word_end
            continue

        # 숫자 리터럴
        if ch.isdigit():
            m = re.match(r'\d+\.?\d*', line[pos:])
            result.append(f'<span class="num">{m.group()}</span>')
            pos += len(m.group())
            continue

        # 2문자 연산자
        if pos + 1 < n and line[pos:pos + 2] in TWO_CHAR_OPS:
            result.append(f'<span class="op">{esc(line[pos:pos + 2])}</span>')
            pos += 2
            continue

        # 1문자 연산자
        if ch in ONE_CHAR_OPS:
            result.append(f'<span class="op">{esc(ch)}</span>')
            pos += 1
            continue

        # 기타 (공백, 괄호, 점 등)
        result.append(esc(ch))
        pos += 1

    return ''.join(result)


def highlight_code(code, user_types):
    """Go 코드 전체에 구문 하이라이팅 적용"""
    all_types = BUILTIN_TYPES | user_types
    return '\n'.join(highlight_line(line, all_types) for line in code.split('\n'))


# ============================================================
# CSS 디자인 시스템
# ============================================================

CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  padding: 40px;
}

/* 슬라이드 컨테이너 */
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

/* 배경 그라데이션 */
.slide-thumbnail { background: linear-gradient(135deg, #0f0f23 0%, #0a3d5c 40%, #00ADD8 100%); }
.slide-concept   { background: linear-gradient(160deg, #0f0f23 0%, #1a1a3e 40%, #0d1b2a 100%); }
.slide-code      { background: linear-gradient(160deg, #0d1117 0%, #161b22 50%, #0d1117 100%); }
.slide-summary   { background: linear-gradient(160deg, #1a0a2e 0%, #16213e 50%, #0a1628 100%); }

/* 장식 원 */
.slide::before, .slide::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  opacity: 0.06;
  pointer-events: none;
}
.slide::before { width: 500px; height: 500px; background: #667eea; top: -150px; right: -100px; }
.slide::after  { width: 350px; height: 350px; background: #f093fb; bottom: -100px; left: -80px; }

/* 상단 바 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40px 60px 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.series-tag { font-size: 26px; font-weight: 700; color: #00ADD8; }
.ep-num     { font-size: 26px; font-weight: 700; color: rgba(255,255,255,0.4); }

/* 타이포그래피 */
.slide-title    { font-size: 48px; font-weight: 900; color: #fff; line-height: 1.3; margin-bottom: 24px; }
.slide-subtitle { font-size: 32px; font-weight: 700; color: #00ADD8; margin-bottom: 20px; }
.body-text      { font-size: 30px; font-weight: 400; color: #e0e0e0; line-height: 1.6; }
.muted-text     { font-size: 26px; color: rgba(255,255,255,0.5); margin-bottom: 12px; }

/* 코드 블록 */
.code-block {
  background: #0d1117;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 32px;
  margin: 20px 0;
  position: relative;
  z-index: 1;
  flex: 1;
}
.code-block pre {
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px;
  line-height: 1.7;
  color: #e6edf3;
  white-space: pre;
  overflow: hidden;
}

/* 코드 구문 색상 */
.kw  { color: #ff7b72; }
.str { color: #a5d6ff; }
.num { color: #79c0ff; }
.cm  { color: #8b949e; }
.tp  { color: #7ee787; }
.fn  { color: #d2a8ff; }
.op  { color: #ffa657; }

/* 노트 박스 */
.note-box {
  background: rgba(0, 173, 216, 0.1);
  border-left: 4px solid #00ADD8;
  border-radius: 0 12px 12px 0;
  padding: 20px 28px;
  margin-top: auto;
  position: relative;
  z-index: 1;
}
.note-box p { font-size: 26px; color: #e0e0e0; line-height: 1.5; }

/* === 썸네일 === */
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
.thumb-series  { font-size: 36px; font-weight: 700; color: rgba(255,255,255,0.9); }
.thumb-sub     { font-size: 48px; font-weight: 900; color: #fff; margin-top: 8px; }
.thumb-divider { width: 80px; height: 4px; background: rgba(255,255,255,0.5); margin: 40px 0; border-radius: 2px; }
.thumb-ep      { font-size: 64px; font-weight: 900; color: #fff; }
.thumb-topic   { font-size: 56px; font-weight: 900; color: #fff; margin-top: 16px; }
.thumb-hook    { font-size: 32px; color: rgba(255,255,255,0.8); margin-top: 32px; }
.thumb-tags    { text-align: center; padding: 40px; font-size: 24px; color: rgba(255,255,255,0.4); position: relative; z-index: 1; }

/* === 컨셉 === */
.concept-body     { flex: 1; padding: 20px 60px 40px; display: flex; flex-direction: column; gap: 28px; position: relative; z-index: 1; }
.concept-explain  { }
.concept-compare  { background: rgba(255,255,255,0.04); border-radius: 16px; padding: 24px 28px; }
.concept-features { background: rgba(0,173,216,0.08); border-radius: 16px; padding: 24px 28px; }

/* === 코드 바디 === */
.code-body { flex: 1; padding: 10px 60px 40px; display: flex; flex-direction: column; position: relative; z-index: 1; }

/* === 요약 === */
.summary-body   { flex: 1; padding: 20px 60px 40px; display: flex; flex-direction: column; gap: 24px; position: relative; z-index: 1; }
.summary-points,
.summary-tips   { background: rgba(255,255,255,0.04); border-radius: 16px; padding: 24px 28px; }
.summary-next   { text-align: center; padding: 20px; background: rgba(0,173,216,0.08); border-radius: 16px; }
.summary-cta    { text-align: center; padding: 24px; font-size: 28px; color: rgba(255,255,255,0.6); position: relative; z-index: 1; }
"""


# ============================================================
# 슬라이드 렌더링
# ============================================================

def render_thumbnail(content):
    """1장: 썸네일"""
    return f'''<div class="slide slide-thumbnail" id="slide-1">
  <div class="thumb-content">
    <p class="thumb-series">{esc(content["series_name"])}</p>
    <p class="thumb-sub">{esc(content["series_sub"])}</p>
    <div class="thumb-divider"></div>
    <p class="thumb-ep">{esc(content["ep_label"])}</p>
    <h1 class="thumb-topic">{esc(content["topic"])}</h1>
    <p class="thumb-hook">{esc(content["hook"])}</p>
  </div>
  <div class="thumb-tags">#Golang #개발 #프로그래밍</div>
</div>'''


def render_concept(content, ep_label):
    """2장: 핵심 개념"""
    explain = '\n'.join(
        f'      <p class="body-text">{esc(line)}</p>'
        for line in content['explanation']
    )

    compare_html = ''
    if 'comparison' in content:
        comp = content['comparison']
        items = '\n'.join(
            f'      <p class="body-text">\u2192 {esc(item)}</p>'
            for item in comp['items']
        )
        compare_html = f'''
    <div class="concept-compare">
      <p class="muted-text">{esc(comp["label"])}</p>
{items}
    </div>'''

    feat = content['features']
    feat_items = '\n'.join(
        f'      <p class="body-text">\u2192 {esc(item)}</p>'
        for item in feat['items']
    )
    features_html = f'''
    <div class="concept-features">
      <p class="slide-subtitle">{esc(feat["label"])}</p>
{feat_items}
    </div>'''

    return f'''<div class="slide slide-concept" id="slide-2">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">{esc(ep_label)}</span>
  </div>
  <div class="concept-body">
    <h2 class="slide-title">{esc(content["question"])}</h2>
    <div class="concept-explain">
{explain}
    </div>{compare_html}{features_html}
  </div>
</div>'''


def render_code_slide(content, ep_label, slide_number, user_types):
    """3~7장: 코드"""
    highlighted = highlight_code(content['code'], user_types)

    note_html = ''
    if 'note' in content:
        note_html = f'''
    <div class="note-box">
      <p>{esc(content["note"])}</p>
    </div>'''

    return f'''<div class="slide slide-code" id="slide-{slide_number}">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">{esc(ep_label)}</span>
  </div>
  <div class="code-body">
    <h2 class="slide-subtitle">{esc(content["title"])}</h2>
    <div class="code-block">
      <pre>{highlighted}</pre>
    </div>{note_html}
  </div>
</div>'''


def render_summary(content, ep_label, slide_number=9):
    """마지막 장: 요약"""
    points = '\n'.join(
        f'      <p class="body-text">{esc(p)}</p>'
        for p in content['points']
    )
    tips = '\n'.join(
        f'      <p class="body-text">{esc(t)}</p>'
        for t in content['tips']
    )

    return f'''<div class="slide slide-summary" id="slide-{slide_number}">
  <div class="top-bar">
    <span class="series-tag">Go 1분 정리</span>
    <span class="ep-num">{esc(ep_label)}</span>
  </div>
  <div class="summary-body">
    <h2 class="slide-subtitle">📌 핵심 정리</h2>
    <div class="summary-points">
{points}
    </div>
    <div class="summary-tips">
      <h3 class="slide-subtitle">💡 Go만의 꿀팁</h3>
{tips}
    </div>
    <div class="summary-next">
      <p class="body-text">{esc(content["next_preview"])}</p>
    </div>
    <div class="summary-cta">
      <p>{esc(content["cta"])}</p>
    </div>
  </div>
</div>'''


# ============================================================
# HTML 문서 생성
# ============================================================

def generate_html(data):
    """에피소드 JSON 데이터로 완전한 HTML 문서 생성"""
    ep_label = f'EP.{data["episode"]:02d}'
    slides = data['slides']
    user_types = extract_user_types(slides)

    slide_htmls = []
    for slide in slides:
        stype = slide['type']
        content = slide['content']
        snum = slide['slide_number']

        if stype == 'thumbnail':
            slide_htmls.append(render_thumbnail(content))
        elif stype == 'concept':
            slide_htmls.append(render_concept(content, ep_label))
        elif stype == 'code':
            slide_htmls.append(render_code_slide(content, ep_label, snum, user_types))
        elif stype == 'summary':
            slide_htmls.append(render_summary(content, ep_label, snum))

    slides_joined = '\n\n'.join(slide_htmls)

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080">
  <title>EP.{data["episode"]:02d} {data["title"]} ({data["title_en"]})</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
{CSS}
  </style>
</head>
<body>

{slides_joined}

</body>
</html>
'''


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='에피소드 JSON → HTML 슬라이드 변환')
    parser.add_argument('--ep', required=True, help='에피소드 번호 (예: 08)')
    parser.add_argument('--preview', action='store_true', help='생성 후 브라우저에서 미리보기')
    args = parser.parse_args()

    ep_num = int(args.ep)
    json_path = os.path.join('episodes', f'ep{ep_num:02d}.json')
    html_path = os.path.join('episodes', f'ep{ep_num:02d}.html')

    if not os.path.exists(json_path):
        print(f'  \u274c {json_path} 파일을 찾을 수 없습니다.')
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    html = generate_html(data)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    slide_count = len(data['slides'])
    print(f'  \u2705 EP.{ep_num:02d} HTML 생성 완료 ({slide_count}장)')
    print(f'  \U0001f4c1 {html_path}')

    if args.preview:
        abs_path = os.path.abspath(html_path)
        webbrowser.open(f'file://{abs_path}')
        print(f'  \U0001f310 브라우저에서 미리보기 열기')


if __name__ == '__main__':
    main()
