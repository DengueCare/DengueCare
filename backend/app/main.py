from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, patient, dashboard

app = FastAPI(
    title="DengueCare AI API - Web Chat",
    description="Backend preditivo para triagem e monitoramento da Dengue",
    version="1.0.0"
)

# Configuração de Segurança: CORS
# Em produção, substituir o "*" pelo domínio real do frontend (ex: ["https://denguecare.fatecrc.edu.br"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas modulares
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Web Chat Interface"])
app.include_router(patient.router, prefix="/api/v1/patients", tags=["Medical Interface"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Triage Dashboard"])

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "operational", "system": "Aedes Copilot RC (Web)"}