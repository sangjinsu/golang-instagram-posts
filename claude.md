# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**Go 기초 문법 1분 정리** - 인스타그램 카드뉴스 자동 생성 시스템

한국 개발자 커뮤니티를 위한 **"Go 기초 문법 1분 정리"** 인스타그램 카드뉴스 시리즈를 자동으로 생성하는 시스템이다.

**현재 상태**: EP01~EP21 완료. EP22 다음 예정.

**핵심 워크플로우:**
```
에피소드 콘텐츠(JSON) → HTML 슬라이드 생성 → PNG 이미지 변환 → 인스타 업로드
```

## 에피소드 목록

| EP | 주제 | 상태 |
|----|------|------|
| 01 | 변수와 상수 | ✅ 완료 |
| 02 | 자료형 (Data Types) | ✅ 완료 |
| 03 | 조건문 (if, switch) | ✅ 완료 |
| 04 | 반복문 (for) | ✅ 완료 |
| 05 | 함수 (Function) | ✅ 완료 |
| 06 | 배열과 슬라이스 (Array & Slice) | ✅ 완료 |
| 07 | 맵 (Map) | ✅ 완료 |
| 08 | 구조체 (Struct) | ✅ 완료 |
| 09 | 포인터 (Pointer) | ✅ 완료 |
| 10 | 인터페이스 (Interface) | ✅ 완료 |
| 11 | Goroutine | ✅ 완료 |
| 12 | Channel | ✅ 완료 |
| 13 | Error Handling | ✅ 완료 |
| 14 | 패키지와 모듈 (Package & Module) | ✅ 완료 |
| 15 | JSON 처리 (JSON) | ✅ 완료 |
| 16 | 테스트 (Testing) | ✅ 완료 |
| 17 | 제네릭 (Generics) | ✅ 완료 |
| 18 | defer, panic, recover | ✅ 완료 |
| 19 | Context | ✅ 완료 |
| 20 | HTTP 서버 (net/http) | ✅ 완료 |
| 21 | 동시성 패턴 (Concurrency Patterns) | ✅ 완료 |
| 22 | 파일 입출력 (File I/O) | 🔜 다음 |

## 슬라이드 구조 (8장 고정)

모든 에피소드는 반드시 아래 8장 구조를 따른다:

| 장 | 타입 | 내용 |
|----|------|------|
| 1장 | `thumbnail` | 시리즈명 + EP번호 + 주제 + 한줄 훅 |
| 2장 | `concept` | 핵심 개념 설명 (비유, 이모지 활용) |
| 3장 | `code` | 기본 코드 예시 |
| 4장 | `code` | 심화 코드 예시 (Go만의 특징) |
| 5장 | `code` | 실전 활용 코드 |
| 6장 | `code` | 추가 패턴 또는 주의사항 코드 |
| 7장 | `code` | 고급 활용 또는 실무 팁 코드 |
| 8장 | `summary` | 핵심 정리 + 다음 편 예고 + CTA |

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
- 상단 바: 시리즈 태그(좌) + EP 번호(우)
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
├── CLAUDE.md              ← 이 파일
├── skills/
│   ├── slide-content.md   ← 콘텐츠 작성 규칙
│   ├── html-template.md   ← HTML/CSS 템플릿 가이드
│   └── image-export.md    ← 이미지 변환 가이드
├── templates/
│   └── base.html          ← 기본 HTML 템플릿
├── episodes/
│   ├── ep01.json          ← 변수와 상수
│   ├── ep02.json          ← 자료형 (Data Types)
│   ├── ep03.json          ← 조건문 (if, switch)
│   ├── ep04.json          ← 반복문 (for)
│   ├── ep05.json          ← 함수 (Function)
│   ├── ep06.json          ← 배열과 슬라이스 (Array & Slice)
│   ├── ep07.json          ← 맵 (Map)
│   ├── ep08.json          ← 구조체 (Struct)
│   ├── ep09.json          ← 포인터 (Pointer)
│   ├── ep10.json          ← 인터페이스 (Interface)
│   ├── ep11.json          ← 고루틴 (Goroutine)
│   ├── ep12.json          ← 채널 (Channel)
│   ├── ep13.json          ← 에러 처리 (Error Handling)
│   ├── ep14.json          ← 패키지와 모듈 (Package & Module)
│   ├── ep15.json          ← JSON 처리 (JSON)
│   ├── ep16.json          ← 테스트 (Testing)
│   ├── ep17.json          ← 제네릭 (Generics)
│   ├── ep18.json          ← defer, panic, recover
│   ├── ep19.json          ← Context
│   ├── ep20.json          ← HTTP 서버 (net/http)
│   └── ep21.json          ← 동시성 패턴 (Concurrency Patterns)
├── .env                   ← API 키 (UPLOAD_POST_API_KEY 등)
├── .venv/                 ← Python 가상환경 (pip3 설치용)
├── output/
│   ├── ep01/ ~ ep16/     ← 에피소드별 slide_01~09.png
│   └── ep16/
│       ├── slide_01.png
│       ├── ...
│       └── slide_08.png
└── scripts/
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

### 에피소드 전체 생성
```bash
# 1. 콘텐츠 JSON 작성
# 2. HTML 생성
python3 scripts/generate_html.py --ep 08
# 3. PNG 이미지 변환
python3 scripts/export_images.py --ep 08
```

### 개별 단계 실행
```bash
# HTML만 미리보기
python3 scripts/generate_html.py --ep 08 --preview
# 특정 슬라이드만 재생성
python3 scripts/export_images.py --ep 08 --slide 3
```

### 인스타그램 업로드
```bash
# venv + .env 필수
source .venv/bin/activate && source .env

# dry-run (파라미터 확인만)
python3 scripts/upload_instagram.py --ep 12 --auto-caption --dry-run

# 실제 업로드
python3 scripts/upload_instagram.py --ep 12 --auto-caption

# 업로드 상태 확인
python3 scripts/upload_instagram.py --status <request_id>
```

## GeekNews 카드뉴스 생성 프로세스

GeekNews 기사 카드뉴스 JSON을 생성할 때 반드시 아래 프로세스를 따른다.

### 1단계: 기사 선정
- `python3 scripts/geeknews_pipeline.py --week latest --scrape-only`로 기사 목록 수집
- 기존 `episodes/gn_*.json`과 중복되지 않는 기사 선정
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
2. **Go 철학 강조**: Go만의 특별한 점을 매번 언급 (예: "Go에는 while이 없다!")
3. **이모지 적극 활용**: 시각적 구분과 친근함을 위해
4. **비유 사용**: 어려운 개념은 일상적 비유로 설명
5. **실무 연결**: "실무에서는 이렇게 씁니다" 팁 포함
6. **코드는 간결하게**: 한 슬라이드 15줄 이내, 핵심만

## 주의사항

- 인스타그램 이미지이므로 테이블, 복잡한 레이아웃 사용 금지
- 모바일에서 보기 때문에 글자 크기 최소 24px 이상
- 코드 블록 내 한 줄 최대 40자 권장 (가로 스크롤 방지)
- 이전 에피소드와 시각적 일관성 유지
- 각 슬라이드는 독립적으로 이해 가능해야 함

---

## 하네스: Card News Pipeline

**목표:** Go 기초 문법 에피소드(ep) 및 GeekNews 주간 픽(gn_) 카드뉴스의 콘텐츠 작성 → 검증 → HTML/PNG 빌드 → 시각 QA → 인스타그램 업로드까지 5인 에이전트 팀으로 조율.

**트리거:** 카드뉴스 파이프라인 관련 요청(에피소드 생성/빌드/수정/재빌드/업로드, GeekNews 주간 카드뉴스, 특정 슬라이드 재생성 등) 시 `orchestrate-pipeline` 스킬을 사용하라. 단순 JSON/스키마 질문이나 개별 스크립트 한 줄 실행만 필요한 경우는 예외.

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-04-09 | 초기 구성 | `.claude/agents/` 5개 + `.claude/skills/orchestrate-pipeline/` + 이 포인터 | 파이프라인 조율 팀 신설 요청. 기존 `go-episode-maker.md`가 에이전트에서 오케스트레이터 역할을 잘못 수행하던 것을 스킬로 이전. writer/validator/builder/visual-qa/uploader 5인 팀 구성, generator/validator/visual-qa 단일 책임 분리. |