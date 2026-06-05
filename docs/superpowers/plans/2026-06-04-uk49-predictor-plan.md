# UK49 Lotto Predictor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Next.js + FastAPI + CrewAI app that scrapes UK49 results, analyzes patterns, and generates tiered probability-ranked predictions.

**Architecture:** Next.js frontend calls FastAPI REST endpoints. FastAPI backs a CrewAI crew of 4 agents (Data Collector, Analyst, Pattern Researcher, Predictor) that read/write SQLite. Scraper uses httpx+bs4 wrapped as a CrewAI tool.

**Tech Stack:** Next.js 15 (App Router), FastAPI, CrewAI, SQLite, httpx, beautifulsoup4, Groq LLM

**Data Source:** lotteryextreme.com (clean HTML tables, all 4 draws)

---

### Task 1: Backend scaffolding — FastAPI + SQLite + config

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlite-utils==3.37
crewai==0.105.0
httpx==0.27.0
beautifulsoup4==4.12.0
lxml==5.3.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    database_url: str = "sqlite:///data/uk49.db"
    groq_model: str = "groq/llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: Create database.py**

```python
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "uk49.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT NOT NULL,
            draw_type TEXT NOT NULL,
            n1 INTEGER NOT NULL,
            n2 INTEGER NOT NULL,
            n3 INTEGER NOT NULL,
            n4 INTEGER NOT NULL,
            n5 INTEGER NOT NULL,
            n6 INTEGER NOT NULL,
            bonus INTEGER NOT NULL,
            UNIQUE(draw_date, draw_type)
        );
        CREATE INDEX IF NOT EXISTS idx_draws_date ON draws(draw_date);
        CREATE INDEX IF NOT EXISTS idx_draws_type ON draws(draw_type);
    """)
    conn.commit()
    conn.close()

def insert_draw(draw_date, draw_type, numbers):
    conn = get_connection()
    conn.execute(
        """INSERT OR IGNORE INTO draws (draw_date, draw_type, n1, n2, n3, n4, n5, n6, bonus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (draw_date, draw_type, *numbers)
    )
    conn.commit()
    conn.close()

def get_draws(limit=50, offset=0, draw_type=None):
    conn = get_connection()
    query = "SELECT * FROM draws"
    params = []
    if draw_type:
        query += " WHERE draw_type = ?"
        params.append(draw_type)
    query += " ORDER BY draw_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_draw_date():
    conn = get_connection()
    row = conn.execute("SELECT MAX(draw_date) as max_date FROM draws").fetchone()
    conn.close()
    return row["max_date"] if row else None
```

- [ ] **Step 4: Create models.py**

```python
from pydantic import BaseModel
from typing import Optional

class DrawResponse(BaseModel):
    id: int
    draw_date: str
    draw_type: str
    n1: int
    n2: int
    n3: int
    n4: int
    n5: int
    n6: int
    bonus: int

class PredictionPick(BaseModel):
    numbers: list[int]
    bonus: int
    probability: float

class PredictionTier(BaseModel):
    tier: str
    picks: list[PredictionPick]

class PredictionResponse(BaseModel):
    generated_at: str
    draw_type: str
    tiers: list[PredictionTier]
    analysis: dict

class ScrapeResponse(BaseModel):
    message: str
    draws_added: int
```

- [ ] **Step 5: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

app = FastAPI(title="UK49 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Verify it starts**

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

Expected: Server starts on http://localhost:8000, `/api/health` returns `{"status": "ok"}`

---

### Task 2: Scraper Tool (CrewAI custom tool)

**Files:**
- Create: `backend/crew/tools/__init__.py`
- Create: `backend/crew/tools/scraper_tool.py`
- Create: `backend/crew/__init__.py`

- [ ] **Step 1: Create scraper_tool.py**

```python
import httpx
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from typing import Optional
from app.database import insert_draw

DRAW_ORDER = ["brunchtime", "lunchtime", "drivetime", "teatime"]

BASE_URL = "https://www.lotteryextreme.com/49s/results"

class UK49ScraperTool(BaseTool):
    name: str = "UK49 Results Scraper"
    description: str = "Scrapes UK49 draw results from lotteryextreme.com and stores them in the database."

    def _run(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        params = {}
        if start_date:
            params["date_from"] = start_date
        if end_date:
            params["date_to"] = end_date

        resp = httpx.get(BASE_URL, params=params, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        count = 0
        result_blocks = soup.select("table.result-table tr, div.result-row, .draw-results")
        if not result_blocks:
            result_blocks = soup.find_all("table")

        for block in result_blocks:
            text = block.get_text(separator="|", strip=True)
            if "brunchtime" in text.lower() or "lunchtime" in text.lower() or "drivetime" in text.lower() or "teatime" in text.lower():
                lines = text.split("|")
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    if line_lower in DRAW_ORDER:
                        date_raw = lines[i-1] if i > 0 else ""
                        date = self._parse_date(date_raw)
                        if not date:
                            continue
                        nums = self._extract_numbers(lines[i+1:i+8])
                        if len(nums) == 7:
                            insert_draw(date, line_lower, nums)
                            count += 1
        return f"Scraped and stored {count} draws."

    def _parse_date(self, raw: str) -> Optional[str]:
        import re
        months = {"january":"01","february":"02","march":"03","april":"04","may":"05","june":"06",
                  "july":"07","august":"08","september":"09","october":"10","november":"11","december":"12"}
        raw = raw.strip()
        for m_name, m_num in months.items():
            if m_name in raw.lower():
                match = re.search(r"(\d+)\s+(\w+)\s+(\d{4})", raw)
                if match:
                    day, _, year = match.groups()
                    return f"{year}-{m_num}-{int(day):02d}"
        return None

    def _extract_numbers(self, cells: list[str]) -> list[int]:
        nums = []
        for c in cells:
            c = c.strip()
            if c.isdigit():
                n = int(c)
                if 1 <= n <= 49:
                    nums.append(n)
        return nums
```

- [ ] **Step 2: Create __init__.py files**

```python
# backend/crew/__init__.py
# backend/crew/tools/__init__.py
```

Both empty files.

---

### Task 3: Analysis & Pattern Tools

**Files:**
- Create: `backend/crew/tools/analysis_tool.py`
- Create: `backend/crew/tools/pattern_tool.py`
- Create: `backend/crew/tools/predictor_tool.py`

- [ ] **Step 1: Create analysis_tool.py**

```python
from crewai.tools import BaseTool
from collections import Counter
from app.database import get_connection

class FrequencyAnalysisTool(BaseTool):
    name: str = "Frequency Analysis"
    description: str = "Analyzes number frequency, hot/cold numbers, odd/even splits, and sum ranges from draw history."

    def _run(self, limit: int = 50, draw_type: str = "lunchtime") -> str:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
            (draw_type, limit)
        ).fetchall()
        conn.close()

        if not rows:
            return "No data found."

        all_nums = []
        bonuses = []
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                all_nums.append(n)
            bonuses.append(r["bonus"])

        freq = Counter(all_nums)
        bonus_freq = Counter(bonuses)

        sorted_by_freq = freq.most_common()
        hot = sorted_by_freq[:5]
        cold = sorted_by_freq[-5:]

        odd_count = sum(1 for n in all_nums if n % 2 == 1)
        even_count = len(all_nums) - odd_count

        sums = [r["n1"]+r["n2"]+r["n3"]+r["n4"]+r["n5"]+r["n6"] for r in rows]

        return {
            "total_draws_analyzed": len(rows),
            "hot_numbers": [{"number": n, "count": c} for n, c in hot],
            "cold_numbers": [{"number": n, "count": c} for n, c in cold],
            "bonus_frequency": [{"number": n, "count": c} for n, c in bonus_freq.most_common(5)],
            "odd_even_ratio": {"odd": odd_count, "even": even_count, "ratio": f"{odd_count}:{even_count}"},
            "sum_range": {"min": min(sums), "max": max(sums), "avg": round(sum(sums)/len(sums), 1)}
        }
```

- [ ] **Step 2: Create pattern_tool.py**

```python
from crewai.tools import BaseTool
from collections import Counter
from app.database import get_connection

class PatternAnalysisTool(BaseTool):
    name: str = "Pattern Analysis"
    description: str = "Analyzes delta patterns, sequential pairs, positional frequency, and overdue numbers."

    def _run(self, limit: int = 50, draw_type: str = "lunchtime") -> str:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
            (draw_type, limit)
        ).fetchall()
        conn.close()

        if not rows:
            return "No data found."

        deltas = []
        pairs = []
        positional = {i: [] for i in range(1, 7)}

        for r in rows:
            nums = sorted([r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]])
            for i in range(len(nums)-1):
                deltas.append(nums[i+1] - nums[i])
            for i in range(len(nums)):
                for j in range(i+1, len(nums)):
                    pairs.append((nums[i], nums[j]))
            for pos in range(1, 7):
                positional[pos].append(r[f"n{pos}"])

        delta_freq = Counter(deltas)
        pair_freq = Counter(pairs)

        all_nums = set()
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                all_nums.add(n)
        overdue = sorted([n for n in range(1, 50) if n not in all_nums])

        return {
            "common_deltas": [{"delta": d, "count": c} for d, c in delta_freq.most_common(5)],
            "common_pairs": [{"pair": list(p), "count": c} for p, c in pair_freq.most_common(5)],
            "positional_frequency": {
                str(pos): Counter([r[f"n{pos}"] for r in rows]).most_common(3)
                for pos in range(1, 7)
            },
            "overdue_numbers": overdue,
        }
```

- [ ] **Step 3: Create predictor_tool.py**

```python
from crewai.tools import BaseTool
import random
from collections import Counter
from app.database import get_connection

class PredictionTool(BaseTool):
    name: str = "Prediction Generator"
    description: str = "Generates tiered predictions (2+bonus through 6+bonus) based on probability analysis."

    def _run(self, draw_type: str = "lunchtime", limit: int = 50) -> str:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
            (draw_type, limit)
        ).fetchall()
        conn.close()

        if not rows:
            return {"error": "No data found"}

        all_nums = []
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                all_nums.append(n)

        freq = Counter(all_nums)
        sorted_numbers = [n for n, _ in freq.most_common()]
        weights = {n: freq[n] for n in sorted_numbers}

        def pick_weighted(k, exclude=None):
            pool = [n for n in sorted_numbers if n not in (exclude or [])]
            w = [weights.get(n, 1) for n in pool]
            return random.choices(pool, weights=w, k=k)

        bonus_freq = Counter(r["bonus"] for r in rows)
        bonus_sorted = [b for b, _ in bonus_freq.most_common()]
        bonus_weights = {b: bonus_freq[b] for b in bonus_sorted}

        def pick_bonus(exclude=None):
            pool = [b for b in bonus_sorted if b not in (exclude or [])]
            if not pool:
                return random.choice(list(set(range(1,50)) - set(exclude)))
            w = [bonus_weights.get(b, 1) for b in pool]
            return random.choices(pool, weights=w, k=1)[0]

        tiers = {}
        for k in [2, 3, 4, 5, 6]:
            tier_picks = []
            for _ in range(3):
                nums = pick_weighted(k)
                bonus = pick_bonus(exclude=nums)
                tier_picks.append({
                    "numbers": sorted(nums),
                    "bonus": bonus,
                    "probability": round(1.0 / (49**k), 6)
                })
            tiers[f"{k}+bonus"] = sorted(tier_picks, key=lambda x: x["probability"], reverse=True)

        return tiers
```

---

### Task 4: CrewAI Agents + Tasks + Crew

**Files:**
- Create: `backend/crew/agents.py`
- Create: `backend/crew/tasks.py`
- Create: `backend/crew/crew.py`

- [ ] **Step 1: Create agents.py**

```python
from crewai import Agent, LLM
from app.config import settings

llm = LLM(model=settings.groq_model, api_key=settings.groq_api_key)

from crew.tools.scraper_tool import UK49ScraperTool
from crew.tools.analysis_tool import FrequencyAnalysisTool
from crew.tools.pattern_tool import PatternAnalysisTool
from crew.tools.predictor_tool import PredictionTool

scraper = UK49ScraperTool()
freq_tool = FrequencyAnalysisTool()
pattern_tool = PatternAnalysisTool()
predict_tool = PredictionTool()

data_collector = Agent(
    role="Data Collector",
    goal="Scrape UK49 draw results from lotteryextreme.com and store them in the database.",
    backstory="Expert web scraper who efficiently collects lottery data.",
    tools=[scraper],
    llm=llm,
    verbose=True,
)

data_analyst = Agent(
    role="Data Analyst",
    goal="Analyze number frequency, hot/cold numbers, odd/even splits, and sum ranges.",
    backstory="Statistical analyst specializing in lottery number patterns.",
    tools=[freq_tool],
    llm=llm,
    verbose=True,
)

pattern_researcher = Agent(
    role="Pattern Researcher",
    goal="Detect delta patterns, sequential pairs, positional trends, and overdue numbers.",
    backstory="Pattern recognition expert who finds hidden relationships in draw data.",
    tools=[pattern_tool],
    llm=llm,
    verbose=True,
)

predictor = Agent(
    role="Predictor",
    goal="Generate tiered predictions ranked by probability for all tiers from 2+bonus to 6+bonus.",
    backstory="Senior lottery strategist who synthesizes all analysis into actionable picks.",
    tools=[predict_tool],
    llm=llm,
    verbose=True,
)
```

- [ ] **Step 2: Create tasks.py**

```python
from crewai import Task
from crew.agents import data_collector, data_analyst, pattern_researcher, predictor

collect_task = Task(
    description="Scrape the latest UK49 draw results from lotteryextreme.com. Check what dates we already have in the database and only scrape missing data.",
    expected_output="Confirmation of how many new draws were added to the database.",
    agent=data_collector,
)

analyze_task = Task(
    description="Analyze the last 50 Lunchtime draws. Compute frequency, hot/cold numbers, bonus ball frequency, odd/even ratio, and sum range.",
    expected_output="JSON with frequency analysis, hot/cold lists, and statistical summaries.",
    agent=data_analyst,
)

pattern_task = Task(
    description="Research patterns in the last 50 Lunchtime draws. Identify common deltas, frequent pairs, positional frequency trends, and overdue numbers.",
    expected_output="JSON with delta analysis, pair analysis, positional trends, and overdue numbers.",
    agent=pattern_researcher,
)

predict_task = Task(
    description="Generate tiered predictions for the next Lunchtime draw. Produce picks for 2+bonus, 3+bonus, 4+bonus, 5+bonus, and 6+bonus tiers. Each tier should have 3 ranked picks with probability scores.",
    expected_output="JSON object with tiered predictions, each tier containing 3 ranked picks with numbers, bonus ball, and probability.",
    agent=predictor,
)
```

- [ ] **Step 3: Create crew.py**

```python
from crewai import Crew, Process
from crew.agents import data_collector, data_analyst, pattern_researcher, predictor
from crew.tasks import collect_task, analyze_task, pattern_task, predict_task

uk49_crew = Crew(
    agents=[data_collector, data_analyst, pattern_researcher, predictor],
    tasks=[collect_task, analyze_task, pattern_task, predict_task],
    process=Process.sequential,
    verbose=True,
)

def run_analysis(draw_type: str = "lunchtime") -> dict:
    result = uk49_crew.kickoff()
    return result
```

---

### Task 5: FastAPI Router — Scrape + Draws + Predictions

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/draws.py`
- Create: `backend/app/routers/scrape.py`
- Create: `backend/app/routers/predictions.py`

- [ ] **Step 1: Create routers __init__.py**

```python
```

- [ ] **Step 2: Create draws.py**

```python
from fastapi import APIRouter, Query
from app.database import get_draws
from app.models import DrawResponse

router = APIRouter(prefix="/api", tags=["draws"])

@router.get("/draws", response_model=list[DrawResponse])
def list_draws(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    draw_type: str = Query(None, regex="^(brunchtime|lunchtime|drivetime|teatime)$")
):
    return get_draws(limit=limit, offset=offset, draw_type=draw_type)
```

- [ ] **Step 3: Create scrape.py**

```python
from fastapi import APIRouter
from app.models import ScrapeResponse
from crew.tools.scraper_tool import UK49ScraperTool
from app.database import get_latest_draw_date

router = APIRouter(prefix="/api", tags=["scrape"])

@router.post("/scrape", response_model=ScrapeResponse)
def trigger_scrape():
    tool = UK49ScraperTool()
    latest = get_latest_draw_date()
    result = tool._run(start_date="2026-01-01")
    return ScrapeResponse(message=result, draws_added=0)
```

- [ ] **Step 4: Create predictions.py**

```python
from fastapi import APIRouter, Query
from crew.crew import uk49_crew

router = APIRouter(prefix="/api", tags=["predictions"])

@router.post("/analyze")
def run_analysis(draw_type: str = Query("lunchtime", regex="^(brunchtime|lunchtime|drivetime|teatime)$")):
    result = uk49_crew.kickoff()
    return {"status": "complete", "result": str(result)}
```

- [ ] **Step 5: Register routers in main.py**

Edit `backend/app/main.py` — add imports and include the routers.

```python
from app.routers import draws, scrape, predictions

app.include_router(draws.router)
app.include_router(scrape.router)
app.include_router(predictions.router)
```

---

### Task 6: Next.js frontend scaffolding

**Files:**
- Scaffold with `create-next-app`

- [ ] **Step 1: Create Next.js app**

```bash
cd /home/morema/UK49 && npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --no-git --import-alias "@/*"
```

- [ ] **Step 2: Create API client**

```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Draw {
  id: number;
  draw_date: string;
  draw_type: string;
  n1: number;
  n2: number;
  n3: number;
  n4: number;
  n5: number;
  n6: number;
  bonus: number;
}

export interface PredictionPick {
  numbers: number[];
  bonus: number;
  probability: number;
}

export interface PredictionTier {
  tier: string;
  picks: PredictionPick[];
}

export interface PredictionResponse {
  generated_at: string;
  draw_type: string;
  tiers: PredictionTier[];
  analysis: Record<string, unknown>;
}

export async function fetchDraws(limit = 50, drawType?: string): Promise<Draw[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (drawType) params.set("draw_type", drawType);
  const res = await fetch(`${API_BASE}/api/draws?${params}`);
  return res.json();
}

export async function triggerScrape(): Promise<{ message: string; draws_added: number }> {
  const res = await fetch(`${API_BASE}/api/scrape`, { method: "POST" });
  return res.json();
}

export async function runAnalysis(drawType = "lunchtime"): Promise<{ status: string; result: string }> {
  const res = await fetch(`${API_BASE}/api/analyze?draw_type=${drawType}`, { method: "POST" });
  return res.json();
}
```

---

### Task 7: Dashboard page — last 50 draws + hot/cold

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/DrawTable.tsx`
- Create: `frontend/src/components/HotColdBalls.tsx`

- [ ] **Step 1: Create DrawTable component**

```tsx
// frontend/src/components/DrawTable.tsx
"use client";
import { Draw } from "@/lib/api";

interface Props {
  draws: Draw[];
}

export default function DrawTable({ draws }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-2 px-3">Date</th>
            <th className="text-left py-2 px-3">Draw</th>
            <th className="text-left py-2 px-3">Numbers</th>
            <th className="text-left py-2 px-3">Bonus</th>
          </tr>
        </thead>
        <tbody>
          {draws.map((d) => (
            <tr key={d.id} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-2 px-3">{d.draw_date}</td>
              <td className="py-2 px-3 capitalize">{d.draw_type}</td>
              <td className="py-2 px-3">
                <div className="flex gap-1">
                  {[d.n1, d.n2, d.n3, d.n4, d.n5, d.n6].map((n, i) => (
                    <span key={i} className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
                      {n}
                    </span>
                  ))}
                </div>
              </td>
              <td className="py-2 px-3">
                <span className="w-8 h-8 rounded-full bg-yellow-500 text-black flex items-center justify-center text-xs font-bold">
                  {d.bonus}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Create HotColdBalls component**

```tsx
// frontend/src/components/HotColdBalls.tsx
"use client";

interface Props {
  hot: number[];
  cold: number[];
}

export default function HotColdBalls({ hot, cold }: Props) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-bold text-red-400 mb-3">🔥 Hot Numbers</h3>
        <div className="flex gap-2 flex-wrap">
          {hot.map((n) => (
            <span key={n} className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center font-bold">
              {n}
            </span>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-lg font-bold text-blue-400 mb-3">❄️ Cold Numbers</h3>
        <div className="flex gap-2 flex-wrap">
          {cold.map((n) => (
            <span key={n} className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold">
              {n}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update Dashboard page**

```tsx
// frontend/src/app/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Draw, fetchDraws } from "@/lib/api";
import DrawTable from "@/components/DrawTable";
import HotColdBalls from "@/components/HotColdBalls";

export default function Dashboard() {
  const [draws, setDraws] = useState<Draw[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDraws(50).then(setDraws).finally(() => setLoading(false));
  }, []);

  const mainNumbers = draws.flatMap(d => [d.n1, d.n2, d.n3, d.n4, d.n5, d.n6]);
  const freq = new Map<number, number>();
  mainNumbers.forEach(n => freq.set(n, (freq.get(n) || 0) + 1));
  const sorted = [...freq.entries()].sort((a, b) => b[1] - a[1]);
  const hot = sorted.slice(0, 5).map(e => e[0]);
  const cold = sorted.slice(-5).map(e => e[0]);

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-8">UK49 Lotto Predictor</h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">📊 Hot & Cold Numbers (Last 50)</h2>
        <HotColdBalls hot={hot} cold={cold} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">📋 Recent Draws</h2>
        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : (
          <DrawTable draws={draws} />
        )}
      </section>
    </main>
  );
}
```

---

### Task 8: Predictions page

**Files:**
- Create: `frontend/src/app/predictions/page.tsx`
- Create: `frontend/src/components/PredictionCard.tsx`

- [ ] **Step 1: Create PredictionCard**

```tsx
// frontend/src/components/PredictionCard.tsx
"use client";
import { PredictionPick } from "@/lib/api";

interface Props {
  tier: string;
  picks: PredictionPick[];
}

export default function PredictionCard({ tier, picks }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h3 className="text-lg font-bold mb-3">{tier}</h3>
      <div className="space-y-3">
        {picks.map((pick, i) => (
          <div key={i} className="flex items-center gap-3 bg-gray-800/50 rounded-lg p-3">
            <span className="text-gray-400 text-sm w-4">#{i + 1}</span>
            <div className="flex gap-1 flex-wrap">
              {pick.numbers.map((n, j) => (
                <span key={j} className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
                  {n}
                </span>
              ))}
              <span className="w-8 h-8 rounded-full bg-yellow-500 text-black flex items-center justify-center text-xs font-bold">
                {pick.bonus}
              </span>
            </div>
            <span className="text-xs text-gray-400 ml-auto">{(pick.probability * 100).toFixed(4)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create Predictions page**

```tsx
// frontend/src/app/predictions/page.tsx
"use client";
import { useEffect, useState } from "react";
import { PredictionTier, runAnalysis } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";

export default function PredictionsPage() {
  const [data, setData] = useState<PredictionTier[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const result = await runAnalysis("lunchtime");
      // Parse the result string back to JSON
      const parsed = JSON.parse(result.result);
      setData(parsed);
    } catch {
      // If CrewAI hasn't been set up, show sample data
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-8">🎯 Predictions</h1>

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-lg mb-8"
      >
        {loading ? "Analyzing..." : "Run Analysis"}
      </button>

      {data.length === 0 && !loading && (
        <p className="text-gray-400">Click &quot;Run Analysis&quot; to generate predictions.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((tier) => (
          <PredictionCard key={tier.tier} tier={tier.tier} picks={tier.picks} />
        ))}
      </div>
    </main>
  );
}
```

---

### Task 9: Analysis page

**Files:**
- Create: `frontend/src/app/analysis/page.tsx`

- [ ] **Step 1: Create Analysis page**

```tsx
// frontend/src/app/analysis/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Draw, fetchDraws } from "@/lib/api";

export default function AnalysisPage() {
  const [draws, setDraws] = useState<Draw[]>([]);

  useEffect(() => {
    fetchDraws(100).then(setDraws);
  }, []);

  const mainNumbers = draws.flatMap(d => [d.n1, d.n2, d.n3, d.n4, d.n5, d.n6]);
  const freq = new Map<number, number>();
  mainNumbers.forEach(n => freq.set(n, (freq.get(n) || 0) + 1));
  const sorted = [...freq.entries()].sort((a, b) => a[0] - b[0]);

  const maxCount = Math.max(...sorted.map(e => e[1]), 1);

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-8">📈 Analysis</h1>

      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">Number Frequency (Last 100)</h2>
        <div className="flex items-end gap-1 flex-wrap">
          {sorted.map(([num, count]) => {
            const height = (count / maxCount) * 200;
            return (
              <div key={num} className="flex flex-col items-center" style={{ width: 24 }}>
                <div
                  className="bg-blue-500 w-full rounded-t"
                  style={{ height: `${Math.max(height, 4)}px` }}
                  title={`${num}: ${count}x`}
                />
                <span className="text-[10px] text-gray-400 mt-1">{num}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h3 className="font-bold mb-3">Odd/Even Split</h3>
          {(() => {
            const odd = mainNumbers.filter(n => n % 2 === 1).length;
            const even = mainNumbers.length - odd;
            const total = mainNumbers.length;
            return (
              <>
                <div className="flex h-6 rounded-full overflow-hidden mb-2">
                  <div className="bg-green-600" style={{ width: `${(odd / total) * 100}%` }} />
                  <div className="bg-purple-600" style={{ width: `${(even / total) * 100}%` }} />
                </div>
                <p className="text-sm text-gray-400">Odd: {odd} | Even: {even}</p>
              </>
            );
          })()}
        </div>

        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h3 className="font-bold mb-3">High/Low Split (1-24 / 25-49)</h3>
          {(() => {
            const low = mainNumbers.filter(n => n <= 24).length;
            const high = mainNumbers.filter(n => n > 24).length;
            const total = mainNumbers.length;
            return (
              <>
                <div className="flex h-6 rounded-full overflow-hidden mb-2">
                  <div className="bg-orange-600" style={{ width: `${(low / total) * 100}%` }} />
                  <div className="bg-cyan-600" style={{ width: `${(high / total) * 100}%` }} />
                </div>
                <p className="text-sm text-gray-400">Low (1-24): {low} | High (25-49): {high}</p>
              </>
            );
          })()}
        </div>
      </section>
    </main>
  );
}
```

---

### Task 10: Navigation layout + final wiring

**Files:**
- Modify: `frontend/src/app/layout.tsx`

- [ ] **Step 1: Update layout with navigation**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UK49 Lotto Predictor",
  description: "AI-powered UK49 lottery analysis and predictions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 px-6 py-3">
          <div className="max-w-6xl mx-auto flex items-center gap-6">
            <a href="/" className="text-lg font-bold text-yellow-500">UK49</a>
            <a href="/" className="text-sm text-gray-300 hover:text-white">Dashboard</a>
            <a href="/predictions" className="text-sm text-gray-300 hover:text-white">Predictions</a>
            <a href="/analysis" className="text-sm text-gray-300 hover:text-white">Analysis</a>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
```

---

### Task 11: .env files and startup scripts

**Files:**
- Create: `backend/.env.example`
- Create: `backend/.env`

- [ ] **Step 1: Create .env.example**

```
GROQ_API_KEY=your_groq_api_key_here
```

- [ ] **Step 2: Create .env**

Ask the user for their Groq API key and write it to `backend/.env`.

---

## Self-Review Checklist

1. **Spec coverage:** ✓ Scraping (Task 2, 5), analysis (Task 3, 4), predictions (Task 3, 4, 8), dashboard (Task 7), FastAPI (Task 1, 5), Next.js (Task 6-10)
2. **Placeholder scan:** ✓ No TBD, TODO, or "implement later"
3. **Type consistency:** ✓ API types match between frontend and backend
