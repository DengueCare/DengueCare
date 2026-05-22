import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes import chat, patient, dashboard, auth
from app.db.database import engine # Importamos o motor diretamente

# ==========================================
# CICLO DE VIDA DO SERVIDOR (LIFESPAN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executa exatamente UMA VEZ quando o servidor inicia.
    Ideal para testar conexões e preparar caches.
    """
    start_time = time.perf_counter()
    try:
        # Usa o motor central para abrir uma conexão teste rápida
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        print(f"\n[OK] [SUPABASE] Conexão estabelecida com sucesso! Ping: {latency}ms\n")
    except Exception as e:
        print(f"\n[ERROR] [SUPABASE] Falha crítica de conexão na inicialização: {str(e)}\n")
    
    yield # O servidor fica rodando aqui, aceitando requisições do chat
    
    # Executa exatamente UMA VEZ quando o servidor desliga (Ctrl+C)
    await engine.dispose()
    print("\n[SHUTDOWN] [SUPABASE] Pool de conexões encerrado com segurança.\n")

# ==========================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==========================================
app = FastAPI(
    title="DengueCare AI API - Web Chat",
    description="Backend preditivo para triagem e monitoramento da Dengue",
    version="2.0.0",
    lifespan=lifespan # Injetamos o ciclo de vida aqui
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Web Chat Interface"])
app.include_router(patient.router, prefix="/api/v1/patients", tags=["Medical Interface"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Triage Dashboard"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação de Profissionais"])