from langchain.chat_models import ChatOpenAI
from crewai import Agent
from app.config import settings

llm = ChatOpenAI(
    model=settings.groq_model.replace("groq/", ""),
    openai_api_key=settings.groq_api_key,
    openai_api_base="https://api.groq.com/openai/v1",
    temperature=0.7,
)

from backend.crew.tools.scraper_tool import UK49ScraperTool
from backend.crew.tools.analysis_tool import FrequencyAnalysisTool
from crew.tools.pattern_tool import PatternAnalysisTool
from crew.tools.predictor_tool import PredictionTool

scraper_tool = UK49ScraperTool()
freq_tool = FrequencyAnalysisTool()
pattern_tool = PatternAnalysisTool()
predict_tool = PredictionTool()

data_collector = Agent(
    role="Data Collector",
    goal="Scrape UK49 draw results from lotteryextreme.com and store them in the database.",
    backstory="Expert web scraper who efficiently collects lottery data. You know exactly how to extract structured data from HTML tables.",
    tools=[scraper_tool],
    llm=llm,
    verbose=True,
)

data_analyst = Agent(
    role="Data Analyst",
    goal="Analyze number frequency, hot/cold numbers, odd/even splits, and sum ranges from draw history.",
    backstory="Statistical analyst specializing in lottery number patterns. You turn raw draw data into actionable statistical insights.",
    tools=[freq_tool],
    llm=llm,
    verbose=True,
)

pattern_researcher = Agent(
    role="Pattern Researcher",
    goal="Detect delta patterns, sequential pairs, positional trends, and overdue numbers in draw data.",
    backstory="Pattern recognition expert who finds hidden relationships in draw data. You spot trends others miss.",
    tools=[pattern_tool],
    llm=llm,
    verbose=True,
)

predictor = Agent(
    role="Predictor",
    goal="Generate tiered predictions ranked by probability for all tiers from 2+bonus to 6+bonus.",
    backstory="Senior lottery strategist who synthesizes all analysis into actionable picks. You combine statistical frequency with pattern insights to generate the most probable number combinations.",
    tools=[predict_tool],
    llm=llm,
    verbose=True,
)
