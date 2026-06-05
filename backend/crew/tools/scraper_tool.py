import os
import httpx
from bs4 import BeautifulSoup
from langchain.tools import BaseTool
from typing import Optional
from datetime import datetime
from app.database import insert_draw, get_latest_draw_date

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional dependency in some environments
    sync_playwright = None

BASE_URL = "https://www.lotteryextreme.com/49s/results"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12"
}


class UK49ScraperTool(BaseTool):
    name: str = "UK49 Results Scraper"
    description: str = "Scrapes UK49 draw results from lotteryextreme.com month by month and stores them in the database."

    def _run(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        now = datetime.now()
        end_month = now.month
        end_year = now.year

        if end_date:
            parts = end_date.split("-")
            end_year = int(parts[0])
            end_month = int(parts[1])

        start_month = 1
        start_year = 2026

        if start_date:
            parts = start_date.split("-")
            start_year = int(parts[0])
            start_month = int(parts[1])

        total_count = 0

        year = start_year
        month = start_month
        while (year < end_year) or (year == end_year and month <= end_month):
            count = self._scrape_month(month, year)
            total_count += count
            month += 1
            if month > 12:
                month = 1
                year += 1

        if total_count == 0:
            return "Database already contains the available 2026-01-01 through current history. No new draws were added."
        return f"Scraped and stored {total_count} draws from 2026-01-01 through the current month."

    def _scrape_month(self, month: int, year: int) -> int:
        try:
            return self._scrape_month_with_playwright(month, year)
        except Exception:
            return self._scrape_month_with_httpx(month, year)

    def _scrape_month_with_playwright(self, month: int, year: int) -> int:
        if sync_playwright is None:
            raise RuntimeError("playwright is not available")

        executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/usr/bin/google-chrome")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=executable_path)
            try:
                page = browser.new_page(user_agent=HEADERS["User-Agent"])
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120000)
                page.select_option("#month", str(month))
                page.select_option("#year", str(year))
                for checkbox in ("time[B]", "time[L]", "time[D]", "time[T]"):
                    page.locator(f'input[name="{checkbox}"]').check()
                page.locator("#sb2").click()
                page.wait_for_load_state("networkidle", timeout=120000)
                html = page.content()
            finally:
                browser.close()

        return self._parse_html_results(html)

    def _scrape_month_with_httpx(self, month: int, year: int) -> int:
        data = self._build_form_data(month, year)

        resp = httpx.post(BASE_URL, data=data, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return self._parse_html_results(resp.text)

    def _parse_html_results(self, html: str) -> int:
        soup = BeautifulSoup(html, "lxml")

        count = 0
        xgame_cells = soup.find_all("td", class_="xgame")

        for cell in xgame_cells:
            text = cell.get_text(strip=True)

            draw_type = None
            for dt in ["brunchtime", "lunchtime", "drivetime", "teatime"]:
                if dt in text.lower():
                    draw_type = dt
                    break
            if not draw_type:
                continue

            if "yesterday" in text.lower() or "today" in text.lower():
                continue

            date_str = self._extract_date(text)
            if not date_str:
                continue

            next_row = cell.parent.find_next_sibling("tr")
            if not next_row:
                continue
            ul = next_row.find("ul", class_="displayball")
            if not ul:
                continue

            numbers = []
            for li in ul.find_all("li"):
                if "dbx" in li.get("class", []):
                    continue
                txt = li.get_text(strip=True)
                if txt.isdigit():
                    n = int(txt)
                    if 1 <= n <= 49:
                        numbers.append(n)

            if len(numbers) == 7:
                insert_draw(date_str, draw_type, numbers)
                count += 1

        return count

    def _build_form_data(self, month: int, year: int) -> dict[str, str]:
        return {
            "tryb": "rokmsc",
            "_month": str(month),
            "_year": str(year),
            "time[B]": "1",
            "time[L]": "1",
            "time[D]": "1",
            "time[T]": "1",
        }

    def _extract_date(self, text: str) -> Optional[str]:
        import re
        text_lower = text.lower()
        for m_name in MONTHS:
            if m_name in text_lower:
                match = re.search(r"(\d+)\s+(\w+)\s+(\d{4})", text)
                if match:
                    day, _, year = match.groups()
                    return f"{year}-{MONTHS[m_name]}-{int(day):02d}"
        return None
