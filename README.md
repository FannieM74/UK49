# UK49 Predictor

A lightweight lottery‑draw prediction service built with:

- **FastAPI** (Python) for the backend API
- **SQLite** for simple persistence of historic draws
- **LangChain‑style "crew" agents** that can scrape new draw data, run statistical analysis and generate AI‑driven predictions
- **Next.js 13 (App Router)** with TypeScript, Tailwind CSS and shadcn UI components for a modern responsive frontend

The project provides two main UI sections:

1. **Draw History** – Browse recent draws with pagination and optional draw‑type filtering.
2. **Predictions** – Generate tiered predictions for the next draw using the built‑in prediction agent.

All API endpoints are documented automatically by FastAPI (`/docs`).
