# UK49 Lotto Predictor — Design Spec

> **Goal:** A Next.js + FastAPI + CrewAI app that scrapes UK49 results, analyzes patterns, and generates probability-ranked predictions at every tier (2+bonus through 6+bonus).

## Architecture

```
Next.js (Frontend)  ◄── REST/JSON ──►  FastAPI (Backend)
                                           │
                                     CrewAI Agents:
                                     1. Data Collector (ScraperTool)
                                     2. Data Analyst (frequency, hot/cold)
                                     3. Pattern Researcher (deltas, pairs, sequences)
                                     4. Predictor (tiered picks)
                                           │
                                     SQLite DB
```

### Frontend (Next.js App Router)
- Dashboard page: last 50 results, today's predictions, hot/cold balls
- Predictions page: tiered picks sorted by probability
- Analysis page: charts (frequency, positional heatmap, delta distribution)

### Backend (Python FastAPI)
- `GET /api/draws` — paginated draw history
- `POST /api/scrape` — trigger incremental scrape
- `GET /api/predictions` — latest predictions
- `POST /api/analyze` — run full CrewAI analysis

### CrewAI Agents
1. **Data Collector** — Uses `ScraperTool` (httpx + bs4) to fetch results incrementally
2. **Data Analyst** — Computes frequency, hot/cold, odd/even, sum ranges
3. **Pattern Researcher** — Delta analysis, sequential pairs, positional frequency, overdue detection
4. **Predictor** — Synthesizes all signals → tiered picks

### Data Model
```sql
CREATE TABLE draws (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  draw_date TEXT NOT NULL,
  draw_type TEXT NOT NULL,  -- brunchtime|lunchtime|drivetime|teatime
  n1, n2, n3, n4, n5, n6 INTEGER NOT NULL,
  bonus INTEGER NOT NULL,
  UNIQUE(draw_date, draw_type)
);
```

### Predictions Output
```json
{
  "generated_at": "2026-06-04T12:00:00Z",
  "tiers": [
    { "tier": "2+bonus", "picks": [
        { "numbers": [12, 38], "bonus": 7, "probability": 0.042 }
      ]
    },
    { "tier": "3+bonus", "picks": [...] },
    { "tier": "4+bonus", "picks": [...] },
    { "tier": "5+bonus", "picks": [...] },
    { "tier": "6+bonus", "picks": [...] }
  ],
  "analysis": {
    "hot_numbers": [38, 44, 12],
    "cold_numbers": [2, 31, 41],
    "key_insights": "..."
  }
}
```

### LLM
- **Provider:** Groq (via `groq/llama-3.3-70b-versatile`)
- **API key:** `GROQ_API_KEY` environment variable

### Data Source
- Scrape from `lotteryextreme.com` (clean HTML tables, all 4 draws, historical back to 1996)
- Initial: Jan 1 2026 → today (scrape once)
- Incremental: scrape latest draw after each result
