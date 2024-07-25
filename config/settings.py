# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr
from typing import Dict

class Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    MAX_CONVERSATION_HISTORY: int = 10

    AGENTS: Dict[str, Dict[str, str]] = {
        "moderator": {
            "role": "대화를 분석하고 다음 발언자를 선택하는 사회자입니다.",
            "model": "gpt-4o-mini"
        },
        "head_of_product": {
            "role": "제품 전략을 수립하고 전체적인 제품 방향을 결정합니다.",
            "model": "gpt-4o"
        },
        "frontend_developer": {
            "role": "사용자 인터페이스와 사용자 경험을 개발합니다.",
            "model": "gpt-4o-mini"
        },
        "api_developer": {
            "role": "백엔드 API를 설계하고 구현합니다.",
            "model": "gpt-4o-mini"
        }
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()