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
AGUARDANDO_DT_NASCIMENTO = 3
AGUARDANDO_SEXO = 4
AGUARDANDO_DIABETES = 5
AGUARDANDO_HEMATOLOG = 6
AGUARDANDO_HEPATOPAT = 7
AGUARDANDO_RENAL = 8
AGUARDANDO_HIPERTENSA = 9
AGUARDANDO_ACIDO_PEPT = 10
AGUARDANDO_AUTO_IMUNE = 11

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

from datetime import datetime
from datetime import date
# ==========================================
# HANDLER: Recebe o nr_carteira para busca
# ==========================================
async def receber_carteira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recebe o nr_carteira, consulta o banco e oferece opções de Cadastro ou Tentar Novamente.
    """
    nr_carteira = update.message.text.strip()
    
    if not nr_carteira.replace('.', '').replace('-', '').isdigit():
        await update.message.reply_text("⚠️ Por favor, digite apenas números para a carteira\\.")
        return AGUARDANDO_CARTEIRA

    nr_carteira_limpo = ''.join(filter(str.isdigit, nr_carteira))
    
    # Mantemos a carteira salva para o caso de ele escolher cadastrar
    context.user_data['cadastro_carteira'] = nr_carteira_limpo

    try:
        async with AsyncSessionLocal() as db:
            paciente = await buscar_paciente_por_carteira(db, nr_carteira_limpo)

        if paciente:
            return await _exibir_menu_paciente(update, context, paciente)
        else:
            # RESTAURADO: Agora com os dois botões novamente
            keyboard = [
                [InlineKeyboardButton("✅ Sim, quero me cadastrar", callback_data="iniciar_cadastro")],
                [InlineKeyboardButton("🔄 Tentar outro número", callback_data="tentar_novamente")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"❌ Carteira *{_escape_md(nr_carteira)}* não encontrada\\.\n\nDeseja realizar o seu cadastro agora?",
                parse_mode="MarkdownV2",
                reply_markup=reply_markup,
            )
            return AGUARDANDO_CARTEIRA
            
    except Exception as e:
        logger.error(f"Erro ao buscar paciente: {e}")
        await update.message.reply_text("⚠️ Ocorreu um erro no sistema\\. Tente novamente mais tarde\\.")
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
    nome = update.message.text.strip()
    context.user_data['cadastro_nome'] = nome
    
    # Adicionamos as barras de escape em todos os pontos e exclamações
    await update.message.reply_text(
        f"Ótimo, {_escape_md(nome)}\\!\n\n"
        f"Como já tenho sua carteira, agora preciso da sua *Data de Nascimento*\\.\n"
        f"Por favor, digite no formato *DD/MM/AAAA*\\.\n\n"
        f"Exemplo: `15/05/1990`", 
        parse_mode="MarkdownV2"
    )
    return AGUARDANDO_DT_NASCIMENTO


async def receber_carteira_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nr_carteira = update.message.text.strip()
    # Apenas limpa e guarda o dado
    nr_carteira_limpo = ''.join(filter(str.isdigit, nr_carteira))
    context.user_data['cadastro_carteira'] = nr_carteira_limpo
    
    await update.message.reply_text("📅 Qual a sua *Data de Nascimento*?")
    return AGUARDANDO_DT_NASCIMENTO

async def receber_dt_nascimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto_data = update.message.text.strip()
    
    try:
        data_nasc = datetime.strptime(texto_data, "%d/%m/%Y")
        hoje = datetime.now()
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        
        context.user_data['DT_NASCIMENTO'] = data_nasc.strftime("%Y-%m-%d")
        
        # Garante que a idade seja um float, ex: 34.0, igual ao ETL
        context.user_data['idade_anos'] = float(idade) 
        
    except ValueError:
        await update.message.reply_text("⚠️ Formato inválido. Por favor, digite sua data de nascimento no formato *DD/MM/AAAA*.\nExemplo: `15/05/1990`", parse_mode="Markdown")
        return AGUARDANDO_DT_NASCIMENTO
        
    keyboard = [
        [InlineKeyboardButton("Masculino", callback_data="sexo_M"),
         InlineKeyboardButton("Feminino", callback_data="sexo_F")]
    ]
    await update.message.reply_text("Qual o seu *sexo biológico*?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return AGUARDANDO_SEXO

# --- INÍCIO DO FLUXO DE COMORBIDADES (1 = Sim, 2 = Não) ---

def botoes_sim_nao(prefixo):
    """Função auxiliar para gerar botões de Sim e Não"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Sim", callback_data=f"{prefixo}_1"), 
         InlineKeyboardButton("Não", callback_data=f"{prefixo}_2")]
    ])

async def callback_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['cs_sexo'] = query.data.split('_')[1] # Pega 'M' ou 'F'
    
    await query.edit_message_text("Você possui *Diabetes*?", reply_markup=botoes_sim_nao("diab"), parse_mode="Markdown")
    return AGUARDANDO_DIABETES

async def callback_diabetes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['diabetes'] = float(query.data.split('_')[1]) 
    
    await query.edit_message_text("Você possui *Doenças Hematológicas*?", reply_markup=botoes_sim_nao("hemato"), parse_mode="Markdown")
    return AGUARDANDO_HEMATOLOG

async def callback_hematolog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['hematolog'] = float(query.data.split('_')[1])
    
    await query.edit_message_text("Você possui *Doenças no Fígado (Hepatopatias)*?", reply_markup=botoes_sim_nao("hepato"), parse_mode="Markdown")
    return AGUARDANDO_HEPATOPAT

async def callback_hepatopat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['hepatopat'] = float(query.data.split('_')[1])
    
    await query.edit_message_text("Você possui *Doenças Renais*?", reply_markup=botoes_sim_nao("renal"), parse_mode="Markdown")
    return AGUARDANDO_RENAL

async def callback_renal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['renal'] = float(query.data.split('_')[1])
    
    await query.edit_message_text("Você possui *Hipertensão Arterial*?", reply_markup=botoes_sim_nao("hiper"), parse_mode="Markdown")
    return AGUARDANDO_HIPERTENSA

async def callback_hipertensa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['hipertensa'] = float(query.data.split('_')[1])
    
    await query.edit_message_text("Você possui *Doença Ácido-Péptica* (ex: Gastrite, Úlcera)?", reply_markup=botoes_sim_nao("acido"), parse_mode="Markdown")
    return AGUARDANDO_ACIDO_PEPT

async def callback_acido_pept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['acido_pept'] = float(query.data.split('_')[1])
    
    await query.edit_message_text("Você possui alguma *Doença Autoimune*?", reply_markup=botoes_sim_nao("auto"), parse_mode="Markdown")
    return AGUARDANDO_AUTO_IMUNE

async def callback_auto_imune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Última pergunta: salva no banco e encerra o fluxo."""
    query = update.callback_query
    await query.answer()
    context.user_data['auto_imune'] = float(query.data.split('_')[1])
    
    # Prepara os dados para enviar ao banco
    ud = context.user_data
    
    try:
        async with AsyncSessionLocal() as db:
            paciente = await criar_paciente(
                db=db,
                nm_usuario=ud['cadastro_nome'],
                nr_carteira=ud['cadastro_carteira'],
                DT_NASCIMENTO=ud['DT_NASCIMENTO'],
                cs_sexo=ud['cs_sexo'],
                diabetes=ud['diabetes'],
                hematolog=ud['hematolog'],
                hepatopat=ud['hepatopat'],
                renal=ud['renal'],
                hipertensa=ud['hipertensa'],
                acido_pept=ud['acido_pept'],
                auto_imune=ud['auto_imune']
            )
        
        # Limpa variáveis temporárias de cadastro
        chaves_limpar = ['cadastro_nome', 'cadastro_carteira', 'cs_sexo', 
                         'diabetes', 'hematolog', 'hepatopat', 'renal', 'hipertensa', 
                         'acido_pept', 'auto_imune']
        for chave in chaves_limpar:
            ud.pop(chave, None)
        
        await query.edit_message_text("🎉 *Cadastro realizado com sucesso\\!*", parse_mode="MarkdownV2")
        return await _exibir_menu_paciente(update, context, paciente)

    except Exception as e:
        logger.error(f"Erro ao criar paciente: {e}", exc_info=True)
        await query.edit_message_text("⚠️ Ocorreu um erro ao salvar os dados. Tente usar /start novamente.")
        return ConversationHandler.END

# ==========================================
# FUNÇÃO AUXILIAR: Exibe o menu principal
# ==========================================
async def _exibir_menu_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE, paciente: dict) -> int:
    """Exibe o menu com proteções contra dados nulos no banco."""
    context.user_data["paciente"] = paciente

    # --- PROTEÇÃO PARA IDADE ---
    dt_nasc = paciente.get("DT_NASCIMENTO")
    idade_texto = "Não informada"
    
    if dt_nasc:
        try:
            # Se for objeto date (o que o SQLAlchemy costuma retornar)
            if isinstance(dt_nasc, date):
                hoje = date.today()
                idade = hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day))
                idade_texto = f"{idade} anos"
            # Se for string (caso o banco retorne texto)
            elif isinstance(dt_nasc, str) and len(dt_nasc) >= 10:
                from datetime import datetime
                # Tenta converter a string 'YYYY-MM-DD'
                dt_objeto = datetime.strptime(dt_nasc[:10], "%Y-%m-%d").date()
                hoje = date.today()
                idade = hoje.year - dt_objeto.year - ((hoje.month, hoje.day) < (dt_objeto.month, dt_objeto.day))
                idade_texto = f"{idade} anos"
        except Exception as e:
            # Se der qualquer erro no cálculo, ele apenas mantém "Não informada" e não trava
            logger.warning(f"Erro ao calcular idade para o paciente {paciente.get('id')}: {e}")

    # --- PROTEÇÃO PARA SEXO ---
    sexo_raw = paciente.get("cs_sexo")
    sexo_map = {"M": "Masculino", "F": "Feminino"}
    # Se sexo_raw for None ou não estiver no mapa, retorna "Não informado"
    sexo_texto = sexo_map.get(str(sexo_raw).upper(), "Não informado")

    keyboard = [
        [InlineKeyboardButton("📋 Meu Acompanhamento", callback_data="acompanhamento")],
        [InlineKeyboardButton("🔄 Trocar Paciente", callback_data="trocar_paciente")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    mensagem = (
        f"✅ *Paciente identificado\\!*\n\n"
        f"👤 *Nome:* {_escape_md(paciente.get('nm_usuario', 'Não informado'))}\n"
        f"🪪 *Carteira:* {_escape_md(str(paciente.get('nr_carteira', '---')))}\n"
        f"🎂 *Idade:* {_escape_md(idade_texto)}\n"
        f"🚻 *Sexo:* {_escape_md(sexo_texto)}\n\n"
        f"Olá, *{_escape_md(paciente.get('nm_usuario', 'Paciente'))}*\\! "
        f"Estou aqui para acompanhar sua recuperação\\.\n"
        f"Escolha uma opção abaixo:"
    )

    if update.message:
        await update.message.reply_text(mensagem, parse_mode="MarkdownV2", reply_markup=reply_markup)
    else:
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
            # --- NOVOS ESTADOS AQUI ---
            AGUARDANDO_DT_NASCIMENTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dt_nascimento)
            ],
            AGUARDANDO_SEXO: [
                CallbackQueryHandler(callback_sexo, pattern="^sexo_")
            ],
            AGUARDANDO_DIABETES: [CallbackQueryHandler(callback_diabetes, pattern="^diab_")],
            AGUARDANDO_HEMATOLOG: [CallbackQueryHandler(callback_hematolog, pattern="^hemato_")],
            AGUARDANDO_HEPATOPAT: [CallbackQueryHandler(callback_hepatopat, pattern="^hepato_")],
            AGUARDANDO_RENAL: [CallbackQueryHandler(callback_renal, pattern="^renal_")],
            AGUARDANDO_HIPERTENSA: [CallbackQueryHandler(callback_hipertensa, pattern="^hiper_")],
            AGUARDANDO_ACIDO_PEPT: [CallbackQueryHandler(callback_acido_pept, pattern="^acido_")],
            AGUARDANDO_AUTO_IMUNE: [CallbackQueryHandler(callback_auto_imune, pattern="^auto_")],
            # --------------------------
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", start_command),
        ],
    )