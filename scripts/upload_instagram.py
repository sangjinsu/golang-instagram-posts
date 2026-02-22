#!/usr/bin/env python3
"""upload_instagram.py — 에피소드 PNG 이미지를 인스타그램에 업로드

upload-post 라이브러리를 사용하여 8장 슬라이드를 캐러셀로 업로드한다.

사용법:
    python scripts/upload_instagram.py --ep 08 --caption "캡션"
    python scripts/upload_instagram.py --ep 08 --caption "캡션" --schedule "2026-02-25T09:00:00"
    python scripts/upload_instagram.py --ep 08 --auto-caption
    python scripts/upload_instagram.py --ep 08 --auto-caption --dry-run
"""

import os
import sys
import json
import argparse

SLIDE_COUNT = 8
DEFAULT_USER = "code_snacku"
DEFAULT_HASHTAGS = (
    "#golang #go #개발 #프로그래밍 #코딩 #개발자 "
    "#golang #go #백엔드 #서버개발"
)


def build_slide_paths(ep_num):
    """에피소드 번호로 slide_01~08.png 경로 리스트를 만든다."""
    output_dir = os.path.join("output", f"ep{ep_num:02d}")
    return [
        os.path.join(output_dir, f"slide_{i:02d}.png")
        for i in range(1, SLIDE_COUNT + 1)
    ]


def check_slides_exist(paths):
    """모든 슬라이드 파일이 존재하는지 확인한다."""
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print("  \u274c 누락된 슬라이드 파일:")
        for m in missing:
            print(f"    - {m}")
        return False
    return True


def generate_caption(ep_num):
    """episodes/epXX.json에서 캡션을 자동 생성한다."""
    json_path = os.path.join("episodes", f"ep{ep_num:02d}.json")
    if not os.path.exists(json_path):
        print(f"  \u274c {json_path} 파일을 찾을 수 없습니다.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "")
    hook = data.get("hook", "")
    ep_label = f"EP.{ep_num:02d}"

    caption = f"Go \uae30\ucd08 \ubb38\ubc95 1\ubd84 \uc815\ub9ac \u26a1 {ep_label} {title}\n{hook}"
    return caption


def upload(photos, caption, user, hashtags, schedule=None, timezone=None):
    """upload-post 라이브러리로 인스타그램 업로드를 실행한다."""
    api_key = os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        print("  \u274c UPLOAD_POST_API_KEY \ud658\uacbd\ubcc0\uc218\uac00 \uc124\uc815\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4.")
        sys.exit(1)

    from upload_post import UploadPostClient

    client = UploadPostClient(api_key=api_key)

    kwargs = {
        "photos": photos,
        "title": caption,
        "user": user,
        "platforms": ["instagram"],
        "instagram_first_comment": hashtags,
    }

    if schedule:
        kwargs["schedule"] = schedule
    if timezone:
        kwargs["timezone"] = timezone

    response = client.upload_photos(**kwargs)
    return response


def main():
    parser = argparse.ArgumentParser(
        description="\uc5d0\ud53c\uc18c\ub4dc PNG \uc774\ubbf8\uc9c0\ub97c \uc778\uc2a4\ud0c0\uadf8\ub7a8\uc5d0 \uc5c5\ub85c\ub4dc"
    )
    parser.add_argument("--ep", required=True, help="\uc5d0\ud53c\uc18c\ub4dc \ubc88\ud638 (\uc608: 08)")
    parser.add_argument("--caption", default=None, help="\uce90\uc158 \ud14d\uc2a4\ud2b8")
    parser.add_argument(
        "--auto-caption",
        action="store_true",
        help="episodes/epXX.json\uc5d0\uc11c \uce90\uc158 \uc790\ub3d9 \uc0dd\uc131",
    )
    parser.add_argument("--user", default=DEFAULT_USER, help=f"\ud504\ub85c\ud544 \uc774\ub984 (\uae30\ubcf8: {DEFAULT_USER})")
    parser.add_argument(
        "--hashtags", default=DEFAULT_HASHTAGS, help="\uccab \ub313\uae00 \ud574\uc2dc\ud0dc\uadf8"
    )
    parser.add_argument("--schedule", default=None, help="\uc608\uc57d \uc77c\uc2dc (ISO 8601, \uc608: 2026-02-25T09:00:00)")
    parser.add_argument(
        "--timezone", default="Asia/Seoul", help="\uc608\uc57d \uc2dc\uac04\ub300 (\uae30\ubcf8: Asia/Seoul)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="\uc2e4\uc81c \uc5c5\ub85c\ub4dc \uc5c6\uc774 \ud30c\ub77c\ubbf8\ud130\ub9cc \ucd9c\ub825",
    )
    args = parser.parse_args()

    ep_num = int(args.ep)
    photos = build_slide_paths(ep_num)

    # 슬라이드 파일 존재 확인
    if not check_slides_exist(photos):
        print(f"\n  \uba3c\uc800 \uc774\ubbf8\uc9c0\ub97c \uc0dd\uc131\ud574\uc8fc\uc138\uc694:")
        print(f"    python3 scripts/export_images.py --ep {args.ep}")
        sys.exit(1)

    # 캡션 결정
    if args.caption:
        caption = args.caption
    elif args.auto_caption:
        caption = generate_caption(ep_num)
    else:
        print("  \u274c --caption \ub610\ub294 --auto-caption\uc744 \uc9c0\uc815\ud574\uc8fc\uc138\uc694.")
        sys.exit(1)

    # dry-run 모드
    if args.dry_run:
        print(f"  \U0001f4cb [DRY RUN] \uc5c5\ub85c\ub4dc \ud30c\ub77c\ubbf8\ud130:")
        print(f"    \ud50c\ub7ab\ud3fc:  instagram")
        print(f"    \ud504\ub85c\ud544:  {args.user}")
        print(f"    \uc774\ubbf8\uc9c0:  {len(photos)}\uc7a5")
        for p in photos:
            print(f"      - {p}")
        print(f"    \uce90\uc158:")
        for line in caption.split("\n"):
            print(f"      {line}")
        print(f"    \ud574\uc2dc\ud0dc\uadf8: {args.hashtags}")
        if args.schedule:
            print(f"    \uc608\uc57d:    {args.schedule} ({args.timezone})")
        print(f"\n  \u2705 DRY RUN \uc644\ub8cc (\uc2e4\uc81c \uc5c5\ub85c\ub4dc\ub294 \uc2e4\ud589\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4)")
        return

    # 실제 업로드
    print(f"  \U0001f680 EP.{ep_num:02d} \uc778\uc2a4\ud0c0\uadf8\ub7a8 \uc5c5\ub85c\ub4dc \uc2dc\uc791...")
    response = upload(
        photos=photos,
        caption=caption,
        user=args.user,
        hashtags=args.hashtags,
        schedule=args.schedule,
        timezone=args.timezone if args.schedule else None,
    )

    print(f"  \u2705 \uc5c5\ub85c\ub4dc \uc644\ub8cc!")
    print(f"    \ud50c\ub7ab\ud3fc: instagram (@{args.user})")
    print(f"    \uc774\ubbf8\uc9c0: {len(photos)}\uc7a5 \uce90\ub7ec\uc140")
    if args.schedule:
        print(f"    \uc608\uc57d: {args.schedule} ({args.timezone})")
    print(f"    \uc751\ub2f5: {response}")


if __name__ == "__main__":
    main()
