---
name: orchestrate-pipeline
description: Go 기초 문법 에피소드(ep01~epXX) 또는 GeekNews 주간 픽(gn_) 인스타그램 카드뉴스의 전체 파이프라인을 조율하는 오케스트레이터. 콘텐츠 작성 → 검증 → HTML/PNG 빌드 → 시각 QA → 인스타 업로드까지 5인 에이전트 팀을 구성해 자동 실행한다. "EP22 만들어줘", "ep22 에피소드 생성", "GeekNews 주간 카드뉴스 만들어줘", "gn_2026_w15_01 업로드", "에피소드 재빌드", "slide 3 다시 만들어줘", "업데이트", "수정", "재실행" 등 카드뉴스 파이프라인과 관련된 모든 요청에 반드시 이 스킬을 사용할 것. 단순 JSON 질문이나 스크립트 한 줄 실행만 필요한 경우는 예외.
---

# orchestrate-pipeline 스킬

"Go 기초 문법 1분 정리" 에피소드 또는 "GeekNews 주간 픽" 기사의 카드뉴스 파이프라인을 **에이전트 팀으로 조율**하는 오케스트레이터.

## 언제 이 스킬을 쓰는가

| 사용자 요청 | 이 스킬 사용 여부 |
|------------|------------------|
| "EP22 파일 입출력 만들어줘" | ✅ 초기 실행 |
| "ep22 에피소드 전체 생성" | ✅ 초기 실행 |
| "GeekNews 이번 주 카드뉴스 만들어줘" | ✅ 초기 실행 (GeekNews 트랙) |
| "gn_2026_w15_01 업로드해줘" | ✅ 업로드 단계만 |
| "EP08 슬라이드 3 다시 만들어줘" | ✅ 부분 재실행 |
| "EP22 content 수정해줘" | ✅ 부분 재실행 (writer만) |
| "EP22 재빌드" | ✅ 부분 재실행 (builder+qa) |
| "ep08.json 스키마가 뭐야?" | ❌ 단순 질문, 직접 응답 |
| "export_images.py 버그 수정" | ❌ 스크립트 개발, 직접 처리 |

## 팀 구성

이 스킬은 `card-news-pipeline` 팀을 구성한다:

| 에이전트 | 역할 | 단계 |
|----------|------|------|
| content-writer | JSON 콘텐츠 작성 | Phase 1 |
| content-validator | JSON 스키마 + 제약 검증 | Phase 2 |
| slide-builder | HTML + PNG 빌드 | Phase 3 |
| visual-qa | 이미지 품질 검증 | Phase 4 |
| instagram-uploader | 업로드 승인 + 실행 | Phase 5 (선택) |

**실행 모드:** 에이전트 팀 (SendMessage + TaskCreate 기반 자체 조율)

## Phase 0: 컨텍스트 확인 (반드시 먼저 수행)

사용자 요청을 받으면 먼저 아래 순서로 상태를 확인한다.

### 0-1. 트랙 식별

사용자 입력에서 트랙과 content_id를 파싱:

| 입력 형태 | 트랙 | content_id |
|----------|------|-----------|
| "EP22", "ep22", "에피소드 22", "22번" | Go EP | `ep22` |
| "gn_2026_w15_01", "GN W15 01" | GeekNews | `gn_2026_w15_01` |
| "이번 주 GeekNews" | GeekNews 파이프라인 | (geeknews_pipeline.py 실행) |

### 0-2. 산출물 존재 확인

```bash
CONTENT_ID="ep22"  # 예시
JSON_EXISTS=$(ls episodes/${CONTENT_ID}.json 2>/dev/null && echo yes)
HTML_EXISTS=$(ls episodes/${CONTENT_ID}.html 2>/dev/null && echo yes)
PNG_DIR_EXISTS=$(ls -d output/${CONTENT_ID} 2>/dev/null && echo yes)
```

### 0-3. 실행 모드 결정

| 상태 | 사용자 요청 | 실행 모드 |
|------|------------|----------|
| 모두 미존재 | 전체 생성 | **초기 실행** (Phase 1~5) |
| JSON만 있음 | "빌드만" | **부분 실행** (Phase 3~4) |
| 전부 있음 | "업로드" | **부분 실행** (Phase 5만) |
| 전부 있음 | "slide N 다시" | **부분 재실행** (builder --slide N + qa) |
| 전부 있음 | "수정해줘" | **부분 재실행** (writer → validator → 필요 시 builder) |
| 전부 있음 | "새로 만들어줘" | **초기 실행** (기존 파일 .bak 백업 후) |
| JSON 있음 + 사용자가 새 주제 | 덮어쓰기 확인 | **사용자 확인 후 초기 실행** |

애매하면 `AskUserQuestion`으로 사용자에게 의도 확인.

### 0-4. 특수: GeekNews 일괄 파이프라인

사용자가 "GeekNews 이번 주" 또는 "GeekNews 주간 카드뉴스"를 요청하면:
1. `scripts/geeknews_pipeline.py --week latest --scrape-only` 실행 → 후보 목록 확인
2. `episodes/gn_{week}_candidates.json` 읽어 기사 목록 표시
3. 사용자에게 "자동 파이프라인(`geeknews_pipeline.py --week latest --dry-run`)으로 일괄 생성할까요, 아니면 개별 기사를 골라 content-writer 팀으로 처리할까요?" 질문
4. 팀 기반이면 각 기사별로 Phase 1~4 반복

## Phase 1-5: 팀 조율 워크플로우

### 팀 구성

```
TeamCreate({
  team_name: "card-news-pipeline",
  members: [
    { agent: "content-writer" },
    { agent: "content-validator" },
    { agent: "slide-builder" },
    { agent: "visual-qa" },
    { agent: "instagram-uploader" }
  ]
})
```

업로드가 요청되지 않은 경우 instagram-uploader는 팀에 추가하지 않는다.

### 작업 그래프 (TaskCreate + 의존성)

초기 실행 시 아래 작업을 생성하고 의존성을 설정한다:

| # | Task subject | 담당 | blockedBy |
|---|-------------|------|-----------|
| T1 | content-writer: draft {content_id} | content-writer | - |
| T2 | content-validator: validate {content_id} | content-validator | T1 |
| T3 | slide-builder: build {content_id} | slide-builder | T2 |
| T4 | visual-qa: verify {content_id} | visual-qa | T3 |
| T5 | instagram-uploader: upload {content_id} | instagram-uploader | T4 (선택) |

각 팀원은 자기 이름 prefix의 작업을 claim → `in_progress` → `completed` 순서로 진행.

### 데이터 전달 (파일 기반)

이 프로젝트는 이미 규칙화된 디렉토리 구조가 있으므로 별도 `_workspace/` 불필요:

| 단계 | 입력 | 출력 |
|------|------|------|
| Phase 1 | (사용자 요청) | `episodes/{id}.json` |
| Phase 2 | `episodes/{id}.json` | (pass/fail 판정) |
| Phase 3 | `episodes/{id}.json` | `episodes/{id}.html`, `output/{id}/slide_*.png` |
| Phase 4 | `output/{id}/*.png` | (pass/fail 판정) |
| Phase 5 | `output/{id}/*.png`, `episodes/{id}.json` | 인스타그램 게시물 URL |

### 피드백 루프 (SendMessage 기반)

```
content-writer  ──draft──▶  content-validator
       ▲                        │
       └──FAIL + 이슈───────────┘
                                │ PASS
                                ▼
                         slide-builder  ──build──▶  visual-qa
                                ▲                        │
                                └──FAIL + slide N────────┘
                                                         │ PASS
                                                         ▼
                                                instagram-uploader
                                                    (사용자 승인)
```

재시도 한계: 각 피드백 단계에서 **최대 3회**. 3회 초과 시 리더에게 보고, 리더가 사용자에게 수동 개입 요청.

## 리더(이 스킬)의 책임

1. Phase 0 컨텍스트 확인 후 실행 모드 결정
2. 팀 구성 (`TeamCreate`)
3. 작업 생성 및 의존성 설정 (`TaskCreate`)
4. 필요 시 초기 context를 first agent에 `SendMessage`로 전달
5. 진행 상황 모니터링 (팀원의 SendMessage 수신)
6. 최종 결과를 사용자에게 보고
7. 실행 후 피드백 기회 제공 (Phase 7 진화)
8. 세션 종료 시 팀 해체 (선택 — 같은 세션에서 재사용 가능)

**리더는 실제 작업을 수행하지 않는다.** 리더가 Bash나 Write를 직접 사용하면 안 된다. 모든 작업은 팀원에게 할당한다.

## 에러 핸들링

| 단계 | 에러 유형 | 대응 |
|------|----------|------|
| Phase 0 | 모호한 요청 | `AskUserQuestion`으로 명확화 |
| Phase 1 | writer 3회 실패 | 수동 개입 요청 |
| Phase 2 | validator 3회 실패 | 수동 개입 요청, 이슈 요약 |
| Phase 3 | 스크립트 에러 (JSON→HTML) | validator 재실행 또는 사용자 보고 |
| Phase 3 | Playwright 에러 | 환경 점검 안내 (`playwright install chromium`) |
| Phase 4 | 폰트 회귀 의심 | builder 재시도 1회, 실패 시 사용자에게 수동 확인 요청 |
| Phase 5 | 사용자 취소 | 파이프라인 정상 종료 (취소도 성공) |
| Phase 5 | API 키 미설정 | 사용자에게 `source .env` 안내 |

## 최종 결과 리포트 형식

```
🎉 {content_id} 파이프라인 완료

트랙: {Go EP | GeekNews}
실행 모드: {초기 실행 | 부분 재실행 | 업로드만}

Phase 1 content-writer:    ✅ episodes/{id}.json (N장)
Phase 2 content-validator:  ✅ PASS
Phase 3 slide-builder:      ✅ HTML + PNG (N장)
Phase 4 visual-qa:          ✅ PASS (썸네일 95KB, 모두 1080×1350)
Phase 5 instagram-uploader: ⏭️ 사용자 미요청 (또는 ✅ {post_url})

다음 단계 제안:
- 업로드: "ep22 인스타에 올려줘"
- 수정: "ep22 slide 5 다시 만들어줘"
- 새 에피소드: "EP23 시작"
```

## 테스트 시나리오

### 정상 흐름 1: Go EP 초기 생성

**입력:** "EP22 파일 입출력 에피소드 만들어줘"

1. Phase 0: `ep22` 파싱, 파일 미존재 → 초기 실행
2. 팀 구성 (uploader 제외)
3. T1~T4 작업 생성
4. content-writer가 T1 claim → `episodes/ep22.json` 작성 → validator에 SendMessage
5. content-validator가 T2 claim → 검증 PASS → builder에 SendMessage
6. slide-builder가 T3 claim → HTML+PNG 생성 → visual-qa에 SendMessage
7. visual-qa가 T4 claim → PNG 검증 PASS → 리더에 SendMessage
8. 리더가 최종 리포트 출력

### 정상 흐름 2: 부분 재실행 (slide 수정)

**입력:** "EP08 slide 5 다시 만들어줘"

1. Phase 0: `ep08` 파싱, 모든 파일 존재 → 부분 재실행
2. 팀 구성 (builder + visual-qa만)
3. builder에 "rebuild ep08 slide 5" 작업 할당
4. builder: `generate_html.py --ep 08` 실행 (전체 HTML 재생성) → `export_images.py --ep 08 --slide 5`
5. visual-qa: 전체 PNG 재검증 (slide 5만이 아니라 전체)
6. 리더 결과 보고

### 정상 흐름 3: GeekNews 일괄

**입력:** "이번 주 GeekNews 카드뉴스 만들어줘"

1. Phase 0: GeekNews 일괄 트랙
2. `scripts/geeknews_pipeline.py --week latest --scrape-only` 실행 (이것만은 리더가 직접)
3. 후보 목록 표시
4. `AskUserQuestion`: 자동 파이프라인(스크립트) vs 팀 기반(에이전트) 선택
5. 팀 기반 선택 시: 각 기사별 content-writer 호출 (기사 번호 loop)

### 에러 흐름: validator 반복 실패

**상황:** content-writer 작성한 JSON의 코드가 3회 연속 40자 초과

1. writer 1차 작성 → validator FAIL (slide 4 line 3: 42자)
2. writer가 해당 줄만 수정 → validator FAIL (slide 4 line 3: 41자, 여전히 초과)
3. writer 재수정 → validator FAIL (slide 5 line 7: 새 이슈)
4. 3회 재시도 초과 → 리더에 차단 보고
5. 리더가 사용자에게: "코드 제약 3회 반복 실패. 수동 수정 후 validator 재실행 요청 주세요"

### 에러 흐름: 폰트 렌더링 회귀

1. builder 빌드 완료 → visual-qa
2. visual-qa: `slide_01.png = 32KB` 감지 (썸네일 40KB 미만)
3. visual-qa → builder: "slide_01 폰트 로딩 실패 의심, 재빌드 요청"
4. builder 재빌드 (1회)
5. visual-qa 재검증 → 이번엔 95KB → PASS
6. 리더 리포트에 경고 기록: "폰트 재빌드 1회 발생"

## Phase 7: 실행 후 피드백 (진화)

파이프라인 완료 후 **매번** 사용자에게 피드백 기회 제공:

```
결과에서 개선할 부분이 있나요?
- 에이전트 역할 조정이 필요하면 알려주세요
- 팀 구성이나 워크플로우를 바꾸고 싶으면 말씀해주세요
```

피드백이 있으면 CLAUDE.md 변경 이력에 기록하고 해당 에이전트/스킬 수정. 피드백 없으면 그냥 넘어감 (강요 금지).

## 참조 파일

| 파일 | 용도 |
|------|------|
| `CLAUDE.md` | 프로젝트 규칙, 에피소드 목록, GeekNews 프로세스 |
| `skills/slide-content.md` | 콘텐츠 작성 규칙 (writer 참조) |
| `skills/html-template.md` | HTML 템플릿 가이드 (builder 참조) |
| `skills/image-exporter.md` | 이미지 변환 가이드 (builder 참조) |
| `scripts/generate_html.py` | JSON → HTML 변환 (builder 실행) |
| `scripts/export_images.py` | HTML → PNG 변환 (builder 실행) |
| `scripts/upload_instagram.py` | 인스타 업로드 (uploader 실행) |
| `scripts/geeknews_pipeline.py` | GeekNews 자동 파이프라인 |
| `episodes/ep08.json` | Go EP 스키마 예시 (writer 참조) |
| `episodes/gn_2026_w14_08.json` | GeekNews 스키마 예시 (writer 참조) |
