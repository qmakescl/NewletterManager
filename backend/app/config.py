from pathlib import Path

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gmail_credentials_path: Path = Path("./credentials.json")
    database_url: str = "sqlite:///./tldr.db"
    chroma_persist_dir: str = "./chroma_db"
    sync_schedule_hour: int = 7
    cors_origins: str = "http://localhost:3000"
    daily_api_call_limit: int = 900
    newsletter_senders: list[str] = ["dan@tldrnewsletter.com"]

    model_config = {
        "env_file": str(_BACKEND_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
