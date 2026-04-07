#!/usr/bin/env python3
"""upload_instagram.py — 에피소드 PNG 이미지를 인스타그램에 업로드

upload-post 라이브러리를 사용하여 8장 슬라이드를 캐러셀로 업로드한다.

사용법:
    python scripts/upload_instagram.py --ep 08 --caption "캡션"
    python scripts/upload_instagram.py --ep 08 --caption "캡션" --schedule "2026-02-25T09:00:00"
    python scripts/upload_instagram.py --ep 08 --auto-caption
    python scripts/upload_instagram.py --ep 08 --auto-caption --dry-run
    python scripts/upload_instagram.py --id gn_2026_w14_01 --auto-caption
    python scripts/upload_instagram.py --status <request_id>
"""

import os
import sys
import json
import re
import argparse

DEFAULT_USER = "code_snacku"
DEFAULT_HASHTAGS = (
    "#golang #go #개발 #프로그래밍 #코딩 #개발자 "
    "#백엔드 #서버개발"
)

MAX_KEY_POINTS = 3
MAX_HASHTAGS = 15
BASE_NEWS_TAGS = "#GeekNews #개발자뉴스 #테크뉴스 #주간뉴스 #개발"

HASHTAG_MAP = {
    "ai": "#AI #인공지능",
    "llm": "#LLM #대규모언어모델",
    "gpt": "#GPT #ChatGPT",
    "claude": "#Claude #Anthropic",
    "codex": "#Codex #OpenAI",
    "agent": "#AIAgent #에이전트",
    "데이터": "#데이터 #DataEngineering",
    "api": "#API #백엔드",
    "shell": "#Shell #터미널 #CLI",
    "생산성": "#생산성 #DevProductivity",
    "코딩": "#코딩 #개발",
    "오픈소스": "#오픈소스 #OpenSource",
    "rust": "#Rust #RustLang",
    "python": "#Python #파이썬",
    "go": "#Go #Golang",
    "javascript": "#JavaScript #JS",
    "typescript": "#TypeScript #TS",
    "react": "#React #프론트엔드",
    "devops": "#DevOps #인프라",
    "보안": "#보안 #Security",
    "스타트업": "#스타트업 #Startup",
    "saas": "#SaaS #소프트웨어",
    "디자인": "#디자인 #UXUI",
    "테스트": "#테스트 #Testing",
    "커리어": "#개발자커리어 #성장",
}


def load_episode_json(ep_num):
    """episodes/epXX.json을 로드하여 반환한다."""
    json_path = os.path.join("episodes", f"ep{ep_num:02d}.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ❌ {json_path} 파일을 찾을 수 없습니다.")
        sys.exit(1)


def get_slide_count(ep_num):
    """episodes/epXX.json에서 슬라이드 수를 읽어 반환한다."""
    data = load_episode_json(ep_num)
    return len(data.get("slides", []))


def build_slide_paths(ep_num):
    """에피소드 번호로 슬라이드 PNG 경로 리스트를 만든다 (JSON 기반 동적 감지)."""
    output_dir = os.path.join("output", f"ep{ep_num:02d}")
    slide_count = get_slide_count(ep_num)
    return [
        os.path.join(output_dir, f"slide_{i:02d}.png")
        for i in range(1, slide_count + 1)
    ]


def load_content_json(content_id):
    """content_id로 JSON을 로드하여 반환한다."""
    json_path = os.path.join("episodes", f"{content_id}.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ❌ {json_path} 파일을 찾을 수 없습니다.")
        sys.exit(1)


def build_slide_paths_by_id(content_id, data=None):
    """content_id로 슬라이드 PNG 경로 리스트를 만든다."""
    if data is None:
        data = load_content_json(content_id)
    output_dir = os.path.join("output", content_id)
    slide_count = len(data.get("slides", []))
    return [
        os.path.join(output_dir, f"slide_{i:02d}.png")
        for i in range(1, slide_count + 1)
    ]


def _extract_slide_data(data):
    """슬라이드를 한 번 순회하여 text_parts, key_points, one_liner를 반환한다."""
    text_parts = [data.get("title", "").lower()]
    key_points = []
    one_liner = ""

    for slide in data.get("slides", []):
        slide_type = slide.get("type", "")
        content = slide.get("content", {})

        if slide_type == "news-summary":
            key_points = content.get("key_points", [])[:MAX_KEY_POINTS]
        elif slide_type == "news-why":
            one_liner = content.get("one_liner", "")

        for val in content.values():
            if isinstance(val, str):
                text_parts.append(val.lower())
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        text_parts.append(item.lower())

    return " ".join(text_parts), key_points, one_liner


def _extract_all_text(data):
    """generate_news_hashtags가 단독 호출될 때만 사용되는 fallback."""
    full_text, _, _ = _extract_slide_data(data)
    return full_text


def generate_news_hashtags(data, full_text=None):
    """기사 콘텐츠에서 키워드 매칭으로 해시태그를 생성한다."""
    if full_text is None:
        full_text = _extract_all_text(data)

    # Tokenize for word-boundary matching (avoids "go" matching "goroutine")
    tokens = set(re.findall(r'[a-z가-힣]+', full_text))

    matched = []
    for keyword, tags in HASHTAG_MAP.items():
        if keyword in tokens:
            matched.append(tags)

    all_tags = BASE_NEWS_TAGS + " " + " ".join(matched)
    seen = set()
    unique = []
    for tag in all_tags.split():
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return " ".join(unique[:MAX_HASHTAGS])


def generate_news_caption(content_id, data=None):
    """GeekNews 기사 캡션과 해시태그를 자동 생성한다."""
    if data is None:
        data = load_content_json(content_id)

    full_text, key_points, one_liner = _extract_slide_data(data)
    hashtags = generate_news_hashtags(data, full_text=full_text)

    title = data.get("title", "")
    source_url = data.get("source_url", "")

    lines = [f"GeekNews 주간 픽 🔥 {title}", ""]
    for kp in key_points:
        lines.append(f"👉 {kp}")
    if one_liner:
        lines.extend(["", f"💡 {one_liner}"])
    if source_url:
        lines.extend(["", f"🔗 원문: {source_url}"])
    lines.extend(["", hashtags])

    return "\n".join(lines)


def check_slides_exist(paths):
    """모든 슬라이드 파일이 존재하는지 확인한다."""
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print("  ❌ 누락된 슬라이드 파일:")
        for m in missing:
            print(f"    - {m}")
        return False
    return True


def generate_caption(ep_num):
    """episodes/epXX.json에서 캡션을 자동 생성한다."""
    data = load_episode_json(ep_num)
    title = data.get("title", "")
    hook = data.get("hook", "")
    ep_label = f"EP.{ep_num:02d}"

    caption = f"Go 기초 문법 1분 정리 ⚡ {ep_label} {title}\n{hook}"
    return caption


def check_status(request_id):
    """비동기 업로드 상태를 확인한다."""
    api_key = os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        print("  ❌ UPLOAD_POST_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    from upload_post import UploadPostClient
    client = UploadPostClient(api_key=api_key)
    result = client.get_status(request_id)

    status = result.get("status", "unknown")
    print(f"  📋 업로드 상태: {status}")

    if status == "completed":
        for r in result.get("results", []):
            print(f"    플랫폼: {r.get('platform')}")
            print(f"    성공: {r.get('success')}")
            if r.get("post_url"):
                print(f"    🔗 게시물: {r['post_url']}")
            if r.get("error_message"):
                print(f"    ❌ 에러: {r['error_message']}")
    else:
        print(f"    전체 응답: {result}")


def upload(photos, caption, user, hashtags, schedule=None, timezone=None):
    """upload-post 라이브러리로 인스타그램 업로드를 실행한다."""
    api_key = os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        print("  ❌ UPLOAD_POST_API_KEY 환경변수가 설정되지 않았습니다.")
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
        description="에피소드 PNG 이미지를 인스타그램에 업로드"
    )
    parser.add_argument("--ep", default=None, help="에피소드 번호 (예: 08)")
    parser.add_argument("--id", default=None, help="콘텐츠 ID (예: gn_2026_w14_01)")
    parser.add_argument("--caption", default=None, help="캡션 텍스트")
    parser.add_argument(
        "--auto-caption",
        action="store_true",
        help="episodes/epXX.json에서 캡션 자동 생성",
    )
    parser.add_argument("--user", default=DEFAULT_USER, help=f"프로필 이름 (기본: {DEFAULT_USER})")
    parser.add_argument(
        "--hashtags", default=DEFAULT_HASHTAGS, help="첫 댓글 해시태그"
    )
    parser.add_argument("--schedule", default=None, help="예약 일시 (ISO 8601, 예: 2026-02-25T09:00:00)")
    parser.add_argument(
        "--timezone", default="Asia/Seoul", help="예약 시간대 (기본: Asia/Seoul)"
    )
    parser.add_argument("--status", default=None, help="업로드 상태 확인 (request_id)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 업로드 없이 파라미터만 출력",
    )
    args = parser.parse_args()

    if args.status:
        check_status(args.status)
        return

    if args.id:
        content_id = args.id
    elif args.ep:
        content_id = None  # use legacy ep_num path
    else:
        print("  ❌ --ep, --id, 또는 --status를 지정해주세요.")
        sys.exit(1)

    news_data = None
    if content_id:
        is_news = content_id.startswith("gn_")
        if is_news:
            news_data = load_content_json(content_id)
            photos = build_slide_paths_by_id(content_id, data=news_data)
        else:
            photos = build_slide_paths_by_id(content_id)
    else:
        ep_num = int(args.ep)
        photos = build_slide_paths(ep_num)
        is_news = False
        content_id = f"ep{ep_num:02d}"

    if not check_slides_exist(photos):
        print(f"\n  먼저 이미지를 생성해주세요:")
        if args.ep:
            print(f"    python3 scripts/export_images.py --ep {args.ep}")
        else:
            print(f"    python3 scripts/export_images.py --id {args.id}")
        sys.exit(1)

    if args.caption:
        caption = args.caption
    elif args.auto_caption:
        if is_news:
            caption = generate_news_caption(content_id, data=news_data)
        else:
            caption = generate_caption(int(args.ep))
    else:
        print("  ❌ --caption 또는 --auto-caption을 지정해주세요.")
        sys.exit(1)

    if is_news and args.auto_caption:
        hashtags = ""
    else:
        hashtags = args.hashtags

    if args.dry_run:
        print(f"  📋 [DRY RUN] 업로드 파라미터:")
        print(f"    플랫폼:  instagram")
        print(f"    프로필:  {args.user}")
        print(f"    콘텐츠:  {content_id}")
        print(f"    이미지:  {len(photos)}장")
        for p in photos:
            print(f"      - {p}")
        print(f"    캡션:")
        for line in caption.split("\n"):
            print(f"      {line}")
        print(f"    해시태그: {hashtags}")
        if args.schedule:
            print(f"    예약:    {args.schedule} ({args.timezone})")
        print(f"\n  ✅ DRY RUN 완료 (실제 업로드는 실행되지 않았습니다)")
        return

    print(f"  🚀 {content_id} 인스타그램 업로드 시작...")
    response = upload(
        photos=photos,
        caption=caption,
        user=args.user,
        hashtags=hashtags,
        schedule=args.schedule,
        timezone=args.timezone if args.schedule else None,
    )

    print(f"  ✅ 업로드 완료!")
    print(f"    플랫폼: instagram (@{args.user})")
    print(f"    콘텐츠: {content_id}")
    print(f"    이미지: {len(photos)}장 캐러셀")
    if args.schedule:
        print(f"    예약: {args.schedule} ({args.timezone})")
    print(f"    응답: {response}")


if __name__ == "__main__":
    main()
