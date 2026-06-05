from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_org_id: str = ""
    groq_api_key: str = ""
    database_url: str = "sqlite:///data/uk49.db"
    groq_model: str = "groq/llama3-8b-8192"

    class Config:
        env_file = ".env"

settings = Settings()
