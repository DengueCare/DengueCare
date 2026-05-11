# bot.py
"""
DengueCare Telegram Bot — Modo Webhook (Render)
 
Em vez de long-polling (conexão aberta contínua), agora usamos Webhook:
- O Telegram envia uma requisição POST para nossa URL no Render
- O FastAPI recebe, repassa para o bot processar, e responde
- Isso permite rodar em qualquer servidor web padrão, incluindo o Render gratuito
 
Execução local para testes: uvicorn bot:app --reload --port 8000
Em produção (Render): o próprio Render executa uvicorn automaticamente
"""
 
import sys
import os
import time
import logging
import asyncio
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from sqlalchemy import text
 
from app.core.config import settings
from app.db.database import engine, AsyncSessionLocal
from app.handlers.start_handler import (
    create_start_conversation_handler,
    callback_acompanhamento,
    callback_trocar_paciente,
)
from app.handlers.error_handler import (
    error_handler,
    unknown_command,
    unknown_text,
    ajuda_command,
)
 
# ==========================================
# CONFIGURAÇÃO DE LOGGING
# ==========================================
logging.basicConfig(
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
 
logger = logging.getLogger("denguecare.bot")
 
# ==========================================
# MONTAGEM DA APPLICATION DO TELEGRAM
# (criada uma vez, reutilizada em todas as requisições)
# ==========================================
def build_application() -> Application:
    """Constrói e configura a Application do python-telegram-bot."""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
 
    # Handlers — mesma ordem do bot.py original
    conv_handler = create_start_conversation_handler()
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("ajuda", ajuda_command))
    application.add_handler(CallbackQueryHandler(callback_acompanhamento, pattern="^acompanhamento$"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    application.add_error_handler(error_handler)
 
    return application
 
# Instância global — criada uma vez quando o servidor sobe
ptb_app = build_application()
 
# ==========================================
# LIFESPAN: startup e shutdown do servidor
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executa ao subir e ao desligar o servidor."""
 
    # --- STARTUP ---
    logger.info("🦟 Iniciando DengueCare Bot (modo Webhook)...")
 
    # Testa conexão com Supabase
    start_time = time.perf_counter()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"✅ [SUPABASE] Conexão OK! Ping: {latency}ms")
 
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM paciente"))
            count = result.scalar()
            logger.info(f"✅ [SUPABASE] Tabela 'paciente' acessível. Registros: {count}")
    except Exception as e:
        logger.error(f"❌ [SUPABASE] Falha de conexão: {e}")
 
    # Inicializa o bot do Telegram
    await ptb_app.initialize()
    await ptb_app.start()
 
    # Registra o Webhook no Telegram automaticamente
    webhook_url = f"{settings.RENDER_EXTERNAL_URL}/webhook"
    try:
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info(f"✅ [WEBHOOK] Registrado com sucesso: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ [WEBHOOK] Falha ao registrar webhook: {e}")
 
    logger.info("🚀 Servidor pronto para receber mensagens!\n")
 
    yield  # servidor fica rodando aqui
 
    # --- SHUTDOWN ---
    logger.info("🛑 Encerrando bot...")
    await ptb_app.stop()
    await ptb_app.shutdown()
    await engine.dispose()
    logger.info("🛑 Encerrado com segurança.")
 
 
# ==========================================
# APLICAÇÃO FASTAPI
# ==========================================
app = FastAPI(
    title="DengueCare Bot — Webhook",
    description="Recebe updates do Telegram via Webhook",
    version="2.0.0",
    lifespan=lifespan,
)
 
 
# ==========================================
# ENDPOINT DO WEBHOOK
# O Telegram vai bater aqui a cada mensagem recebida
# ==========================================
@app.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    """
    Recebe o JSON do Telegram, converte em objeto Update
    e passa para o bot processar de forma assíncrona.
    """
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=ptb_app.bot)
        await ptb_app.process_update(update)
    except Exception as e:
        logger.error(f"Erro ao processar update: {e}")
    # Sempre retorna 200 para o Telegram não reenviar a mensagem
    return Response(status_code=200)
 
 
# ==========================================
# ENDPOINT DE HEALTH CHECK
# Usado pelo UptimeRobot para manter o servidor acordado
# e pelo Render para saber se o serviço está vivo
# ==========================================
@app.get("/health")
async def health_check():
    """Verifica se o servidor está no ar."""
    return {"status": "ok", "bot": "DengueCare 🦟"}
 
 
# ==========================================
# ENDPOINT RAIZ (informativo)
# ==========================================
@app.get("/")
async def root():
    return {"message": "DengueCare Bot está rodando!", "webhook": "/webhook", "health": "/health"}
