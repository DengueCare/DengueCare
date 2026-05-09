# app/handlers/start_handler.py
"""
Handler principal do bot: /start, fluxo de identificação e cadastro de paciente.

Fluxo conversacional (Máquina de Estados):
  1. Usuário envia /start → Bot saúda e pede o número da carteira
  2. Usuário digita nr_carteira → Bot busca no Supabase
  3a. Se encontrado → Saúda pelo nome, armazena no context e exibe menu
  3b. Se não encontrado → Pergunta se deseja cadastrar
  4. Fluxo de Cadastro:
     - Pede o Nome Completo
     - Pede a Carteira
     - Salva no banco e exibe menu
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.db.database import AsyncSessionLocal
from app.services.patient_service import buscar_paciente_por_carteira, criar_paciente

logger = logging.getLogger(__name__)

# ==========================================
# ESTADOS DA MÁQUINA DE CONVERSA
# ==========================================
AGUARDANDO_CARTEIRA = 0
AGUARDANDO_NOME_CADASTRO = 1
AGUARDANDO_CARTEIRA_CADASTRO = 2


# ==========================================
# HANDLER: /start — Ponto de entrada do bot
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Acionado quando o usuário envia /start.
    Exibe a saudação inicial e solicita o número da carteira.
    """
    user = update.effective_user
    logger.info(f"Novo /start recebido de {user.first_name} (telegram_id: {user.id})")

    await update.message.reply_text(
        f"🦟 *Olá, {user.first_name}\\!*\n\n"
        f"Bem\\-vindo ao *DengueCare* — seu assistente de acompanhamento da Dengue\\.\n\n"
        f"Para começarmos, preciso identificar seu cadastro\\.\n"
        f"Por favor, digite o seu *número da carteira*:",
        parse_mode="MarkdownV2",
    )

    return AGUARDANDO_CARTEIRA


# ==========================================
# HANDLER: Recebe o nr_carteira para busca
# ==========================================
async def receber_carteira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recebe o texto digitado (nr_carteira) e consulta o Supabase.
    Se não encontrar, oferece a opção de cadastro.
    """
    nr_carteira = update.message.text.strip()
    
    if not nr_carteira.replace('.', '').replace('-', '').isdigit():
        await update.message.reply_text("⚠️ Por favor, digite apenas números para a carteira.")
        return AGUARDANDO_CARTEIRA

    # Limpa apenas os caracteres numéricos caso tenha digitado pontos
    nr_carteira_limpo = ''.join(filter(str.isdigit, nr_carteira))

    try:
        async with AsyncSessionLocal() as db:
            paciente = await buscar_paciente_por_carteira(db, nr_carteira_limpo)

        if paciente:
            return await _exibir_menu_paciente(update, context, paciente)
        else:
            keyboard = [
                [InlineKeyboardButton("✅ Sim, quero me cadastrar", callback_data="iniciar_cadastro")],
                [InlineKeyboardButton("🔄 Tentar outro número", callback_data="tentar_novamente")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"❌ Nenhum paciente encontrado com a carteira *{_escape_md(nr_carteira)}*\\.\n\n"
                f"Deseja realizar o seu cadastro agora?",
                parse_mode="MarkdownV2",
                reply_markup=reply_markup,
            )
            return AGUARDANDO_CARTEIRA

    except Exception as e:
        logger.error(f"Erro ao buscar paciente: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Ocorreu um erro no sistema. Tente novamente mais tarde.")
        return ConversationHandler.END


# ==========================================
# CALLBACKS: Fluxo de não-encontrado
# ==========================================
async def callback_iniciar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de cadastro perguntando o nome."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("📝 *Cadastro de Paciente*\n\nPor favor, digite o seu *Nome Completo*:", parse_mode="MarkdownV2")
    return AGUARDANDO_NOME_CADASTRO


async def callback_tentar_novamente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede o número da carteira novamente sem alterar o estado."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("🔄 Certo\\! Digite o *número da carteira* novamente:", parse_mode="MarkdownV2")
    return AGUARDANDO_CARTEIRA


# ==========================================
# HANDLERS: Fluxo de Cadastro
# ==========================================
async def receber_nome_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome e pede a carteira."""
    nome = update.message.text.strip()
    context.user_data['cadastro_nome'] = nome
    
    await update.message.reply_text(f"Ótimo, {_escape_md(nome)}\\.\n\nAgora, digite o número da sua *Carteira*:", parse_mode="MarkdownV2")
    return AGUARDANDO_CARTEIRA_CADASTRO


async def receber_carteira_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a carteira, cria o paciente no DB e exibe o menu."""
    nr_carteira = update.message.text.strip()
    
    if not nr_carteira.replace('.', '').replace('-', '').isdigit():
        await update.message.reply_text("⚠️ Por favor, digite apenas números para a carteira.")
        return AGUARDANDO_CARTEIRA_CADASTRO

    nr_carteira_limpo = ''.join(filter(str.isdigit, nr_carteira))
    nome = context.user_data.get('cadastro_nome')

    try:
        async with AsyncSessionLocal() as db:
            paciente = await criar_paciente(db, nome, nr_carteira_limpo)
        
        # Limpa variável temporária de cadastro
        context.user_data.pop('cadastro_nome', None)
        
        await update.message.reply_text("🎉 *Cadastro realizado com sucesso\\!*", parse_mode="MarkdownV2")
        return await _exibir_menu_paciente(update, context, paciente)

    except Exception as e:
        logger.error(f"Erro ao criar paciente: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Ocorreu um erro ao criar seu cadastro. Pode ser que essa carteira já exista. Tente usar /start novamente.")
        return ConversationHandler.END


# ==========================================
# FUNÇÃO AUXILIAR: Exibe o menu principal
# ==========================================
async def _exibir_menu_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE, paciente: dict) -> int:
    """Armazena o paciente no contexto e exibe as opções pós-identificação."""
    context.user_data["paciente"] = paciente

    keyboard = [
        [InlineKeyboardButton("📋 Meu Acompanhamento", callback_data="acompanhamento")],
        [InlineKeyboardButton("🔄 Trocar Paciente", callback_data="trocar_paciente")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    mensagem = (
        f"✅ *Paciente identificado\\!*\n\n"
        f"👤 *Nome:* {_escape_md(paciente['nm_usuario'])}\n"
        f"🪪 *Carteira:* {_escape_md(str(paciente['nr_carteira']))}\n\n"
        f"Olá, *{_escape_md(paciente['nm_usuario'])}*\\! "
        f"Estou aqui para acompanhar sua recuperação\\.\n"
        f"Escolha uma opção abaixo:"
    )

    if update.message:
        await update.message.reply_text(mensagem, parse_mode="MarkdownV2", reply_markup=reply_markup)
    else:
        # Se veio de um callback query
        await update.callback_query.edit_message_text(mensagem, parse_mode="MarkdownV2", reply_markup=reply_markup)

    return ConversationHandler.END


# ==========================================
# CALLBACKS: Botões inline pós-identificação
# ==========================================
async def callback_acompanhamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback do botão 'Meu Acompanhamento'."""
    query = update.callback_query
    await query.answer()

    paciente = context.user_data.get("paciente")
    if paciente:
        await query.edit_message_text(
            f"📋 *Acompanhamento de {_escape_md(paciente['nm_usuario'])}*\n\n"
            f"🚧 Esta funcionalidade está em desenvolvimento\\.\n"
            f"Em breve você poderá registrar sintomas, ver histórico e receber alertas\\.\n\n"
            f"Use /start para voltar ao menu\\.",
            parse_mode="MarkdownV2",
        )
    else:
        await query.edit_message_text("⚠️ Sessão expirada. Use /start para se identificar novamente.")


async def callback_trocar_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback do botão 'Trocar Paciente'."""
    query = update.callback_query
    await query.answer()

    context.user_data.pop("paciente", None)
    await query.edit_message_text(
        "🔄 Certo\\! Digite o *número da carteira* do novo paciente:", 
        parse_mode="MarkdownV2"
    )
    return AGUARDANDO_CARTEIRA


# ==========================================
# HANDLER: /cancelar — Sai do fluxo
# ==========================================
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Encerra a conversa de identificação ou cadastro."""
    await update.message.reply_text("👋 Operação cancelada. Use /start quando quiser retomar.")
    return ConversationHandler.END


# ==========================================
# UTILITÁRIO: Escape MarkdownV2
# ==========================================
def _escape_md(text: str) -> str:
    """Escapa caracteres especiais do MarkdownV2."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for char in text:
        if char in special_chars:
            escaped += f"\\{char}"
        else:
            escaped += char
    return escaped


# ==========================================
# FÁBRICA: Monta o ConversationHandler
# ==========================================
def create_start_conversation_handler() -> ConversationHandler:
    """
    Cria e retorna o ConversationHandler de identificação e cadastro de paciente.
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(callback_trocar_paciente, pattern="^trocar_paciente$")
        ],
        states={
            AGUARDANDO_CARTEIRA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_carteira),
                CallbackQueryHandler(callback_iniciar_cadastro, pattern="^iniciar_cadastro$"),
                CallbackQueryHandler(callback_tentar_novamente, pattern="^tentar_novamente$"),
            ],
            AGUARDANDO_NOME_CADASTRO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome_cadastro),
            ],
            AGUARDANDO_CARTEIRA_CADASTRO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_carteira_cadastro),
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", start_command),
        ],
    )
