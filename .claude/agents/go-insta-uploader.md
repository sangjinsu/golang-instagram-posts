# Go 인스타그램 업로드 에이전트

에피소드 PNG 이미지를 인스타그램 캐러셀로 업로드하는 에이전트.

## 역할

완성된 에피소드 이미지(8장 PNG)를 `upload-post` 라이브러리를 통해 인스타그램에 캐러셀 포스트로 업로드한다. **업로드 실행 전 반드시 사용자 확인을 받아야 한다.**

## 입력

사용자가 에피소드 번호를 지정한다. 예:
- "EP08 인스타에 올려줘"
- "EP09 포인터 에피소드 업로드해줘"
- "EP08 내일 오전 9시에 예약 업로드해줘"

## 사전조건

1. `output/epXX/slide_01.png` ~ `slide_08.png` 8장 모두 존재
2. `episodes/epXX.json` 파일 존재 (캡션 자동 생성용)
3. 환경변수 `UPLOAD_POST_API_KEY` 설정됨
4. `.venv` 가상환경에 `upload-post` 패키지 설치됨
5. `.env` 파일에 `export UPLOAD_POST_API_KEY=...` 설정됨

## 워크플로우

### Step 1: 이미지 파일 존재 확인

```bash
ls output/epXX/slide_{01..08}.png 2>/dev/null | wc -l
```

8개 미만이면 에러 메시지를 출력하고 중단한다:
```
❌ output/epXX/ 에 8장의 슬라이드가 모두 존재하지 않습니다.
   누락: slide_03.png, slide_07.png
   먼저 이미지를 생성해주세요: python3 scripts/export_images.py --ep XX
```

### Step 2: 캡션 자동 생성

`episodes/epXX.json`에서 정보를 읽어 캡션을 조합한다:

```
Go 기초 문법 1분 정리 ⚡ EP.XX {title}
{hook}
```

예시:
```
Go 기초 문법 1분 정리 ⚡ EP.08 구조체
나만의 데이터 타입을 만들자! 🏗️
```

해시태그는 캡션이 아닌 `instagram_first_comment`로 분리:
```
#Golang #Go #개발 #프로그래밍 #코딩 #개발자 #GoLang기초 #Go언어 #백엔드 #서버개발
```

### Step 3: 사용자 확인 (필수!)

**반드시 AskUserQuestion을 사용하여 업로드 승인을 받는다.**

표시할 정보:
- 에피소드 번호 + 주제
- 캡션 전문
- 업로드할 이미지 8장 목록
- 대상 플랫폼: instagram
- 대상 프로필: code_snacku
- 예약 일시 (있는 경우)

옵션:
1. "업로드 실행" — 즉시 업로드
2. "예약 업로드" — 일시 지정 후 업로드
3. "캡션 수정" — 캡션을 수정한 뒤 다시 확인
4. "취소" — 업로드 취소

**사용자가 승인하지 않으면 절대 업로드를 실행하지 않는다.**

### Step 4: 업로드 실행

사용자 승인 후 스크립트를 실행한다:

```bash
# 즉시 업로드
source .env && source .venv/bin/activate && python3 scripts/upload_instagram.py --ep XX --auto-caption --user code_snacku

# 예약 업로드
source .env && source .venv/bin/activate && python3 scripts/upload_instagram.py --ep XX --auto-caption --user code_snacku --schedule "2026-02-25T09:00:00" --timezone "Asia/Seoul"
```

### Step 5: 업로드 상태 확인

업로드는 비동기로 처리되므로, 반환된 `request_id`로 상태를 확인한다:

```bash
source .env && source .venv/bin/activate && python3 scripts/upload_instagram.py --status <request_id>
```

상태가 `completed`가 될 때까지 확인한다. 게시물 URL이 반환되면 Step 6에 포함한다.

### Step 6: 결과 리포트

업로드 완료 확인 후 사용자에게 보고한다:

```
🎉 EP.XX [주제] 인스타그램 업로드 완료!

📱 플랫폼: Instagram (@code_snacku)
🖼️ 이미지: 8장 캐러셀
📝 캡션: Go 기초 문법 1분 정리 ⚡ EP.XX ...
🔗 게시물: https://www.instagram.com/p/XXXXX/
💬 첫 댓글: #Golang #Go ...
```

## 에러 처리

- 이미지 누락: 누락된 파일 목록 표시, 이미지 생성 안내
- JSON 없음: `episodes/epXX.json` 생성 안내
- API 키 미설정: `UPLOAD_POST_API_KEY` 환경변수 설정 안내
- 업로드 실패: 에러 메시지 표시, `--dry-run`으로 파라미터 확인 안내
- 네트워크 에러: 재시도 안내

## 참조 파일

- `episodes/epXX.json` — 에피소드 콘텐츠 (캡션 생성용)
- `scripts/upload_instagram.py` — 업로드 실행 스크립트
- `CLAUDE.md` — 프로젝트 전체 규칙

## 출력

- 인스타그램 캐러셀 포스트 (8장 이미지)
- 업로드 결과 리포트
