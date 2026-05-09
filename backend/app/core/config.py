import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Pega o caminho absoluto da pasta backend (3 níveis acima de config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra="ignore")

settings = Settings()