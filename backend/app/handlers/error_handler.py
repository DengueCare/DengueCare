# app/handlers/error_handler.py
"""
Handler global de erros e fallbacks do bot.

Captura exceções não tratadas pelos handlers individuais,
loga o stack trace completo e envia mensagem amigável ao usuário.
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler global de erros registrado via application.add_error_handler().
    
    Captura QUALQUER exceção que escape dos handlers individuais,
    garantindo que o bot nunca "morra silenciosamente".
    """
    logger.error("Exceção durante o processamento de update:", exc_info=context.error)

    # Formata o traceback para o log
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"Traceback completo:\n{tb_string}")

    # Tenta enviar uma mensagem amigável ao usuário
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Ocorreu um erro inesperado no sistema.\n\n"
                "A equipe técnica foi notificada. "
                "Por favor, tente novamente com /start."
            )
        except Exception:
            # Se nem a mensagem de erro conseguir ser enviada, só loga
            logger.error("Falha ao enviar mensagem de erro ao usuário.")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Responde a comandos não reconhecidos.
    Registrado como MessageHandler(filters.COMMAND) com baixa prioridade.
    """
    await update.message.reply_text(
        "🤔 Não reconheço esse comando.\n\n"
        "Use /start para iniciar o acompanhamento."
    )


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Responde a mensagens de texto enviadas fora de qualquer conversa ativa.
    Evita que o usuário fique sem resposta.
    """
    await update.message.reply_text(
        "💬 Não estou esperando uma mensagem neste momento.\n\n"
        "Use /start para iniciar o acompanhamento "
        "ou /ajuda para ver os comandos disponíveis."
    )


async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /ajuda — lista os comandos disponíveis."""
    await update.message.reply_text(
        "🦟 *DengueCare — Comandos Disponíveis*\n\n"
        "/start — Iniciar e identificar paciente\n"
        "/ajuda — Ver esta lista de comandos\n"
        "/cancelar — Cancelar operação em andamento\n",
        parse_mode="MarkdownV2",
    )
