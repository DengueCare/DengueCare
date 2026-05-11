# bot_local.py
"""
Use este arquivo para testar o bot LOCALMENTE (na sua máquina).
Ele usa long-polling, sem precisar de URL pública.
 
Execução: python bot_local.py
 
Em produção (Render), o arquivo usado é o bot.py (modo Webhook).
"""
 
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
import logging
import time
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
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
 
logging.basicConfig(
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
 
logger = logging.getLogger("denguecare.local")
 
 
async def post_init(application: Application) -> None:
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
 
 
async def post_shutdown(application: Application) -> None:
    await engine.dispose()
    logger.info("🛑 Pool de conexões encerrado.")
 
 
def main() -> None:
    logger.info("🦟 [LOCAL] Iniciando DengueCare Bot em modo polling...")
 
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
 
    conv_handler = create_start_conversation_handler()
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("ajuda", ajuda_command))
    application.add_handler(CallbackQueryHandler(callback_acompanhamento, pattern="^acompanhamento$"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    application.add_error_handler(error_handler)
 
    logger.info("🚀 Bot local rodando! Pressione Ctrl+C para encerrar.\n")
    application.run_polling(drop_pending_updates=True)
 
 
if __name__ == "__main__":
    main()
 
