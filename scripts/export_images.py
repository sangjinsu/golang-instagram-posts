#!/usr/bin/env python3
"""export_images.py — HTML 슬라이드 → PNG 이미지 변환

Playwright(Chromium)를 사용하여 각 .slide div를 개별 PNG로 캡처한다.

사용법:
    python scripts/export_images.py --ep 08
    python scripts/export_images.py --ep 08 --slide 3
    python scripts/export_images.py --id gn_2026_w14_01
    python scripts/export_images.py --id gn_2026_w14_01 --slide 3
"""

import os
import sys
import argparse
from playwright.sync_api import sync_playwright


def export_slides(content_id, slide_filter=None):
    html_path = os.path.join('episodes', f'{content_id}.html')
    output_dir = os.path.join('output', content_id)

    if not os.path.exists(html_path):
        print(f'  \u274c {html_path} 파일을 찾을 수 없습니다.')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    abs_html = os.path.abspath(html_path)

    chromium_path = None
    for candidate in [
        '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
        '/opt/pw-browsers/chromium-1208/chrome-linux64/chrome',
    ]:
        if os.path.exists(candidate):
            chromium_path = candidate
            break

    with sync_playwright() as p:
        launch_kwargs = {}
        if chromium_path:
            launch_kwargs['executable_path'] = chromium_path
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={'width': 1080, 'height': 1350})
        # Block external resource requests (fonts, etc.) that may fail in restricted environments
        page.route('**/*', lambda route: route.abort() if route.request.resource_type in ('font', 'stylesheet') and 'googleapis' in route.request.url else route.continue_())
        page.goto(f'file://{abs_html}', wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(2000)  # Wait for rendering

        slides = page.query_selector_all('.slide')
        total = len(slides)

        if total == 0:
            print('  \u274c .slide 요소를 찾을 수 없습니다.')
            browser.close()
            sys.exit(1)

        for i, slide in enumerate(slides, 1):
            if slide_filter and i != slide_filter:
                continue

            out_path = os.path.join(output_dir, f'slide_{i:02d}.png')
            slide.screenshot(path=out_path)
            print(f'  \U0001f4f8 slide_{i:02d}.png 저장 완료')

        browser.close()

    exported = 1 if slide_filter else total
    print(f'  \u2705 {content_id} 이미지 변환 완료 ({exported}장)')
    print(f'  \U0001f4c1 {output_dir}/')


def main():
    parser = argparse.ArgumentParser(description='HTML 슬라이드 → PNG 이미지 변환')
    parser.add_argument('--ep', default=None, help='에피소드 번호 (예: 08)')
    parser.add_argument('--id', default=None, help='콘텐츠 ID (예: gn_2026_w14_01)')
    parser.add_argument('--slide', type=int, default=None, help='특정 슬라이드만 변환 (예: 3)')
    args = parser.parse_args()

    if args.id:
        content_id = args.id
    elif args.ep:
        content_id = f'ep{int(args.ep):02d}'
    else:
        print('  \u274c --ep 또는 --id를 지정해주세요.')
        sys.exit(1)

    export_slides(content_id, args.slide)


if __name__ == '__main__':
    main()
