from pathlib import Path

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gmail_credentials_path: Path = Path("./credentials.json")
    database_url: str = "sqlite:///./tldr.db"
    chroma_persist_dir: str = "./chroma_db"
    cors_origins: str = "http://localhost:3000"
    daily_api_call_limit: int = 900
    newsletter_senders: list[str] = ["dan@tldrnewsletter.com"]

    # OAuth / JWT / 암호화
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret_key: str = ""
    token_encryption_key: str = ""  # Fernet key (32-byte base64)
    frontend_url: str = "http://localhost:3000"

    model_config = {
        "env_file": str(_BACKEND_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
