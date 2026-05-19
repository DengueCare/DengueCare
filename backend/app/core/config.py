import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Mapeia dinamicamente o caminho absoluto para a pasta 'backend'
# __file__ = config.py -> app/core -> app -> backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    RENDER_EXTERNAL_URL: str = ""
    
    # Aponta explicitamente para o caminho absoluto do .env e garante o enconding
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, 
        env_file_encoding='utf-8', 
        extra="ignore"
    )

settings = Settings()