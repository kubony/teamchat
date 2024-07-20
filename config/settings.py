# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()