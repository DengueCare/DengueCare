# bot.py
"""
DengueCare Telegram Bot — Entry Point Principal

Este é o ponto de entrada do bot. Ele:
1. Configura o logging estruturado
2. Testa a conexão com o Supabase/PostgreSQL no startup
3. Registra todos os handlers (conversas, callbacks, fallbacks)
4. Inicia o polling (long-polling) para receber updates do Telegram

Execução: python bot.py
"""

import sys
import os
import time
import logging

# Garante que o diretório raiz do backend esteja no sys.path
# para que os imports 'app.xxx' funcionem corretamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
# CONFIGURAÇÃO DE LOGGING ESTRUTURADO
# ==========================================
logging.basicConfig(
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Console
    ],
)

# Reduz o nível de log das bibliotecas externas para evitar spam
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("denguecare.bot")


# ==========================================
# STARTUP: Teste de conexão com o Supabase
# ==========================================
async def post_init(application: Application) -> None:
    """
    Callback executado APÓS a inicialização do bot, antes de começar o polling.
    Ideal para testar conexões externas (Supabase, APIs, etc).
    """
    start_time = time.perf_counter()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        latency = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"✅ [SUPABASE] Conexão OK! Ping: {latency}ms")

        # Verifica se a tabela 'paciente' existe e é acessível
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM paciente"))
            count = result.scalar()
            logger.info(f"✅ [SUPABASE] Tabela 'paciente' acessível. Registros: {count}")

    except Exception as e:
        logger.error(f"❌ [SUPABASE] Falha de conexão na inicialização: {e}")
        logger.error("O bot iniciará, mas operações com banco de dados podem falhar.")


# ==========================================
# SHUTDOWN: Limpeza de recursos
# ==========================================
async def post_shutdown(application: Application) -> None:
    """
    Callback executado quando o bot é encerrado (Ctrl+C).
    Fecha o pool de conexões do SQLAlchemy.
    """
    await engine.dispose()
    logger.info("🛑 [SUPABASE] Pool de conexões encerrado com segurança.")


# ==========================================
# MAIN: Montagem e execução do bot
# ==========================================
def main() -> None:
    """Monta a Application, registra handlers e inicia o polling."""

    logger.info("🦟 Iniciando DengueCare Telegram Bot...")
    logger.info(f"📡 Token: ...{settings.TELEGRAM_BOT_TOKEN[-8:]}")

    # Cria a Application (equivalente ao antigo Updater do python-telegram-bot)
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)        # Testa DB no startup
        .post_shutdown(post_shutdown) # Limpa DB no shutdown
        .build()
    )

    # ------------------------------------------
    # REGISTRO DE HANDLERS (ordem importa!)
    # ------------------------------------------

    # 1. ConversationHandler do /start (prioridade mais alta)
    #    Gerencia o fluxo: saudação → pedir carteira → identificar paciente
    conv_handler = create_start_conversation_handler()
    application.add_handler(conv_handler)

    # 2. Comando /ajuda (funciona fora de conversas ativas)
    application.add_handler(CommandHandler("ajuda", ajuda_command))

    # 3. Callbacks dos botões inline (pós-identificação)
    application.add_handler(CallbackQueryHandler(callback_acompanhamento, pattern="^acompanhamento$"))

    # 4. Fallbacks (baixa prioridade — captura o que não foi tratado acima)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    # 5. Handler global de erros (captura exceções não tratadas)
    application.add_error_handler(error_handler)

    # ------------------------------------------
    # INICIA O POLLING
    # ------------------------------------------
    logger.info("🚀 Bot iniciado! Aguardando mensagens...")
    logger.info("   Pressione Ctrl+C para encerrar.\n")

    # run_polling() bloqueia aqui até Ctrl+C
    # drop_pending_updates=True ignora mensagens antigas acumuladas enquanto o bot estava offline
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
