from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Motor que gerencia a comunicação com o Supabase
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Mude para True se quiser ver o SQL gerado no terminal durante o debug
    pool_size=20, # Mantém 20 conexões abertas prontas para uso
    max_overflow=10 # Permite até 10 conexões extras em picos de tráfego
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False
)

# Classe base para a criação dos modelos (tabelas)
Base = declarative_base()