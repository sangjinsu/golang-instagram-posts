# Go 기초 문법 1분 정리

한국 개발자를 위한 **Go 기초 문법** 인스타그램 카드뉴스 자동 생성 시스템입니다.

## 워크플로우

```
에피소드 콘텐츠(JSON) → HTML 슬라이드 생성 → PNG 이미지 변환 → 인스타 업로드
```

## 에피소드 목록

| EP | 주제 |
|----|------|
| 01 | 변수와 상수 |
| 02 | 자료형 (Data Types) |
| 03 | 조건문 (if, switch) |
| 04 | 반복문 (for) |
| 05 | 함수 (Function) |
| 06 | 배열과 슬라이스 (Array & Slice) |
| 07 | 맵 (Map) |
| 08 | 구조체 (Struct) |
| 09 | 포인터 (Pointer) |
| 10 | 인터페이스 (Interface) |
| 11 | Goroutine |

## 슬라이드 구조 (8장)

| 장 | 내용 |
|----|------|
| 1 | 썸네일 (시리즈명 + EP번호 + 주제) |
| 2 | 핵심 개념 설명 |
| 3 | 기본 코드 예시 |
| 4 | 심화 코드 예시 |
| 5 | 실전 활용 코드 |
| 6 | 추가 패턴 / 주의사항 |
| 7 | 고급 활용 / 실무 팁 |
| 8 | 핵심 정리 + 다음 편 예고 |

## 기술 스택

- **Playwright (Python)** - Chromium 헤드리스로 HTML을 1080x1350px PNG로 변환
- **Noto Sans KR** + **JetBrains Mono** - Google Fonts 웹폰트
- **CSS 수동 구문 강조** - 하이라이팅 라이브러리 없이 직접 색상 클래스 적용

## 사용법

```bash
# 1. HTML 생성
python scripts/generate_html.py --ep 11

# 2. PNG 이미지 변환
python scripts/export_images.py --ep 11

# 3. 인스타그램 업로드
python scripts/upload_instagram.py --ep 11
```

## 프로젝트 구조

```
├── episodes/        # 에피소드별 콘텐츠 JSON + HTML
├── output/          # 생성된 PNG 이미지 (ep별 디렉토리)
├── templates/       # HTML 베이스 템플릿
└── scripts/
    ├── generate_html.py      # JSON → HTML
    ├── export_images.py      # HTML → PNG
    └── upload_instagram.py   # 인스타그램 업로드
```
