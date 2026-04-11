# Graph Report - .  (2026-04-11)

## Corpus Check
- Large corpus: 56 files · ~601,407 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 124 nodes · 197 edges · 7 communities detected
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `generate_html()` - 14 edges
2. `esc()` - 12 edges
3. `main()` - 9 edges
4. `HTML Generator (generate_html.py)` - 9 edges
5. `GeekNews Pipeline (geeknews_pipeline.py)` - 8 edges
6. `GeekNews Track (gn_YYYY_wWW_NN)` - 8 edges
7. `main()` - 7 edges
8. `generate_news_caption()` - 6 edges
9. `select_articles_ai()` - 6 edges
10. `generate_article_json()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Card News Pipeline` --implements--> `HTML Generator (generate_html.py)`  [EXTRACTED]
  claude.md → scripts/generate_html.py
- `GeekNews Track (gn_YYYY_wWW_NN)` --references--> `GN W14 #2: Shell 트릭으로 생산성 10배 올리기`  [EXTRACTED]
  claude.md → output/gn_2026_w14_02/slide_01.png
- `GeekNews Track (gn_YYYY_wWW_NN)` --references--> `GN W14 #5`  [EXTRACTED]
  claude.md → output/gn_2026_w14_05/slide_01.png
- `GeekNews Track (gn_YYYY_wWW_NN)` --references--> `GN W14 #6: Anthropic AI 하네스 설계`  [EXTRACTED]
  claude.md → output/gn_2026_w14_06/slide_01.png
- `GeekNews Track (gn_YYYY_wWW_NN)` --references--> `GN W14 #7: 구글 TurboQuant`  [EXTRACTED]
  claude.md → output/gn_2026_w14_07/slide_01.png

## Hyperedges (group relationships)
- **Card News Production Pipeline** — script_generate_html, script_export_images, script_upload_instagram, script_geeknews_pipeline [EXTRACTED 1.00]
- **Developer Productivity Theme** — gn_w14_01_virtual_team, gn_w14_02_shell_tricks, gn_w14_03_coding_limit, concept_dev_productivity [INFERRED 0.75]
- **AI-Powered Features (Claude API)** — concept_ai_article_selection, concept_ai_json_generation, concept_quality_validation, entity_claude_api [EXTRACTED 1.00]

## Communities

### Community 0 - "GeekNews Pipeline (Scrape/Select/Generate)"
Cohesion: 0.12
Nodes (28): extract_json(), fetch_article_detail(), fetch_articles(), fetch_weekly_articles_html(), fetch_weekly_articles_rss(), generate_and_validate(), generate_article_json(), get_anthropic_client() (+20 more)

### Community 1 - "Instagram Upload & Caption"
Cohesion: 0.12
Nodes (26): build_slide_paths(), build_slide_paths_by_id(), check_slides_exist(), check_status(), _extract_all_text(), _extract_slide_data(), generate_caption(), generate_news_caption() (+18 more)

### Community 2 - "HTML Slide Renderer"
Cohesion: 0.23
Nodes (19): esc(), extract_user_types(), generate_html(), highlight_code(), highlight_line(), main(), Go 코드 전체에 구문 하이라이팅 적용, 코드 슬라이드에서 type X struct 패턴으로 사용자 정의 타입 추출 (+11 more)

### Community 3 - "Pipeline Infrastructure & Tools"
Cohesion: 0.14
Nodes (18): AI Article Selection (Claude API), AI JSON Generation (Claude API), GeekNews Article Scraping (HTML + RSS), News Hashtag Generation (keyword matching), Playwright Chromium Capture, AI Quality Validation, Upload-Post API Integration, Image Export Guide (+10 more)

### Community 4 - "Design System & Schemas"
Cohesion: 0.17
Nodes (15): Auto Caption Generation, Code Constraints (40char/15line), Color System (Go Blue #00ADD8 + GeekNews Orange #FF6B35), CSS Design System (1080x1350), Web Font Loading (Noto Sans KR + JetBrains Mono), Go Syntax Highlighter, EP JSON Schema (8 slides fixed), GN JSON Schema (3-9 slides variable) (+7 more)

### Community 5 - "GeekNews W14 Articles (Dev Productivity)"
Cohesion: 0.23
Nodes (12): AI Coding Tools, Developer Productivity, Garry Tan (YC CEO), gstack Framework, GN W14 #1: Claude Code 가상 엔지니어링 팀 (gstack), GN W14 #2: Shell 트릭으로 생산성 10배 올리기, GN W14 #3: 하루 코딩 4시간이 한계인 이유, GN W14 #4: 코드의 죽음은 과장되었다 (+4 more)

### Community 6 - "Playwright Image Exporter"
Cohesion: 1.0
Nodes (2): export_slides(), main()

## Knowledge Gaps
- **41 isolated node(s):** `코드 슬라이드에서 type X struct 패턴으로 사용자 정의 타입 추출`, `한 줄의 Go 코드에 구문 하이라이팅 HTML 적용`, `Go 코드 전체에 구문 하이라이팅 적용`, `에피소드 JSON 데이터로 완전한 HTML 문서 생성`, `episodes/epXX.json을 로드하여 반환한다.` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Card News Pipeline` connect `Pipeline Infrastructure & Tools` to `Design System & Schemas`, `GeekNews W14 Articles (Dev Productivity)`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `HTML Generator (generate_html.py)` connect `Design System & Schemas` to `Pipeline Infrastructure & Tools`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `GeekNews Track (gn_YYYY_wWW_NN)` connect `GeekNews W14 Articles (Dev Productivity)` to `Pipeline Infrastructure & Tools`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **What connects `코드 슬라이드에서 type X struct 패턴으로 사용자 정의 타입 추출`, `한 줄의 Go 코드에 구문 하이라이팅 HTML 적용`, `Go 코드 전체에 구문 하이라이팅 적용` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `GeekNews Pipeline (Scrape/Select/Generate)` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._
- **Should `Instagram Upload & Caption` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._
- **Should `Pipeline Infrastructure & Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._