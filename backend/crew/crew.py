import logging
from crewai import Crew, Process
from app.config import settings
from crew.agents import data_collector, data_analyst, pattern_researcher, predictor, groq_llm, gemini_llm, get_llm
from crew.tasks import make_tasks

logger = logging.getLogger(__name__)

def run_analysis(draw_type: str = "lunchtime") -> str:
    from crew import agents as agent_module

    current_provider = settings.llm_provider
    used_fallback = False

    for attempt in range(2):
        try:
            selected = get_llm() if attempt == 0 else gemini_llm if current_provider == "groq" else groq_llm
            if attempt == 1:
                used_fallback = True
                logger.info("Falling back to alternate LLM provider")

            agent_module.data_collector.llm = selected
            agent_module.data_analyst.llm = selected
            agent_module.pattern_researcher.llm = selected
            agent_module.predictor.llm = selected

            tasks = make_tasks(draw_type)
            crew = Crew(
                agents=[data_collector, data_analyst, pattern_researcher, predictor],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
            )
            return crew.kickoff()

        except Exception as e:
            error_text = str(e).lower()
            is_rate_limit = "429" in str(e) or "rate limit" in error_text or "quota" in error_text
            if is_rate_limit and attempt == 0 and current_provider == "groq" and gemini_llm is not None:
                logger.warning(f"Rate limit on Groq, retrying with Gemini: {e}")
                continue
            raise

    raise RuntimeError("Analysis failed after fallback")
