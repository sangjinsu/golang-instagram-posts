#!/usr/bin/env python3
"""geeknews_pipeline.py — GeekNews daily 카드뉴스 주간 배치 파이프라인

GeekNews 주간 뉴스에서 하루 1개 발행용 7개 기사를 선별하여
인스타그램 카드뉴스를 자동 생성한다.

사용법:
    python3 scripts/geeknews_pipeline.py --week latest
    python3 scripts/geeknews_pipeline.py --week latest --dry-run
    python3 scripts/geeknews_pipeline.py --week latest --count 7 --json-only
    python3 scripts/geeknews_pipeline.py --week 2026-W14
"""

import json
import os
import sys
import re
import argparse
import subprocess
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# Helpers
# ============================================================

def extract_json(text):
    """LLM 응답에서 첫 번째 유효한 JSON 객체를 추출한다."""
    text = text.strip()
    for i, ch in enumerate(text):
        if ch == '{':
            try:
                decoder = json.JSONDecoder()
                obj, _ = decoder.raw_decode(text, i)
                return obj
            except json.JSONDecodeError:
                continue
    return None


_openai_client = None


def get_openai_client():
    """OpenAI client singleton."""
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def get_response_text(response):
    """Extract text from an OpenAI Responses API response."""
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text.strip()

    chunks = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
            elif isinstance(content, dict) and content.get("text"):
                chunks.append(content["text"])
    return "".join(chunks).strip()


def create_openai_response(prompt, instructions, max_output_tokens):
    """Create a text response using OpenAI Responses API."""
    client = get_openai_client()
    if not client:
        return None

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )
    return get_response_text(response)


# ============================================================
# Configuration
# ============================================================

GEEKNEWS_WEEKLY_URL = "https://news.hada.io/weekly"
GEEKNEWS_RSS_URL = "https://news.hada.io/rss"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
MAX_ARTICLES = 7  # daily publishing: 7 articles per weekly batch
MAX_CANDIDATES = 15
MAX_RETRY = 2
GEEKNEWS_SLIDE_TYPES = [
    "news-thumbnail",
    "news-summary",
    "news-why",
    "news-detail",
    "news-closing",
]

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)


# ============================================================
# Step 1: Scraping
# ============================================================

def _get_latest_weekly_issue_url():
    """주간 페이지에서 최신 이슈 URL을 가져온다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(GEEKNEWS_WEEKLY_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    weekly_div = soup.select_one(".weekly")
    if weekly_div:
        first_link = weekly_div.select_one("a.u")
        if first_link:
            href = first_link.get("href", "")
            if href.startswith("/"):
                return f"https://news.hada.io{href}"
            return href
    return None


def fetch_weekly_articles_html():
    """최신 GeekNews Weekly 이슈 페이지에서 기사 목록을 수집한다."""
    print("  📡 GeekNews 주간 페이지 스크래핑 중...")

    issue_url = _get_latest_weekly_issue_url()
    if not issue_url:
        print("  ⚠️ 최신 주간 이슈 URL을 찾을 수 없습니다.")
        return []

    print(f"  📄 이슈 페이지: {issue_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(issue_url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []

    topics_div = soup.select_one(".topics")
    if not topics_div:
        return []

    ul = topics_div.select_one("ul")
    if not ul:
        return []

    for li in ul.select("li"):
        title_el = li.select_one("a[href*='topic']")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if not href.startswith("http"):
            href = f"https://news.hada.io{href}"

        content_el = li.select_one(".content")
        summary = content_el.get_text(strip=True) if content_el else ""

        if title:
            articles.append({
                "title": title,
                "geeknews_url": href,
                "source_url": href,
                "points": 0,
                "comments": 0,
                "summary": summary,
            })

    print(f"  ✅ {len(articles)}개 기사 수집 완료")
    return articles


def fetch_weekly_articles_rss():
    """RSS 피드에서 기사 목록을 수집한다 (fallback)."""
    if not feedparser:
        return None

    print("  📡 GeekNews RSS 피드 파싱 중...")
    feed = feedparser.parse(GEEKNEWS_RSS_URL)
    if not feed.entries:
        return None

    articles = []
    for entry in feed.entries[:30]:
        articles.append({
            "title": entry.get("title", ""),
            "geeknews_url": entry.get("link", ""),
            "source_url": entry.get("link", ""),
            "points": 0,
            "comments": 0,
            "summary": entry.get("summary", ""),
        })

    if articles:
        print(f"  ✅ RSS에서 {len(articles)}개 기사 수집 완료")
    return articles if articles else None


def fetch_articles():
    """기사 목록을 수집한다. HTML 우선, RSS fallback."""
    try:
        articles = fetch_weekly_articles_html()
        if articles:
            return articles
    except Exception as e:
        print(f"  ⚠️ HTML 스크래핑 실패: {e}", file=sys.stderr)

    try:
        articles = fetch_weekly_articles_rss()
        if articles:
            return articles
    except Exception as e:
        print(f"  ⚠️ RSS 파싱 실패: {e}", file=sys.stderr)

    print("  ❌ 기사 수집 실패 (HTML + RSS 모두 실패)", file=sys.stderr)
    sys.exit(1)


def fetch_article_detail(geeknews_url):
    """GeekNews 개별 기사 페이지에서 상세 요약을 가져온다."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(geeknews_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        desc_el = soup.select_one(".topic_contents")
        if desc_el:
            return desc_el.get_text(strip=True)
        return ""
    except Exception:
        return ""


# ============================================================
# Step 2: Article Selection (AI)
# ============================================================

def select_articles_ai(articles, num=MAX_ARTICLES):
    """OpenAI API로 상위 기사를 선별한다."""
    if not OpenAI:
        print("  ⚠️ openai 패키지 없음, 포인트 기준 선별로 fallback")
        return select_articles_fallback(articles, num)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️ OPENAI_API_KEY 없음, 포인트 기준 선별로 fallback")
        return select_articles_fallback(articles, num)

    candidates = sorted(articles, key=lambda a: a["points"] + a["comments"], reverse=True)[:MAX_CANDIDATES]

    candidates_text = ""
    for i, art in enumerate(candidates, 1):
        candidates_text += f"{i}. 제목: {art['title']}\n"
        candidates_text += f"   포인트: {art['points']} | 댓글: {art['comments']}\n"
        candidates_text += f"   요약: {art['summary'][:200]}\n\n"

    print(f"  🤖 OpenAI API로 {num}개 기사 선별 중... ({OPENAI_MODEL})")

    try:
        result_text = create_openai_response(
            prompt=f"""다음 GeekNews 주간 뉴스 상위 {len(candidates)}개 후보입니다:

{candidates_text}

이 중 {num}개를 선정해주세요.
선정 기준 (우선순위):
1. 한국 개발자에게 실무적으로 유용한가
2. 기술적 깊이가 있어 카드뉴스로 풀어낼 내용이 충분한가
3. 커뮤니티에서 화제가 되고 있는가 (포인트/댓글 수 참고)

응답은 반드시 아래 JSON 형식만 출력하세요:
{{"selected": [{{"index": 번호, "reason": "선정 이유"}}, ...]}}""",
            instructions="당신은 한국 개발자 커뮤니티를 위한 테크 뉴스 큐레이터입니다. 인스타그램 카드뉴스에 적합한 기사를 선정합니다. 응답은 JSON만 출력하세요.",
            max_output_tokens=1024,
        )

        result = extract_json(result_text)
        if result:
            selected_indices = [s["index"] for s in result["selected"]]
            selected = [candidates[i - 1] for i in selected_indices if 1 <= i <= len(candidates)]

            if len(selected) >= num:
                selected = selected[:num]
            else:
                remaining = [c for c in candidates if c not in selected]
                selected.extend(remaining[:num - len(selected)])

            print(f"  ✅ AI 선별 완료: {len(selected)}개")
            for i, art in enumerate(selected, 1):
                print(f"    {i}. {art['title']}")
            return selected

    except Exception as e:
        print(f"  ⚠️ AI 선별 실패: {e}", file=sys.stderr)
        print("  30초 대기 후 재시도...")
        time.sleep(30)

        try:
            result_text = create_openai_response(
                prompt=f"다음 뉴스 후보 중 한국 개발자에게 가장 유용한 {num}개를 선정하세요. JSON으로만 응답: {{\"selected\": [{{\"index\": N}}]}}\n\n{candidates_text}",
                instructions="테크 뉴스 큐레이터. JSON만 응답.",
                max_output_tokens=1024,
            )
            result = extract_json(result_text)
            if result:
                selected_indices = [s["index"] for s in result["selected"]]
                selected = [candidates[i - 1] for i in selected_indices if 1 <= i <= len(candidates)]
                if selected:
                    return selected[:num]
        except Exception:
            pass

    print("  ⚠️ AI 선별 최종 실패, 포인트 기준 fallback")
    return select_articles_fallback(articles, num)


def select_articles_fallback(articles, num=MAX_ARTICLES):
    """포인트 + 댓글 수 기준으로 상위 기사를 선별한다."""
    sorted_articles = sorted(articles, key=lambda a: a["points"] + a["comments"], reverse=True)
    selected = sorted_articles[:num]
    print(f"  ✅ 포인트 기준 선별 완료: {len(selected)}개")
    for i, art in enumerate(selected, 1):
        print(f"    {i}. {art['title']} (P:{art['points']} C:{art['comments']})")
    return selected


# ============================================================
# Step 3: JSON Generation (AI)
# ============================================================

def generate_article_json(article, week_str, article_index, total_articles):
    """OpenAI API로 기사 하나의 카드뉴스 JSON을 생성한다."""
    if not OpenAI or not os.environ.get("OPENAI_API_KEY"):
        print(f"  ❌ OpenAI API 사용 불가, 기사 #{article_index} 건너뜀")
        return None

    time.sleep(1)
    detail = fetch_article_detail(article["geeknews_url"])
    summary_text = detail if detail else article.get("summary", "")

    next_article = "다음 기사가 있습니다" if article_index < total_articles else ""

    print(f"  🤖 기사 #{article_index} JSON 생성 중: {article['title'][:40]}... ({OPENAI_MODEL})")

    source_url = article.get('source_url', '') or article['geeknews_url']

    prompt = f"""다음 기사를 인스타그램 카드뉴스 JSON으로 변환해주세요.

기사 제목: {article['title']}
기사 URL: {source_url}
GeekNews URL: {article['geeknews_url']}
기사 요약/본문:
{summary_text[:3000]}

주차: {week_str}
기사 번호: {article_index}/{total_articles}

슬라이드 구성 규칙:
- 반드시 5장만 생성
- 1장: news-thumbnail — 첫 화면에서 멈추게 하는 호기심 훅
- 2장: news-summary — "이게 뭔데?"를 핵심 3개로 설명
- 3장: news-why — "왜 지금 중요한가?"를 구체적 신호/수치 3개로 설명
- 4장: news-detail — "개발자가 뭘 해볼까?" 중심의 실행 포인트 3개
- 5장: news-closing — 저장/공유를 유도하는 3줄 요약 + CTA

가독성/후킹 제약:
- topic은 28자 내외, hook은 45자 내외
- key_points, why points, detail points, summary는 각각 정확히 3개
- detail desc는 70자 내외, 한 슬라이드에 긴 문단 금지
- 모든 문장은 모바일에서 한눈에 읽히게 짧게 작성
- 제네릭한 표현보다 제품명, 수치, 명령어, 실무 행동을 우선
- news-detail content.points는 반드시 {{"label": "...", "desc": "..."}} 객체 배열
- JSON 외 텍스트, 마크다운 코드펜스, 설명 문장 출력 금지

응답은 반드시 아래 JSON 형식만 출력하세요:
{{
  "type": "geeknews",
  "week": "{week_str}",
  "article_index": {article_index},
  "title": "기사 제목 (한국어)",
  "source_url": "{source_url}",
  "geeknews_url": "{article['geeknews_url']}",
  "slides": [
    {{
      "slide_number": 1,
      "type": "news-thumbnail",
      "content": {{
        "series_name": "GeekNews 주간 픽",
        "series_sub": "이번 주 핫토픽 🔥",
        "icon": "주제 이모지",
        "week_label": "주차 라벨 (예: 2026년 14주차)",
        "article_num": "{article_index}/{total_articles}",
        "topic": "기사 제목 (한국어, 간결하게)",
        "hook": "한줄 훅 (호기심 유발)"
      }}
    }},
    {{
      "slide_number": 2,
      "type": "news-summary",
      "content": {{
        "question": "이게 뭔데? 🤔",
        "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
        "source": "출처명"
      }}
    }},
    {{
      "slide_number": 3,
      "type": "news-why",
      "content": {{
        "title": "왜 지금 중요한가? 💡",
        "points": ["구체적 신호/수치 1", "구체적 신호/수치 2", "실무 맥락 3"],
        "one_liner": "한줄 결론"
      }}
    }},
    {{
      "slide_number": 4,
      "type": "news-detail",
      "content": {{
        "title": "개발자가 뭘 해볼까? 🔍",
        "points": [
          {{"label": "실행 포인트 1", "desc": "짧은 설명"}},
          {{"label": "실행 포인트 2", "desc": "짧은 설명"}},
          {{"label": "실행 포인트 3", "desc": "짧은 설명"}}
        ]
      }}
    }},
    {{
      "slide_number": 5,
      "type": "news-closing",
      "content": {{
        "summary": ["핵심 1", "핵심 2", "핵심 3"],
        "source_link": "{source_url}",
        "next_article": "{next_article}",
        "cta": "저장하고 나중에 읽기 📌"
      }}
    }}
  ]
}}"""

    try:
        result_text = create_openai_response(
            prompt=prompt,
            instructions="당신은 인스타그램 카드뉴스 콘텐츠 제작자입니다. 한국 개발자를 위한 기술 뉴스를 쉽고 매력적인 카드뉴스로 변환합니다. 이모지를 적극 활용하고, 한국어로 자연스럽게 작성합니다. 응답은 JSON만 출력하세요.",
            max_output_tokens=4096,
        )

        data = extract_json(result_text)
        if data:
            slide_count = len(data.get('slides', []))
            print(f"  ✅ 기사 #{article_index} JSON 생성 완료 ({slide_count}장)")
            return data

    except Exception as e:
        print(f"  ⚠️ 기사 #{article_index} JSON 생성 실패: {e}", file=sys.stderr)

    return None


# ============================================================
# Step 4: Quality Validation (AI)
# ============================================================

def _is_nonempty_string(value):
    """Return True for useful string fields."""
    return isinstance(value, str) and bool(value.strip())


def _check_string_list(value, field_name, expected_len, max_item_len, issues):
    """Validate compact list fields used by GeekNews slides."""
    if not isinstance(value, list):
        issues.append(f"{field_name} 배열이 없습니다.")
        return
    if len(value) != expected_len:
        issues.append(f"{field_name} 항목 수가 {expected_len}개가 아닙니다.")
    for i, item in enumerate(value, 1):
        if not _is_nonempty_string(item):
            issues.append(f"{field_name}[{i}]가 빈 문자열입니다.")
        elif len(item) > max_item_len:
            issues.append(f"{field_name}[{i}]가 너무 깁니다. ({len(item)}자)")


def validate_required_structure(data):
    """Validate required GeekNews structure without asking an LLM."""
    issues = []

    if not isinstance(data, dict):
        return False, ["최상위 JSON 객체가 아닙니다."]

    if data.get("type") != "geeknews":
        issues.append("type은 geeknews여야 합니다.")

    for field in ("week", "article_index", "title", "source_url", "geeknews_url"):
        if field == "article_index":
            if not isinstance(data.get(field), int):
                issues.append("article_index는 정수여야 합니다.")
        elif not _is_nonempty_string(data.get(field)):
            issues.append(f"{field} 필드가 비어 있습니다.")

    slides = data.get("slides")
    if not isinstance(slides, list):
        return False, issues + ["slides 배열이 없습니다."]

    if len(slides) != len(GEEKNEWS_SLIDE_TYPES):
        issues.append(f"GeekNews daily는 5장이어야 합니다. 현재 {len(slides)}장입니다.")

    for idx, expected_type in enumerate(GEEKNEWS_SLIDE_TYPES, 1):
        if idx > len(slides):
            issues.append(f"{idx}번 슬라이드가 없습니다.")
            continue

        slide = slides[idx - 1]
        if slide.get("slide_number") != idx:
            issues.append(f"{idx}번 슬라이드 번호가 연속되지 않습니다.")
        if slide.get("type") != expected_type:
            issues.append(f"{idx}번 슬라이드는 {expected_type} 타입이어야 합니다.")

        content = slide.get("content")
        if not isinstance(content, dict):
            issues.append(f"{idx}번 슬라이드 content가 객체가 아닙니다.")
            continue

        if expected_type == "news-thumbnail":
            for field in ("series_name", "series_sub", "week_label", "article_num", "topic", "hook"):
                if not _is_nonempty_string(content.get(field)):
                    issues.append(f"news-thumbnail.{field} 필드가 비어 있습니다.")
            if len(str(content.get("topic", ""))) > 40:
                issues.append("news-thumbnail.topic이 너무 깁니다.")
            if len(str(content.get("hook", ""))) > 70:
                issues.append("news-thumbnail.hook이 너무 깁니다.")

        elif expected_type == "news-summary":
            if not _is_nonempty_string(content.get("question")):
                issues.append("news-summary.question 필드가 비어 있습니다.")
            _check_string_list(content.get("key_points"), "news-summary.key_points", 3, 95, issues)

        elif expected_type == "news-why":
            if not _is_nonempty_string(content.get("title")):
                issues.append("news-why.title 필드가 비어 있습니다.")
            _check_string_list(content.get("points"), "news-why.points", 3, 95, issues)
            if not _is_nonempty_string(content.get("one_liner")):
                issues.append("news-why.one_liner 필드가 비어 있습니다.")
            elif len(content["one_liner"]) > 90:
                issues.append("news-why.one_liner가 너무 깁니다.")

        elif expected_type == "news-detail":
            if not _is_nonempty_string(content.get("title")):
                issues.append("news-detail.title 필드가 비어 있습니다.")
            points = content.get("points")
            if not isinstance(points, list):
                issues.append("news-detail.points 배열이 없습니다.")
            else:
                if len(points) != 3:
                    issues.append("news-detail.points 항목 수가 3개가 아닙니다.")
                for i, point in enumerate(points, 1):
                    if not isinstance(point, dict):
                        issues.append(f"news-detail.points[{i}]가 객체가 아닙니다.")
                        continue
                    if not _is_nonempty_string(point.get("label")):
                        issues.append(f"news-detail.points[{i}].label이 비어 있습니다.")
                    elif len(point["label"]) > 45:
                        issues.append(f"news-detail.points[{i}].label이 너무 깁니다.")
                    if not _is_nonempty_string(point.get("desc")):
                        issues.append(f"news-detail.points[{i}].desc가 비어 있습니다.")
                    elif len(point["desc"]) > 105:
                        issues.append(f"news-detail.points[{i}].desc가 너무 깁니다.")

        elif expected_type == "news-closing":
            _check_string_list(content.get("summary"), "news-closing.summary", 3, 90, issues)
            for field in ("source_link", "cta"):
                if not _is_nonempty_string(content.get(field)):
                    issues.append(f"news-closing.{field} 필드가 비어 있습니다.")
            if len(str(content.get("cta", ""))) > 80:
                issues.append("news-closing.cta가 너무 깁니다.")

    return not issues, issues


def build_quality_validation_payload(data):
    """Build a compact payload so AI quality checks do not receive truncated JSON."""
    lines = [
        f"제목: {data.get('title', '')}",
        f"원문: {data.get('source_url', '')}",
        "슬라이드 요약:",
    ]
    for slide in data.get("slides", []):
        content = slide.get("content", {})
        slide_type = slide.get("type", "")
        if slide_type == "news-thumbnail":
            body = f"topic={content.get('topic', '')} / hook={content.get('hook', '')}"
        elif slide_type == "news-summary":
            body = " | ".join(content.get("key_points", []))
        elif slide_type == "news-why":
            body = " | ".join(content.get("points", [])) + f" / {content.get('one_liner', '')}"
        elif slide_type == "news-detail":
            point_texts = []
            for point in content.get("points", []):
                point_texts.append(f"{point.get('label', '')}: {point.get('desc', '')}")
            body = " | ".join(point_texts)
        elif slide_type == "news-closing":
            body = " | ".join(content.get("summary", [])) + f" / CTA={content.get('cta', '')}"
        else:
            body = json.dumps(content, ensure_ascii=False)
        lines.append(f"- {slide.get('slide_number')}. {slide_type}: {body}")
    return "\n".join(lines)


def validate_article_json(data, article):
    """생성된 JSON의 품질을 검증한다."""
    structure_ok, structure_issues = validate_required_structure(data)
    if not structure_ok:
        return False, structure_issues

    if not OpenAI or not os.environ.get("OPENAI_API_KEY"):
        return True, []

    quality_payload = build_quality_validation_payload(data)
    article_title = article['title']
    article_summary = article.get('summary', '')[:500]

    validation_prompt = f"""다음 인스타그램 카드뉴스 문안을 검증해주세요:

{quality_payload}

원문 기사 제목: {article_title}
원문 요약: {article_summary}

검증 기준:
1. 사실 왜곡: 원문과 다른 내용이 있는가?
2. 한국어 품질: 자연스럽고 모바일에서 읽기 쉬운가?
3. 후킹 강도: 1~2장에서 저장/스와이프를 유도하는가?
4. 길이 적절성: 한 슬라이드에 텍스트가 과밀하지 않은가?

응답은 반드시 JSON만:
{{"verified": true, "issues": []}} 또는 {{"verified": false, "issues": ["이슈"]}}"""

    try:
        result_text = create_openai_response(
            prompt=validation_prompt,
            instructions="인스타그램 카드뉴스 콘텐츠 품질 검증자입니다. JSON 문법이나 필수 슬라이드는 이미 코드로 검증되었습니다. 사실성, 한국어 가독성, 후킹, 텍스트 과밀만 판단하세요. JSON만 응답하세요.",
            max_output_tokens=512,
        )

        result = extract_json(result_text)
        if result:
            return result.get("verified", True), result.get("issues", [])

    except Exception as e:
        print(f"  ⚠️ 품질 검증 실패: {e}", file=sys.stderr)

    return True, []


def generate_and_validate(article, week_str, article_index, total_articles):
    """JSON 생성 + 품질 검증. 실패 시 재생성."""
    for attempt in range(MAX_RETRY + 1):
        data = generate_article_json(article, week_str, article_index, total_articles)
        if not data:
            if attempt < MAX_RETRY:
                print(f"  🔄 기사 #{article_index} 재시도 ({attempt + 1}/{MAX_RETRY})...")
                time.sleep(5)
                continue
            return None

        verified, issues = validate_article_json(data, article)
        if verified:
            return data

        print(f"  ⚠️ 기사 #{article_index} 검증 실패: {', '.join(issues)}")
        if attempt < MAX_RETRY:
            print(f"  🔄 재생성 ({attempt + 1}/{MAX_RETRY})...")
            time.sleep(3)

    print(f"  ❌ 기사 #{article_index} 최종 실패, 건너뜀")
    return None


# ============================================================
# Step 5: Pipeline Execution
# ============================================================

def get_week_string():
    """현재 주차 문자열을 반환한다."""
    now = datetime.now()
    week_num = now.isocalendar()[1]
    return f"{now.year}_w{week_num:02d}"


def parse_week_arg(week_arg):
    """--week 인자를 파싱한다."""
    if week_arg == "latest":
        return get_week_string()

    m = re.match(r"(\d{4})-W(\d{1,2})", week_arg, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_w{int(m.group(2)):02d}"

    m = re.match(r"(\d{4})_w(\d{1,2})", week_arg, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_w{int(m.group(2)):02d}"

    print(f"  ❌ 잘못된 주차 형식: {week_arg} (예: latest, 2026-W14)")
    sys.exit(1)


def save_json(data, content_id):
    """JSON 파일을 저장한다."""
    json_path = os.path.join(PROJECT_DIR, "episodes", f"{content_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 {json_path} 저장 완료")
    return json_path


def run_existing_pipeline(content_id, dry_run=False):
    """기존 파이프라인 스크립트를 실행한다."""
    print(f"\n  📄 HTML 생성: {content_id}")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "generate_html.py"), "--id", content_id],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ HTML 생성 실패: {result.stderr}", file=sys.stderr)
        return False
    print(result.stdout.strip())

    print(f"  📸 PNG 변환: {content_id}")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "export_images.py"), "--id", content_id],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ PNG 변환 실패: {result.stderr}", file=sys.stderr)
        return False
    print(result.stdout.strip())

    if dry_run:
        print(f"  ⏭️ DRY RUN: 업로드 건너뜀")
        return True

    print(f"  🚀 업로드: {content_id}")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "upload_instagram.py"),
         "--id", content_id, "--auto-caption"],
        cwd=PROJECT_DIR, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ 업로드 실패: {result.stderr}", file=sys.stderr)
        return False
    print(result.stdout.strip())
    return True


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="GeekNews 하루 1개 발행용 주간 7개 카드뉴스 자동 생성 파이프라인"
    )
    parser.add_argument("--week", default="latest", help="주차 (예: latest, 2026-W14)")
    parser.add_argument("--dry-run", action="store_true", help="JSON + HTML + PNG까지만 (업로드 안 함)")
    parser.add_argument("--json-only", action="store_true", help="JSON 생성까지만")
    parser.add_argument("--scrape-only", action="store_true", help="기사 목록만 JSON으로 출력 (AI 없이)")
    parser.add_argument("--count", type=int, default=MAX_ARTICLES, help=f"선별할 기사 수 (daily 기본: {MAX_ARTICLES}개 = 7일치)")
    args = parser.parse_args()

    week_str = parse_week_arg(args.week)
    num_articles = args.count

    print(f"\n{'='*60}")
    print(f"  GeekNews Daily 카드뉴스 파이프라인")
    print(f"  주차: {week_str} | 기사: {num_articles}개")
    print(f"  운영: 하루 1개 발행용 주간 배치")
    mode_str = "스크래핑만" if args.scrape_only else "JSON만" if args.json_only else "DRY RUN" if args.dry_run else "전체 실행"
    print(f"  모드: {mode_str}")
    print(f"{'='*60}\n")

    print("[Step 1] 기사 수집")
    articles = fetch_articles()

    if args.scrape_only:
        output = {"week": week_str, "total": len(articles), "articles": articles}
        output_path = os.path.join(PROJECT_DIR, "episodes", f"gn_{week_str}_candidates.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ 기사 목록 저장 완료: {output_path}")
        print(f"  📊 총 {len(articles)}개 기사")
        for i, a in enumerate(articles[:10], 1):
            print(f"    {i}. {a['title'][:60]}")
        if len(articles) > 10:
            print(f"    ... 외 {len(articles) - 10}개")
        return

    if len(articles) < num_articles:
        print(f"  ⚠️ 수집된 기사({len(articles)}개)가 요청({num_articles}개)보다 적음")
        num_articles = len(articles)

    print(f"\n[Step 2/5] 기사 선별 ({num_articles}개)")
    selected = select_articles_ai(articles, num_articles)

    print(f"\n[Step 3-4/5] JSON 생성 + 품질 검증")
    generated = []
    backup_candidates = [a for a in articles if a not in selected]
    backup_idx = 0

    for i, article in enumerate(selected, 1):
        content_id = f"gn_{week_str}_{i:02d}"
        data = generate_and_validate(article, week_str, i, num_articles)

        if not data:
            while backup_idx < len(backup_candidates):
                backup = backup_candidates[backup_idx]
                backup_idx += 1
                print(f"  🔄 대체 기사 시도: {backup['title'][:40]}...")
                data = generate_and_validate(backup, week_str, i, num_articles)
                if data:
                    break

        if data:
            save_json(data, content_id)
            generated.append(content_id)
        else:
            print(f"  ❌ 기사 #{i} 최종 실패 (대체 기사도 실패)")

    print(f"\n  📊 JSON 생성 결과: {len(generated)}/{num_articles}개 성공")

    if not generated:
        print("  ❌ 생성된 JSON이 없습니다. 종료.")
        sys.exit(1)

    if args.json_only:
        print("\n  ✅ JSON 생성 완료 (--json-only)")
        print(f"  발행 계획: 하루 1개 기준 {len(generated)}일치")
        for cid in generated:
            print(f"    📄 episodes/{cid}.json")
        return

    print(f"\n[Step 5/5] 파이프라인 실행")
    success_count = 0
    for content_id in generated:
        print(f"\n{'─'*40}")
        print(f"  처리 중: {content_id}")
        print(f"{'─'*40}")

        if run_existing_pipeline(content_id, args.dry_run):
            success_count += 1
        else:
            print(f"  ⚠️ {content_id} 파이프라인 실패, 다음 기사로 진행")

    print(f"\n{'='*60}")
    print(f"  완료!")
    print(f"  생성: {len(generated)}/{num_articles}개")
    print(f"  파이프라인 성공: {success_count}/{len(generated)}개")
    print(f"  발행 계획: 하루 1개 기준 {success_count}일치")
    if args.dry_run:
        print(f"  모드: DRY RUN (업로드 건너뜀)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
