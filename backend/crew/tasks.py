from crewai import Task
from crew.agents import data_collector, data_analyst, pattern_researcher, predictor

def make_tasks(draw_type: str) -> list[Task]:
    return [
        Task(
            description="""Scrape the latest UK49 draw results from lotteryextreme.com. 
First check the database to see what dates we already have. Then scrape only missing data starting from 2026-01-01.
Use the UK49 Results Scraper tool to fetch and store the results.""",
            expected_output="Confirmation of how many new draws were scraped and stored in the database.",
            agent=data_collector,
        ),
        Task(
            description=f"""Analyze the last 50 {draw_type} draws in the database. 
Use the Frequency Analysis tool to compute:
- Number frequency (how often each number 1-49 appears)
- Hot numbers (most frequent)
- Cold numbers (least frequent)
- Bonus ball frequency
- Odd/even ratio
- Sum range of the 6 main numbers

Provide a clear summary of the statistical findings.""",
            expected_output="JSON with frequency analysis, hot/cold lists, and statistical summaries for the last 50 draws.",
            agent=data_analyst,
        ),
        Task(
            description=f"""Research patterns in the last 50 {draw_type} draws.
Use the Pattern Analysis tool to identify:
- Common delta patterns (differences between consecutive sorted numbers)
- Frequent number pairs that appear together
- Overdue numbers (haven't appeared recently)

Interpret what these patterns suggest for future draws.""",
            expected_output="JSON with delta analysis, pair analysis, positional trends, and overdue numbers.",
            agent=pattern_researcher,
        ),
        Task(
            description=f"""Generate tiered predictions for the next {draw_type} draw.
Use the Prediction Generator tool to produce picks for:
- 2+bonus tier: most probable pair + bonus ball
- 3+bonus tier: most probable triple + bonus ball
- 4+bonus tier: most probable quadruple + bonus ball
- 5+bonus tier: most probable five-number set + bonus ball
- 6+bonus tier: most probable full set + bonus ball

Each tier should have 3 ranked picks with probability scores.
Use ALL the analysis from previous steps to inform your prediction strategy.""",
            expected_output="JSON object with tiered predictions, each tier containing 3 ranked picks with numbers, bonus ball, and probability.",
            agent=predictor,
        ),
    ]
