#!/usr/bin/env python3
"""export_images.py — HTML 슬라이드 → PNG 이미지 변환

Playwright(Chromium)를 사용하여 각 .slide div를 개별 PNG로 캡처한다.

사용법:
    python scripts/export_images.py --ep 08
    python scripts/export_images.py --ep 08 --slide 3
"""

import os
import sys
import argparse
from playwright.sync_api import sync_playwright


def export_slides(ep_num, slide_filter=None):
    html_path = os.path.join('episodes', f'ep{ep_num:02d}.html')
    output_dir = os.path.join('output', f'ep{ep_num:02d}')

    if not os.path.exists(html_path):
        print(f'  \u274c {html_path} 파일을 찾을 수 없습니다.')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    abs_html = os.path.abspath(html_path)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1080, 'height': 1350})
        page.goto(f'file://{abs_html}')
        page.wait_for_load_state('networkidle')

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
    print(f'  \u2705 EP.{ep_num:02d} 이미지 변환 완료 ({exported}장)')
    print(f'  \U0001f4c1 {output_dir}/')


def main():
    parser = argparse.ArgumentParser(description='HTML 슬라이드 → PNG 이미지 변환')
    parser.add_argument('--ep', required=True, help='에피소드 번호 (예: 08)')
    parser.add_argument('--slide', type=int, default=None, help='특정 슬라이드만 변환 (예: 3)')
    args = parser.parse_args()

    export_slides(int(args.ep), args.slide)


if __name__ == '__main__':
    main()
