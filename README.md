# GeekNews Daily Card News

한국 개발자를 위한 **GeekNews 하루 1개 인스타그램 카드뉴스** 생성/업로드 파이프라인입니다.

운영 목표는 단순합니다:

- 하루 1개 발행
- 주 7개 카드뉴스 사전 생성
- 월 28~31개 포스트 유지
- 매주 후보 10개 이상 확보 후 7개 선별

기존 Go 기초 문법 에피소드 트랙은 보존하지만, 현재 기본 운영 대상은 GeekNews입니다.

## Workflow

```text
GeekNews 후보 수집 → 7개 기사 선별 → JSON 생성/검증 → HTML 생성 → PNG 변환 → dry-run/업로드
```

## Weekly Batch

매주 7개를 한 번에 만들고 하루 1개씩 발행합니다.

```bash
# 1. 최신 GeekNews 후보 수집
python3 scripts/geeknews_pipeline.py --week latest --scrape-only

# 2. 7일치 카드뉴스 생성 + HTML/PNG 빌드
python3 scripts/geeknews_pipeline.py --week latest --count 7 --dry-run

# 3. 개별 업로드 dry-run 확인
python3 scripts/upload_instagram.py --id gn_YYYY_wWW_01 --auto-caption --dry-run

# 4. 실제 업로드 또는 예약 업로드
python3 scripts/upload_instagram.py --id gn_YYYY_wWW_01 --auto-caption
python3 scripts/upload_instagram.py --id gn_YYYY_wWW_01 --auto-caption \
  --schedule "2026-06-01T09:00:00" --timezone "Asia/Seoul"
```

`--dry-run`은 Instagram 업로드를 실행하지 않고 JSON, HTML, PNG 생성까지만 확인합니다.

## Content Rules

GeekNews 카드뉴스는 보통 5장 구성입니다.

| 장 | 타입 | 목적 |
|----|------|------|
| 1 | `news-thumbnail` | 기사 주제와 훅 |
| 2 | `news-summary` | 핵심 요약 3~5개 |
| 3 | `news-why` | 왜 중요한지 |
| 4 | `news-detail` | 실무 맥락 또는 사례 |
| 5 | `news-closing` | 요약, 원문, CTA |

품질 기준:

- 한국 개발자에게 실무적으로 유용한 기사 우선
- AI/ML 실전 활용, 개발자 생산성, 프로그래밍 언어/프레임워크, 소프트웨어 엔지니어링 우선
- 리서치 기반의 구체적 숫자, 제품명, 사건, 연구 결과 포함
- 제네릭한 요약 금지
- 업로드 전 dry-run과 PNG 시각 QA 확인

## Tech Stack

- **Python 3** - 파이프라인 스크립트
- **Playwright** - HTML을 1080x1350px PNG로 변환
- **Anthropic API** - 기사 선별, JSON 생성, 품질 검증
- **upload-post** - Instagram 업로드/예약 업로드
- **Noto Sans KR** + **JetBrains Mono** - 카드뉴스 웹폰트

## Project Structure

```text
├── episodes/                  # GeekNews JSON/HTML 산출물
├── output/                    # 생성된 PNG 이미지
├── scripts/
│   ├── geeknews_pipeline.py   # 후보 수집부터 빌드까지 주간 7개 배치
│   ├── generate_html.py       # JSON → HTML
│   ├── export_images.py       # HTML → PNG
│   └── upload_instagram.py    # Instagram 업로드/예약
├── templates/                 # HTML 베이스 템플릿
└── skills/                    # 카드뉴스 작성/빌드 가이드
```

## Legacy Go EP Track

`ep08`~`ep21` Go 기초 문법 콘텐츠와 `--ep` 기반 생성/업로드 경로는 보존되어 있습니다. 다만 신규 기본 운영은 GeekNews daily publishing입니다.
