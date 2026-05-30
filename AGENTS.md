# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 프로젝트 개요

**GeekNews Daily Card News** - 하루 1개 인스타그램 카드뉴스 생성/업로드 시스템

한국 개발자 커뮤니티를 위한 **GeekNews 주간 픽** 카드뉴스를 매주 7개씩 만들고, 하루 1개씩 발행하는 운영을 기본값으로 둔다.

**현재 운영 목표**:
- GeekNews only
- 하루 1개 발행
- 주 7개 카드뉴스 사전 생성
- 월 28~31개 포스트 유지
- 매주 후보 10개 이상 확보 후 7개 선별

**핵심 워크플로우:**
```
GeekNews 후보 수집 → 7개 기사 선별 → JSON 생성/검증 → HTML 생성 → PNG 변환 → dry-run/업로드
```

## GeekNews Daily 슬라이드 구조

GeekNews 카드뉴스는 3~9장 가변 구조를 지원하지만, daily 운영의 기본은 5장 구성이다:

| 장 | 타입 | 내용 |
|----|------|------|
| 1장 | `news-thumbnail` | 주제 + 한줄 훅 + 주차/기사 번호 |
| 2장 | `news-summary` | 핵심 포인트 3~5개 |
| 3장 | `news-why` | 왜 중요한지, 통계/연구/시장 맥락 |
| 4장 | `news-detail` | 실무 사례, 적용 포인트, 주의사항 |
| 5장 | `news-closing` | 핵심 정리 + 원문 링크 + CTA |

## Legacy Go EP 트랙

기존 Go 기초 문법 콘텐츠(`ep08`~`ep21`)와 `--ep` 기반 생성/업로드 경로는 보존한다. 단, 신규 기본 운영 대상은 GeekNews이며 Go EP는 명시 요청이 있을 때만 다룬다.

## 디자인 스펙

### 크기
- **1080 x 1350px** (인스타 4:5 세로형)

### 폰트
- 제목/본문: **Noto Sans KR** (400, 700, 900)
- 코드: **JetBrains Mono** (400, 600)
- 웹폰트 CDN 사용 (Google Fonts)

### 색상 시스템
```
배경:
  primary:    #0f0f23 (딥 네이비)
  secondary:  #161b22 (다크 그레이)
  accent-bg:  #1a1a3e (퍼플 네이비)

텍스트:
  heading:    #ffffff
  body:       #e0e0e0
  muted:      rgba(255,255,255,0.5)

강조:
  go-blue:    #00ADD8 (Go 공식 컬러)
  purple:     #667eea
  pink:       #f093fb
  green:      #7ee787
  orange:     #ffa657
  yellow:     #e3b341

코드 배경:
  code-bg:    #0d1117
  code-border: rgba(255,255,255,0.1)
```

### 코드 표현 규칙
- 코드 하이라이팅 라이브러리 사용하지 않음
- 대신 CSS로 직접 색상 클래스 적용:
  - 키워드(func, var, if 등): `#ff7b72` (코랄)
  - 문자열: `#a5d6ff` (하늘색)
  - 숫자: `#79c0ff` (파란색)
  - 주석: `#8b949e` (회색)
  - 타입(string, int 등): `#7ee787` (초록)
  - 함수명: `#d2a8ff` (보라)
- 코드 폰트 크기: 28~32px
- 한 슬라이드 최대 15줄

### 레이아웃 공통
- 상단 바: 시리즈 태그(좌) + 주차/기사 번호(우)
- 콘텐츠 좌우 패딩: 60px
- 코드 블록: 둥근 모서리(16px), 내부 패딩 32px
- 장식 원: 반투명 그라데이션 원 2~3개 (배경 데코)

## 기술 스택

### HTML → PNG 변환
- **Playwright (Python)** 사용
- Chromium 헤드리스 브라우저
- 각 슬라이드(`.slide` div)를 개별 PNG로 캡처

### 파일 구조
```
go-insta-content/
├── AGENTS.md              ← 이 파일
├── skills/
│   ├── slide-content.md   ← 콘텐츠 작성 규칙
│   ├── html-template.md   ← HTML/CSS 템플릿 가이드
│   └── image-export.md    ← 이미지 변환 가이드
├── templates/
│   └── base.html          ← 기본 HTML 템플릿
├── episodes/
│   ├── gn_YYYY_wWW_NN.json  ← GeekNews daily 카드뉴스 JSON
│   ├── gn_YYYY_wWW_NN.html  ← GeekNews generated HTML
│   └── epNN.json/html       ← legacy Go EP 콘텐츠
├── .env                   ← API 키 (UPLOAD_POST_API_KEY 등)
├── .venv/                 ← Python 가상환경 (pip3 설치용)
├── output/
│   └── gn_YYYY_wWW_NN/     ← 카드뉴스별 slide_01~NN.png
└── scripts/
    ├── geeknews_pipeline.py ← GeekNews 주간 7개 배치 생성
    ├── generate_html.py   ← JSON → HTML 변환
    ├── export_images.py   ← HTML → PNG 변환
    └── upload_instagram.py ← 인스타그램 업로드
```

## 작업 명령어

> **주의**: macOS 환경에서 `python` 명령이 없을 수 있음. 반드시 `python3`을 사용할 것.

### 환경 설정
- **Python 가상환경**: `.venv/` 디렉토리에 venv가 존재함. macOS의 externally-managed-environment 제한으로 시스템 pip 사용 불가.
- **패키지 설치**: 반드시 venv를 활성화한 후 설치할 것.
- **환경변수**: `.env` 파일에 `UPLOAD_POST_API_KEY` 등 API 키가 저장되어 있음. 스크립트 실행 전 `source .env` 필요.

```bash
# venv 활성화 + .env 로드
source .venv/bin/activate && source .env

# 패키지 설치 (venv 활성화 후)
pip3 install <패키지명>
```

### GeekNews 주간 7개 배치 생성
```bash
# 1. 최신 GeekNews 후보 수집
python3 scripts/geeknews_pipeline.py --week latest --scrape-only

# 2. 7일치 카드뉴스 생성 + HTML/PNG 빌드 (업로드 없음)
python3 scripts/geeknews_pipeline.py --week latest --count 7 --dry-run

# 3. JSON만 생성하고 수동 검토
python3 scripts/geeknews_pipeline.py --week latest --count 7 --json-only
```

### 개별 단계 실행
```bash
# GeekNews HTML만 미리보기
python3 scripts/generate_html.py --id gn_2026_w15_01 --preview

# 특정 슬라이드만 재생성
python3 scripts/export_images.py --id gn_2026_w15_01 --slide 3

# Legacy Go EP 경로 (명시 요청 시만)
python3 scripts/generate_html.py --ep 21
python3 scripts/export_images.py --ep 21
```

### 인스타그램 업로드
```bash
# venv + .env 필수
source .venv/bin/activate && source .env

# GeekNews dry-run (파라미터 확인만)
python3 scripts/upload_instagram.py --id gn_2026_w15_01 --auto-caption --dry-run

# 실제 업로드
python3 scripts/upload_instagram.py --id gn_2026_w15_01 --auto-caption

# 예약 업로드
python3 scripts/upload_instagram.py --id gn_2026_w15_01 --auto-caption \
  --schedule "2026-06-01T09:00:00" --timezone "Asia/Seoul"

# 업로드 상태 확인
python3 scripts/upload_instagram.py --status <request_id>
```

## GeekNews 카드뉴스 생성 프로세스

GeekNews 기사 카드뉴스 JSON을 생성할 때 반드시 아래 프로세스를 따른다.

### 1단계: 기사 선정
- `python3 scripts/geeknews_pipeline.py --week latest --scrape-only`로 기사 목록 수집
- daily 운영 기본값은 `--count 7`이며, 하루 1개씩 7일치 카드뉴스를 생성한다
- 매주 후보 10개 이상을 확인하고, 기존 `episodes/gn_*.json`과 중복되지 않는 기사 7개를 선정한다
- 품질 저하/중복에 대비해 예비 후보 2~3개를 별도로 유지한다
- 선호 주제: 개발자 생산성, AI/ML 실전 활용, 프로그래밍 언어/프레임워크, 소프트웨어 엔지니어링

### 2단계: 웹 리서치 (필수)
선정된 기사에 대해 반드시 웹 조사를 수행한다:
1. **GeekNews 원문**: WebFetch로 GeekNews URL에서 전체 요약 + 커뮤니티 댓글 수집
2. **원본 소스**: WebFetch로 원문 기사 전문 확인
3. **관련 자료 검색**: WebSearch로 관련 통계, 연구 결과, 전문가 의견, 실제 사례 조사
4. **리서치 정리**: 최소 5개 구체적 데이터 포인트 확보

### 3단계: JSON 생성
리서치 결과를 반영하여 콘텐츠 품질 기준을 충족하는 JSON 생성:
- **news-summary**: 리서치에서 발견한 구체적 사실 포함 (제네릭 설명 금지)
- **news-why**: `points` 배열에 최소 1개 통계/연구 결과 필수
- **news-detail**: 실전 사례 + 실무 맥락 포함
- **news-thumbnail**: 주제에 맞는 이모지 `icon` 필드 포함

### 4단계: HTML → PNG → 업로드
```bash
python3 scripts/generate_html.py --id {content_id}
python3 scripts/export_images.py --id {content_id}
python3 scripts/upload_instagram.py --id {content_id} --auto-caption --dry-run
```

## 콘텐츠 작성 원칙

1. **한국어 중심**: 모든 설명은 한국어, 코드 주석도 한국어
2. **GeekNews 기본 운영**: 하루 1개 발행을 기준으로 주 7개를 사전 생성
3. **리서치 기반**: 숫자, 제품명, 연구 결과, 실제 사례를 최소 5개 이상 확보
4. **실무 연결**: 한국 개발자가 바로 판단하거나 적용할 수 있는 맥락 포함
5. **이모지 적극 활용**: 시각적 구분과 친근함을 위해 사용
6. **Go EP 전용 규칙**: Go 에피소드 요청이 있을 때만 Go 철학과 코드 제약을 적용

## 주의사항

- 인스타그램 이미지이므로 테이블, 복잡한 레이아웃 사용 금지
- 모바일에서 보기 때문에 글자 크기 최소 24px 이상
- 코드 블록 내 한 줄 최대 40자 권장 (가로 스크롤 방지)
- GeekNews 카드 간 시각적 일관성 유지
- 각 슬라이드는 독립적으로 이해 가능해야 함

---

## 하네스: Card News Pipeline

**목표:** GeekNews 주간 픽(gn_) 카드뉴스를 하루 1개 발행 기준으로 콘텐츠 작성 → 검증 → HTML/PNG 빌드 → 시각 QA → 인스타그램 업로드까지 5인 에이전트 팀으로 조율. Go EP 트랙은 legacy로 보존하며 명시 요청 시만 처리한다.

**트리거:** 카드뉴스 파이프라인 관련 요청(GeekNews 주간 7개 배치 생성/빌드/수정/재빌드/업로드, 특정 슬라이드 재생성, legacy Go EP 명시 요청 등) 시 `orchestrate-pipeline` 스킬을 사용하라. 단순 JSON/스키마 질문이나 개별 스크립트 한 줄 실행만 필요한 경우는 예외.

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-04-09 | 초기 구성 | `.Codex/agents/` 5개 + `.Codex/skills/orchestrate-pipeline/` + 이 포인터 | 파이프라인 조율 팀 신설 요청. 기존 `go-episode-maker.md`가 에이전트에서 오케스트레이터 역할을 잘못 수행하던 것을 스킬로 이전. writer/validator/builder/visual-qa/uploader 5인 팀 구성, generator/validator/visual-qa 단일 책임 분리. |
