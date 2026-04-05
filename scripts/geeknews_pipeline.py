#!/usr/bin/env python3
"""geeknews_pipeline.py — GeekNews 주간 뉴스 카드뉴스 자동 생성 파이프라인

GeekNews 주간 뉴스에서 7개 기사를 선별하여 인스타그램 카드뉴스를 자동 생성한다.

사용법:
    python3 scripts/geeknews_pipeline.py --week latest
    python3 scripts/geeknews_pipeline.py --week latest --dry-run
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
    import anthropic
except ImportError:
    anthropic = None


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


_anthropic_client = None


def get_anthropic_client():
    """Anthropic 클라이언트를 싱글톤으로 반환한다."""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


# ============================================================
# Configuration
# ============================================================

GEEKNEWS_WEEKLY_URL = "https://news.hada.io/weekly"
GEEKNEWS_RSS_URL = "https://news.hada.io/rss"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_ARTICLES = 7
MAX_CANDIDATES = 15
MAX_RETRY = 2

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
    """Claude API로 상위 기사를 선별한다."""
    if not anthropic:
        print("  ⚠️ anthropic 패키지 없음, 포인트 기준 선별로 fallback")
        return select_articles_fallback(articles, num)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️ ANTHROPIC_API_KEY 없음, 포인트 기준 선별로 fallback")
        return select_articles_fallback(articles, num)

    candidates = sorted(articles, key=lambda a: a["points"] + a["comments"], reverse=True)[:MAX_CANDIDATES]

    candidates_text = ""
    for i, art in enumerate(candidates, 1):
        candidates_text += f"{i}. 제목: {art['title']}\n"
        candidates_text += f"   포인트: {art['points']} | 댓글: {art['comments']}\n"
        candidates_text += f"   요약: {art['summary'][:200]}\n\n"

    print(f"  🤖 Claude API로 {num}개 기사 선별 중...")
    client = get_anthropic_client()

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""다음 GeekNews 주간 뉴스 상위 {len(candidates)}개 후보입니다:

{candidates_text}

이 중 {num}개를 선정해주세요.
선정 기준 (우선순위):
1. 한국 개발자에게 실무적으로 유용한가
2. 기술적 깊이가 있어 카드뉴스로 풀어낼 내용이 충분한가
3. 커뮤니티에서 화제가 되고 있는가 (포인트/댓글 수 참고)

응답은 반드시 아래 JSON 형식만 출력하세요:
{{"selected": [{{"index": 번호, "reason": "선정 이유"}}, ...]}}"""
            }],
            system="당신은 한국 개발자 커뮤니티를 위한 테크 뉴스 큐레이터입니다. 인스타그램 카드뉴스에 적합한 기사를 선정합니다. 응답은 JSON만 출력하세요."
        )

        result_text = response.content[0].text.strip()
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
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"다음 뉴스 후보 중 한국 개발자에게 가장 유용한 {num}개를 선정하세요. JSON으로만 응답: {{\"selected\": [{{\"index\": N}}]}}\n\n{candidates_text}"
                }],
                system="테크 뉴스 큐레이터. JSON만 응답."
            )
            result_text = response.content[0].text.strip()
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
    """Claude API로 기사 하나의 카드뉴스 JSON을 생성한다."""
    if not anthropic or not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"  ❌ Claude API 사용 불가, 기사 #{article_index} 건너뜀")
        return None

    time.sleep(1)
    detail = fetch_article_detail(article["geeknews_url"])
    summary_text = detail if detail else article.get("summary", "")

    next_article = "다음 기사가 있습니다" if article_index < total_articles else ""

    client = get_anthropic_client()
    print(f"  🤖 기사 #{article_index} JSON 생성 중: {article['title'][:40]}...")

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
- 최소 3장, 최대 9장
- 1장 (필수): news-thumbnail
- 2장 (필수): news-summary — 핵심 포인트 3~5개
- 중간 (선택 0~1장): news-why — 왜 중요한가
- 중간 (선택 0~5장): news-detail — 상세 포인트
- 마지막 (필수): news-closing — 요약 + CTA

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
      "slide_number": N,
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
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system="당신은 인스타그램 카드뉴스 콘텐츠 제작자입니다. 한국 개발자를 위한 기술 뉴스를 쉽고 매력적인 카드뉴스로 변환합니다. 이모지를 적극 활용하고, 한국어로 자연스럽게 작성합니다. 응답은 JSON만 출력하세요."
        )

        result_text = response.content[0].text.strip()
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

def validate_article_json(data, article):
    """생성된 JSON의 품질을 검증한다."""
    if not anthropic or not os.environ.get("ANTHROPIC_API_KEY"):
        return True, []

    client = get_anthropic_client()

    data_str = json.dumps(data, ensure_ascii=False, indent=2)[:3000]
    article_title = article['title']
    article_summary = article.get('summary', '')[:500]

    validation_prompt = f"""다음 카드뉴스 JSON을 검증해주세요:

{data_str}

원문 기사 제목: {article_title}
원문 요약: {article_summary}

검증 기준:
1. 사실 왜곡: 원문과 다른 내용이 있는가?
2. 슬라이드 구성: 필수 슬라이드(news-thumbnail, news-summary, news-closing)가 모두 있는가?
3. 한국어 품질: 자연스러운 한국어인가?
4. 길이 적절성: 슬라이드당 텍스트가 너무 길거나 짧지 않은가?

응답은 반드시 JSON만:
{{"verified": true, "issues": []}} 또는 {{"verified": false, "issues": ["이슈"]}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": validation_prompt}],
            system="인스타그램 카드뉴스 콘텐츠 품질 검증자. JSON만 응답."
        )

        result_text = response.content[0].text.strip()
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
        description="GeekNews 주간 뉴스 카드뉴스 자동 생성 파이프라인"
    )
    parser.add_argument("--week", default="latest", help="주차 (예: latest, 2026-W14)")
    parser.add_argument("--dry-run", action="store_true", help="JSON + HTML + PNG까지만 (업로드 안 함)")
    parser.add_argument("--json-only", action="store_true", help="JSON 생성까지만")
    parser.add_argument("--scrape-only", action="store_true", help="기사 목록만 JSON으로 출력 (AI 없이)")
    parser.add_argument("--count", type=int, default=MAX_ARTICLES, help=f"선별할 기사 수 (기본: {MAX_ARTICLES})")
    args = parser.parse_args()

    week_str = parse_week_arg(args.week)
    num_articles = args.count

    print(f"\n{'='*60}")
    print(f"  GeekNews 카드뉴스 파이프라인")
    print(f"  주차: {week_str} | 기사: {num_articles}개")
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
    if args.dry_run:
        print(f"  모드: DRY RUN (업로드 건너뜀)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
