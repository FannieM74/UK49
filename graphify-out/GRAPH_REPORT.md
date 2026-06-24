# Graph Report - .  (2026-06-24)

## Corpus Check
- Corpus is ~14,347 words - fits in a single context window. You may not need a graph.

## Summary
- 174 nodes · 241 edges · 22 communities (15 shown, 7 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Frontend Package Config|Frontend Package Config]]
- [[_COMMUNITY_Frontend UI Pages|Frontend UI Pages]]
- [[_COMMUNITY_Backend Database|Backend Database]]
- [[_COMMUNITY_Frontend TypeScript Config|Frontend TypeScript Config]]
- [[_COMMUNITY_Backend Analysis Tools|Backend Analysis Tools]]
- [[_COMMUNITY_Frontend UI Components|Frontend UI Components]]
- [[_COMMUNITY_Gemini LLM Wrapper|Gemini LLM Wrapper]]
- [[_COMMUNITY_CrewAI Agent Pipeline|CrewAI Agent Pipeline]]
- [[_COMMUNITY_Scraper Tool|Scraper Tool]]
- [[_COMMUNITY_Backend API Models|Backend API Models]]
- [[_COMMUNITY_Frontend Layout|Frontend Layout]]
- [[_COMMUNITY_Start Script|Start Script]]
- [[_COMMUNITY_ESLint Config|ESLint Config]]
- [[_COMMUNITY_Next.js Config|Next.js Config]]
- [[_COMMUNITY_PostCSS Config|PostCSS Config]]
- [[_COMMUNITY_Frontend Start Script|Frontend Start Script]]

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 16 edges
2. `get_connection()` - 13 edges
3. `UK49ScraperTool` - 10 edges
4. `GeminiChat` - 6 edges
5. `Draw` - 6 edges
6. `trigger_analysis()` - 5 edges
7. `trigger_scrape()` - 5 edges
8. `FrequencyAnalysisTool` - 5 edges
9. `PatternAnalysisTool` - 5 edges
10. `scripts` - 5 edges

## Surprising Connections (you probably didn't know these)
- `trigger_scrape()` --calls--> `UK49ScraperTool`  [INFERRED]
  backend/app/routers/scrape.py → backend/crew/tools/scraper_tool.py
- `trigger_scrape()` --calls--> `ScrapeResponse`  [EXTRACTED]
  backend/app/routers/scrape.py → backend/app/models.py
- `trigger_analysis()` --calls--> `run_analysis()`  [EXTRACTED]
  backend/app/routers/predictions.py → backend/crew/crew.py
- `Props` --references--> `Draw`  [EXTRACTED]
  frontend/src/components/DrawTable.tsx → frontend/src/lib/api.ts
- `startup()` --calls--> `init_db()`  [EXTRACTED]
  backend/app/main.py → backend/app/database.py

## Import Cycles
- None detected.

## Communities (22 total, 7 thin omitted)

### Community 0 - "Frontend Package Config"
Cohesion: 0.09
Nodes (21): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, tailwindcss (+13 more)

### Community 1 - "Frontend UI Pages"
Cohesion: 0.19
Nodes (10): Props, TYPE_BADGES, TYPE_LABELS, Draw, fetchDraws(), PredictionTier, runAnalysis(), triggerScrape() (+2 more)

### Community 2 - "Backend Database"
Cohesion: 0.18
Nodes (14): clear_prediction_cache(), get_cached_prediction(), get_connection(), get_draws(), get_draws_by_type_count(), get_draws_count(), get_latest_draw_date(), init_db() (+6 more)

### Community 3 - "Frontend TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 4 - "Backend Analysis Tools"
Cohesion: 0.18
Nodes (4): BaseTool, FrequencyAnalysisTool, PatternAnalysisTool, PredictionTool

### Community 5 - "Frontend UI Components"
Cohesion: 0.21
Nodes (8): Props, NumberBall(), Props, Props, PredictionPick, BONUS_COLOR, getNumberColor(), RANGE_COLORS

### Community 6 - "Gemini LLM Wrapper"
Cohesion: 0.23
Nodes (7): Any, BaseChatModel, BaseMessage, CallbackManagerForLLMRun, ChatResult, _convert_message(), GeminiChat

### Community 7 - "CrewAI Agent Pipeline"
Cohesion: 0.25
Nodes (7): Config, Settings, BaseSettings, get_llm(), run_analysis(), make_tasks(), Task

### Community 9 - "Backend API Models"
Cohesion: 0.48
Nodes (6): DrawResponse, PredictionPick, PredictionResponse, PredictionTier, ScrapeResponse, BaseModel

## Knowledge Gaps
- **49 isolated node(s):** `Config`, `eslintConfig`, `nextConfig`, `name`, `version` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `Backend Database` to `Backend Analysis Tools`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `UK49ScraperTool` connect `Scraper Tool` to `Backend Database`, `Backend Analysis Tools`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `Config`, `eslintConfig`, `nextConfig` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Package Config` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `Frontend TypeScript Config` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._