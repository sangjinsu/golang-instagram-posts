# 스킬: 이미지 변환 (HTML → PNG)

## 개요

생성된 HTML 파일의 각 `.slide` div를 개별 PNG 파일로 캡처한다.
Playwright (Python)의 헤드리스 Chromium을 사용한다.

## 기술 요구사항

```bash
pip install playwright
playwright install chromium
```

## 핵심 스크립트: export_images.py

```python
import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def export_slides(ep_number: int, output_dir: str = None):
    """에피소드 HTML에서 각 슬라이드를 PNG로 캡처"""

    html_path = f"episodes/ep{ep_number:02d}.html"
    if output_dir is None:
        output_dir = f"output/ep{ep_number:02d}"

    os.makedirs(output_dir, exist_ok=True)

    # HTML 파일을 절대 경로로 변환
    abs_html = os.path.abspath(html_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1350}
        )

        # HTML 파일 열기
        await page.goto(f"file://{abs_html}")

        # ⚠️ 웹폰트 로딩 대기 (중요!)
        await page.wait_for_timeout(3000)

        # 추가: 모든 폰트가 로드될 때까지 대기
        await page.evaluate("""
            () => document.fonts.ready
        """)
        await page.wait_for_timeout(500)

        # 각 슬라이드를 개별 PNG로 캡처
        slides = await page.query_selector_all(".slide")
        total = len(slides)

        for i, slide in enumerate(slides, 1):
            output_path = os.path.join(output_dir, f"slide_{i:02d}.png")
            await slide.screenshot(path=output_path)
            print(f"  ✅ [{i}/{total}] {output_path}")

        await browser.close()

    print(f"\n🎉 EP.{ep_number:02d} 슬라이드 {total}장 생성 완료!")
    print(f"📁 출력 경로: {output_dir}")
    return total


async def export_single_slide(ep_number: int, slide_number: int):
    """특정 슬라이드 하나만 재캡처"""

    html_path = f"episodes/ep{ep_number:02d}.html"
    output_dir = f"output/ep{ep_number:02d}"
    os.makedirs(output_dir, exist_ok=True)

    abs_html = os.path.abspath(html_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1350}
        )

        await page.goto(f"file://{abs_html}")
        await page.wait_for_timeout(3000)
        await page.evaluate("() => document.fonts.ready")
        await page.wait_for_timeout(500)

        slide = await page.query_selector(f"#slide-{slide_number}")
        if slide:
            output_path = os.path.join(
                output_dir, f"slide_{slide_number:02d}.png"
            )
            await slide.screenshot(path=output_path)
            print(f"  ✅ {output_path}")
        else:
            print(f"  ❌ slide-{slide_number} 을 찾을 수 없습니다")

        await browser.close()


if __name__ == "__main__":
    ep = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    if len(sys.argv) > 2 and sys.argv[2] == "--slide":
        slide_num = int(sys.argv[3])
        asyncio.run(export_single_slide(ep, slide_num))
    else:
        asyncio.run(export_slides(ep))
```

## 사용법

```bash
# 전체 슬라이드 캡처
python scripts/export_images.py 8

# 특정 슬라이드만 캡처
python scripts/export_images.py 8 --slide 3
```

## 파일 명명 규칙

```
output/
└── ep08/
    ├── slide_01.png    (썸네일)
    ├── slide_02.png    (핵심 개념)
    ├── slide_03.png    (코드 1)
    ├── slide_04.png    (코드 2)
    ├── slide_05.png    (코드 3)
    ├── slide_06.png    (코드 4)
    ├── slide_07.png    (코드 5)
    └── slide_08.png    (요약 + CTA)
```

## 품질 설정

- 해상도: 1080 x 1350px (인스타 4:5 네이티브)
- 포맷: PNG (무손실)
- DPI: 기본 (1x) — 인스타에서 추가 압축하므로 2x 불필요

## 트러블슈팅

### 한글 폰트가 깨지는 경우
- `page.wait_for_timeout(3000)` 시간을 늘려본다
- `document.fonts.ready` 대기가 제대로 동작하는지 확인
- 오프라인 환경이면 로컬 폰트 파일 사용 고려

### 이모지가 깨지는 경우
- Chromium에서 시스템 이모지 폰트가 필요
- 리눅스: `fonts-noto-color-emoji` 패키지 설치
  ```bash
  apt-get install fonts-noto-color-emoji
  ```

### 슬라이드 크기가 맞지 않는 경우
- viewport 크기와 `.slide` CSS 크기가 모두 1080x1350인지 확인
- `element.screenshot()`은 요소 크기 기준으로 캡처됨

### 배경 그라데이션이 잘리는 경우
- `overflow: hidden`이 `.slide`에 적용되어 있는지 확인
- 장식 원(::before, ::after)이 슬라이드 밖으로 나가도 잘리도록 처리

## Claude Code 연동 시 주의사항

1. HTML 파일 생성 후 반드시 `export_images.py`를 실행하여 이미지 생성
2. 이미지 생성 후 사용자에게 output 디렉토리의 PNG를 제공
3. 수정 요청 시 해당 슬라이드만 HTML 수정 → 해당 슬라이드만 재캡처 (--slide 옵션)
4. 전체 에피소드 재생성 시 HTML 전체 재생성 → 전체 캡처