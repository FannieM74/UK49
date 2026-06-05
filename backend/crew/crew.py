from crewai import Crew, Process
from crew.agents import data_collector, data_analyst, pattern_researcher, predictor
from crew.tasks import make_tasks

def run_analysis(draw_type: str = "lunchtime") -> str:
    tasks = make_tasks(draw_type)
    crew = Crew(
        agents=[data_collector, data_analyst, pattern_researcher, predictor],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew.kickoff()
