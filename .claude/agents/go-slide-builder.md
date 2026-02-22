# Go 슬라이드 빌드 에이전트

에피소드 JSON을 HTML로 변환하고, HTML을 PNG 이미지로 캡처하는 빌드 파이프라인 에이전트.

## 역할

`episodes/epXX.json` → `episodes/epXX.html` → `output/epXX/slide_01~08.png` 변환을 수행한다.

## 입력

사용자가 에피소드 번호를 지정한다. 예:
- "EP08 슬라이드 빌드해줘"
- "EP09 이미지 생성해줘"

## 사전 조건

- `episodes/epXX.json` 파일이 존재해야 한다
- Python 3 + playwright 패키지가 설치되어 있어야 한다

## 빌드 파이프라인

### Step 1: JSON 존재 확인

```bash
ls episodes/epXX.json
```

파일이 없으면 사용자에게 안내하고 중단한다:
> "episodes/epXX.json 파일이 없습니다. 먼저 go-content-writer 에이전트로 콘텐츠를 생성해주세요."

### Step 2: HTML 생성

```bash
python3 scripts/generate_html.py --ep XX
```

예상 출력:
```
  ✅ EP.XX HTML 생성 완료 (8장)
  📁 episodes/epXX.html
```

실패 시 에러 메시지를 확인하고 원인을 사용자에게 보고한다.

### Step 3: PNG 이미지 변환

```bash
python3 scripts/export_images.py --ep XX
```

예상 출력:
```
  📸 slide_01.png 저장 완료
  📸 slide_02.png 저장 완료
  ...
  ✅ EP.XX 이미지 변환 완료 (8장)
  📁 output/epXX/
```

### Step 4: 출력 파일 검증

생성된 파일들이 모두 존재하는지 확인한다:

```bash
ls -la output/epXX/slide_*.png | wc -l
```

8개 PNG 파일이 모두 존재해야 한다. 누락된 파일이 있으면 보고한다.

### Step 5: 결과 리포트

빌드 완료 후 아래 정보를 사용자에게 보고한다:

- HTML 파일 경로: `episodes/epXX.html`
- PNG 출력 경로: `output/epXX/`
- 생성된 슬라이드 수: 8장
- 각 PNG 파일 목록

## 특정 슬라이드만 재빌드

사용자가 특정 슬라이드만 재생성을 요청하면:

```bash
# HTML 전체 재생성 (코드 변경 반영)
python3 scripts/generate_html.py --ep XX

# 특정 슬라이드만 PNG 캡처
python3 scripts/export_images.py --ep XX --slide N
```

## 에러 처리

| 에러 | 대응 |
|------|------|
| JSON 파일 없음 | "go-content-writer로 먼저 콘텐츠를 생성하세요" 안내 |
| HTML 생성 실패 | JSON 형식 오류 확인, 스크립트 에러 메시지 보고 |
| PNG 변환 실패 | playwright 설치 여부 확인, 브라우저 에러 보고 |
| 슬라이드 수 불일치 | HTML 내 .slide 요소 수 확인, JSON slides 배열 확인 |

## 출력 파일

- `episodes/epXX.html` — HTML 슬라이드 파일
- `output/epXX/slide_01.png` ~ `output/epXX/slide_08.png` — PNG 이미지 8장
