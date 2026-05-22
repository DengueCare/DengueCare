# app/handlers/start_handler.py
"""
Handler principal do bot: /start, fluxo de identificação, cadastro e triagem diária.
Totalmente integrado ao modelo de Machine Learning e persistência assíncrona.
"""

import logging
from datetime import datetime, date
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
from app.services.atendimento_service import salvar_atendimento, buscar_ultimo_atendimento, buscar_historico_atendimentos
from app.services.bot_service import (
    PERGUNTAS_TRIAGEM,
    RESPOSTAS_CLASSIFICACAO,
    RESPOSTA_FALLBACK,
    MENSAGEM_EVOLUCAO,
    detectar_evolucao,
)
from app.services.ml_service import predict_classification

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
AGUARDANDO_TELEFONE = 12

# Estados do fluxo de triagem
TRIAGEM_PERGUNTA = 13


# ==========================================
# HANDLER: /start — Ponto de entrada do bot
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"Novo /start recebido de {user.first_name} (telegram_id: {user.id})")

    nome_esquivado = _escape_md(user.first_name)
    await update.message.reply_text(
        f"🦟 *Olá, {nome_esquivado}\\!*\n\n"
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
    nr_carteira = update.message.text.strip()

    if not nr_carteira.replace('.', '').replace('-', '').isdigit():
        await update.message.reply_text("⚠️ Por favor, digite apenas números para a carteira\\.")
        return AGUARDANDO_CARTEIRA

    nr_carteira_limpo = ''.join(filter(str.isdigit, nr_carteira))
    context.user_data['cadastro_carteira'] = nr_carteira_limpo

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
            await update.message.reply_text(
                f"❌ Carteira *{_escape_md(nr_carteira)}* não encontrada\\.\n\nDeseja realizar o seu cadastro agora?",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard),
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
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 *Cadastro de Paciente*\n\nPor favor, digite o seu *Nome Completo*:", parse_mode="MarkdownV2")
    return AGUARDANDO_NOME_CADASTRO


async def callback_tentar_novamente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        context.user_data['idade_anos'] = float(idade)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Formato inválido. Por favor, digite sua data de nascimento no formato *DD/MM/AAAA*.\nExemplo: `15/05/1990`",
            parse_mode="Markdown"
        )
        return AGUARDANDO_DT_NASCIMENTO

    keyboard = [
        [InlineKeyboardButton("Masculino", callback_data="sexo_M"),
         InlineKeyboardButton("Feminino", callback_data="sexo_F")]
    ]
    await update.message.reply_text(
        "Qual o seu *sexo biológico*?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return AGUARDANDO_SEXO


async def callback_atualizar_dados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    paciente = context.user_data.get("paciente")
    if not paciente:
        await query.edit_message_text("⚠️ Erro ao recuperar dados do paciente\\. Use /start novamente\\.")
        return ConversationHandler.END
    context.user_data['update_id'] = paciente['id']
    context.user_data['cadastro_nome'] = paciente['nm_usuario']
    context.user_data['cadastro_carteira'] = paciente['nr_carteira']
    await query.edit_message_text(
        "🔄 *Atualização de Perfil de Saúde*\n\n"
        "Por favor, digite sua *Data de Nascimento*\\.\n"
        "Exemplo: `15/05/1990`",
        parse_mode="MarkdownV2"
    )
    return AGUARDANDO_DT_NASCIMENTO


def botoes_sim_nao(prefixo):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim", callback_data=f"{prefixo}_1"),
         InlineKeyboardButton("❌ Não", callback_data=f"{prefixo}_2")]
    ])


async def callback_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['cs_sexo'] = query.data.split('_')[1]
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
    await query.edit_message_text("Você possui *Doenças no Fígado \\(Hepatopatias\\)*?", reply_markup=botoes_sim_nao("hepato"), parse_mode="MarkdownV2")
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
    await query.edit_message_text("Você possui *Doença Ácido\\-Péptica* \\(ex: Gastrite, Úlcera\\)?", reply_markup=botoes_sim_nao("acido"), parse_mode="MarkdownV2")
    return AGUARDANDO_ACIDO_PEPT


async def callback_acido_pept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['acido_pept'] = float(query.data.split('_')[1])
    await query.edit_message_text("Você possui alguma *Doença Autoimune*?", reply_markup=botoes_sim_nao("auto"), parse_mode="Markdown")
    return AGUARDANDO_AUTO_IMUNE


async def callback_auto_imune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['auto_imune'] = float(query.data.split('_')[1])
    
    # Após responder auto_imune, pede o telefone
    await query.edit_message_text(
        "📱 Para finalizar, por favor, digite o seu *número de WhatsApp com DDD* (somente números).\n"
        "Exemplo: `11999998888`",
        parse_mode="Markdown"
    )
    return AGUARDANDO_TELEFONE


async def handle_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telefone = update.message.text.strip()
    # Remove qualquer caracter que não seja número
    telefone_limpo = ''.join(filter(str.isdigit, telefone))
    
    if len(telefone_limpo) < 10:
        await update.message.reply_text(
            "⚠️ O número parece inválido. Por favor, digite o seu *WhatsApp com DDD* contendo apenas números.\n"
            "Exemplo: `11999998888`",
            parse_mode="Markdown"
        )
        return AGUARDANDO_TELEFONE
        
    context.user_data['telefone'] = telefone_limpo
    ud = context.user_data

    try:
        async with AsyncSessionLocal() as db:
            if ud.get('update_id'):
                from app.services.patient_service import atualizar_paciente
                await atualizar_paciente(
                    db=db, paciente_id=ud['update_id'],
                    DT_NASCIMENTO=ud['DT_NASCIMENTO'], cs_sexo=ud['cs_sexo'],
                    diabetes=ud['diabetes'], hematolog=ud['hematolog'],
                    hepatopat=ud['hepatopat'], renal=ud['renal'],
                    hipertensa=ud['hipertensa'], acido_pept=ud['acido_pept'],
                    auto_imune=ud['auto_imune'], telefone=ud['telefone']
                )
                paciente = await buscar_paciente_por_carteira(db, ud['cadastro_carteira'])
                mensagem_final = "✅ *Perfil de saúde atualizado com sucesso\\!*"
            else:
                paciente = await criar_paciente(
                    db=db, nm_usuario=ud['cadastro_nome'], nr_carteira=ud['cadastro_carteira'],
                    DT_NASCIMENTO=ud['DT_NASCIMENTO'], cs_sexo=ud['cs_sexo'],
                    diabetes=ud['diabetes'], hematolog=ud['hematolog'],
                    hepatopat=ud['hepatopat'], renal=ud['renal'],
                    hipertensa=ud['hipertensa'], acido_pept=ud['acido_pept'],
                    auto_imune=ud['auto_imune'], telefone=ud['telefone']
                )
                mensagem_final = "🎉 *Cadastro realizado com sucesso\\!*"

        chaves_limpar = ['cadastro_nome', 'cadastro_carteira', 'cs_sexo',
                         'diabetes', 'hematolog', 'hepatopat', 'renal', 'hipertensa',
                         'acido_pept', 'auto_imune', 'update_id', 'DT_NASCIMENTO', 'telefone']
        for chave in chaves_limpar:
            ud.pop(chave, None)

        await update.message.reply_text(mensagem_final, parse_mode="MarkdownV2")
        return await _exibir_menu_paciente(update, context, paciente)

    except Exception as e:
        logger.error(f"Erro ao processar dados do paciente: {e}", exc_info=True)
        await query.edit_message_text("⚠️ Ocorreu um erro ao salvar os dados. Tente usar /start novamente.")
        return ConversationHandler.END


# ==========================================
# FLUXO DE TRIAGEM DIÁRIA
# ==========================================

async def callback_acompanhamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    paciente = context.user_data.get("paciente")
    if not paciente:
        await query.edit_message_text(
            "⚠️ Sessão expirada\\. Use /start para se identificar novamente\\.",
            parse_mode="MarkdownV2"
        )
        return ConversationHandler.END

    context.user_data['triagem_index'] = 0
    context.user_data['triagem_inicio'] = datetime.now()
    context.user_data['triagem_respostas'] = {}

    await query.edit_message_text(
        f"📋 *Triagem Diária — {_escape_md(paciente['nm_usuario'])}*\n\n"
        f"Vou te fazer *{len(PERGUNTAS_TRIAGEM)} perguntas rápidas* sobre como você está se sentindo hoje\\.\n"
        f"Responda com os botões *Sim* ou *Não*\\.\n\n"
        f"Vamos começar\\! 👇",
        parse_mode="MarkdownV2"
    )

    return await _enviar_proxima_pergunta(update, context)


async def _enviar_proxima_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    index = context.user_data.get('triagem_index', 0)

    if index >= len(PERGUNTAS_TRIAGEM):
        return await _finalizar_triagem(update, context)

    chave, texto, prefixo = PERGUNTAS_TRIAGEM[index]
    total = len(PERGUNTAS_TRIAGEM)
    progresso = f"_{index + 1}/{total}_\n\n"

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim", callback_data=f"triagem_{prefixo}_1"),
         InlineKeyboardButton("❌ Não", callback_data=f"triagem_{prefixo}_2")]
    ])

    mensagem = progresso + texto

    if update.callback_query:
        try:
            await update.callback_query.message.reply_text(
                mensagem,
                parse_mode="MarkdownV2",
                reply_markup=teclado
            )
        except Exception:
            await update.callback_query.edit_message_text(
                mensagem,
                parse_mode="MarkdownV2",
                reply_markup=teclado
            )
    else:
        await update.message.reply_text(
            mensagem,
            parse_mode="MarkdownV2",
            reply_markup=teclado
        )

    return TRIAGEM_PERGUNTA


async def callback_triagem_resposta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    partes = query.data.split('_')
    valor = partes[-1]
    chave = '_'.join(partes[1:-1])

    context.user_data['triagem_respostas'][chave] = valor

    resposta_texto = "✅ Sim" if valor == "1" else "❌ Não"
    _, texto_pergunta, _ = PERGUNTAS_TRIAGEM[context.user_data['triagem_index']]
    try:
        await query.edit_message_text(
            f"{texto_pergunta}\n\n*Resposta:* {resposta_texto}",
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

    context.user_data['triagem_index'] += 1
    return await _enviar_proxima_pergunta(update, context)


async def _finalizar_triagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    paciente = context.user_data.get("paciente")
    respostas = context.user_data.get('triagem_respostas', {})
    dt_inicio = context.user_data.get('triagem_inicio', datetime.now())
    dt_fim = datetime.now()

    if isinstance(paciente.get('DT_NASCIMENTO'), date):
        hoje = date.today()
        dt_nasc = paciente.get('DT_NASCIMENTO')
        idade_anos = float(hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day)))
    else:
        idade_anos = context.user_data.get('idade_anos', 30.0)

    sexo_raw = str(paciente.get('cs_sexo', 'M')).upper()
    cs_sexo = 1 if sexo_raw == 'M' else (0 if sexo_raw == 'F' else -1)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT diabetes, hematolog, hepatopat, renal, hipertensa, acido_pept, auto_imune FROM paciente WHERE id = :id"),
            {"id": paciente['id']}
        )
        row = result.fetchone()
        comorbidades = dict(row._mapping) if row else {}

    def parse_comorb(val):
        """
        Converte o valor do banco de dados para o formato do SINAN esperado pelo modelo ML:
        1.0 = Sim
        2.0 = Não
        O banco pode armazenar 0 ou nulo para 'Não', ambos devem virar 2.0.
        """
        if val is None:
            return 2.0
        try:
            f = float(val)
            return 1.0 if f == 1.0 else 2.0
        except (ValueError, TypeError):
            return 2.0

    features = {
        "idade_anos":  idade_anos,
        "cs_sexo":     cs_sexo,
        "febre":       float(respostas.get("febre", "2")),
        "mialgia":     float(respostas.get("mialgia", "2")),
        "cefaleia":    float(respostas.get("cefaleia", "2")),
        "exantema":    float(respostas.get("exantema", "2")),
        "vomito":      float(respostas.get("vomito", "2")),
        "nausea":      float(respostas.get("nausea", "2")),
        "dor_costas":  float(respostas.get("dor_costas", "2")),
        "conjuntvit":  float(respostas.get("conjuntvit", "2")),
        "artrite":     float(respostas.get("artrite", "2")),
        "artralgia":   float(respostas.get("artralgia", "2")),
        "dor_retro":   float(respostas.get("dor_retro", "2")),
        "diabetes":    parse_comorb(comorbidades.get("diabetes")),
        "hematolog":   parse_comorb(comorbidades.get("hematolog")),
        "hepatopat":   parse_comorb(comorbidades.get("hepatopat")),
        "renal":       parse_comorb(comorbidades.get("renal")),
        "hipertensa":  parse_comorb(comorbidades.get("hipertensa")),
        "acido_pept":  parse_comorb(comorbidades.get("acido_pept")),
        "auto_imune":  parse_comorb(comorbidades.get("auto_imune")),
    }

    classificacao = predict_classification(features)
    
    # --- TRAVA DE SEGURANÇA MÁXIMA (Sinais de Alarme) ---
    dor_abd_val = respostas.get("dor_abd", "2")
    sangram_val = respostas.get("sangram", "2")
    letargia_val = respostas.get("letargia", "2")
    
    tem_sinal_alarme = "1" in [dor_abd_val, sangram_val, letargia_val]
    
    if tem_sinal_alarme:
        classificacao = "C"
        logger.warning(f"🚨 [Segurança] Paciente {paciente['id']} apresentou Sinais de Alarme! IA ignorada. Classificação travada em C.")
    
    logger.info(f"Triagem finalizada — paciente {paciente['id']} | classificação: {classificacao}")

    evolucao_detectada = False
    try:
        async with AsyncSessionLocal() as db:
            ultimo = await buscar_ultimo_atendimento(db, paciente['id'])
            if ultimo and ultimo.get('grupo_risco'):
                evolucao_detectada = detectar_evolucao(ultimo['grupo_risco'], classificacao)
    except Exception as e:
        logger.warning(f"Não foi possível verificar evolução: {e}")

    try:
        async with AsyncSessionLocal() as db:
            await salvar_atendimento(
                db=db,
                paciente_id=paciente['id'],  # Alinhado com a Chave Estrangeira correta na coluna 'id'
                dt_inicio=dt_inicio,
                dt_fim=dt_fim,
                febre=respostas.get("febre", "2"),
                mialgia=respostas.get("mialgia", "2"),
                cefaleia=respostas.get("cefaleia", "2"),
                exantema=respostas.get("exantema", "2"),
                vomito=respostas.get("vomito", "2"),
                nausea=respostas.get("nausea", "2"),
                dor_costas=str(respostas.get("dor_costas", "2")),
                conjuntvit=str(respostas.get("conjuntvit", "2")),
                artrite=str(respostas.get("artrite", "2")),
                artralgia=str(respostas.get("artralgia", "2")),
                dor_retro=str(respostas.get("dor_retro", "2")),
                dor_abd=str(dor_abd_val),
                sangram=str(sangram_val),
                letargia=str(letargia_val),
                grupo_risco=classificacao
            )
    except Exception as e:
        logger.error(f"Erro ao salvar atendimento: {e}")

    texto_resultado = RESPOSTAS_CLASSIFICACAO.get(classificacao, RESPOSTA_FALLBACK)

    if evolucao_detectada:
        texto_resultado = MENSAGEM_EVOLUCAO + texto_resultado

    for chave in ['triagem_index', 'triagem_inicio', 'triagem_respostas']:
        context.user_data.pop(chave, None)

    teclado_final = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="voltar_menu")]
    ])

    if update.callback_query:
        await update.callback_query.message.reply_text(
            f"✅ *Triagem concluída\\!*\n\n{texto_resultado}",
            parse_mode="MarkdownV2",
            reply_markup=teclado_final
        )
    else:
        await update.message.reply_text(
            f"✅ *Triagem concluída\\!*\n\n{texto_resultado}",
            parse_mode="MarkdownV2",
            reply_markup=teclado_final
        )

    return ConversationHandler.END


# ==========================================
# CALLBACK: Voltar ao menu principal
# ==========================================
async def callback_voltar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    paciente = context.user_data.get("paciente")
    if paciente:
        return await _exibir_menu_paciente(update, context, paciente)
    else:
        await query.edit_message_text("⚠️ Sessão expirada\\. Use /start para se identificar novamente\\.", parse_mode="MarkdownV2")
        return ConversationHandler.END

# Baixar cartilha
# ==========================================
# CALLBACK: Enviar Cartilha do Ministério da Saúde
# ==========================================
async def callback_baixar_cartilha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Feedback visual imediato para melhorar a UX
    mensagem_aguarde = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="⏳ *Aguarde um momento\\.\\.\\.* Baixando a cartilha oficial do Ministério da Saúde\\. Isso pode levar alguns segundos\\.",
        parse_mode="MarkdownV2"
    )

    # URL oficial do PDF do Ministério da Saúde (link direto)
    pdf_url = "https://www.ubec.edu.br/wp-content/uploads/2024/02/CARTILHA.pdf"

    caption = (
        "📚 *Dengue: Diagnóstico e Manejo Clínico*\n\n"
        "Aqui está o material oficial do Ministério da Saúde\\. "
        "Ele contém orientações valiosas sobre cuidados, hidratação e restrições médicas para o seu tratamento\\."
    )

    try:
        # Envia o documento aumentando os timeouts de rede
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf_url,
            caption=caption,
            parse_mode="MarkdownV2",
            read_timeout=60,   # Aumenta a tolerância de leitura para 60 segundos
            write_timeout=60
        )
        
        # Apaga a mensagem de "Aguarde" após o envio bem-sucedido do PDF
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=mensagem_aguarde.message_id
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar cartilha: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Não foi possível carregar o arquivo no momento\\. Tente novamente mais tarde\\.",
            parse_mode="MarkdownV2"
        )

    return ConversationHandler.END


# ==========================================
# FUNÇÃO AUXILIAR: Exibe o menu principal
# ==========================================
async def _exibir_menu_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE, paciente: dict) -> int:
    context.user_data["paciente"] = paciente

    dt_nasc = paciente.get("DT_NASCIMENTO")
    idade_texto = "Não informada"
    if dt_nasc:
        try:
            if isinstance(dt_nasc, date):
                hoje = date.today()
                idade = hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day))
                idade_texto = f"{idade} anos"
            elif isinstance(dt_nasc, str) and len(dt_nasc) >= 10:
                dt_objeto = datetime.strptime(dt_nasc[:10], "%Y-%m-%d").date()
                hoje = date.today()
                idade = hoje.year - dt_objeto.year - ((hoje.month, hoje.day) < (dt_objeto.month, dt_objeto.day))
                idade_texto = f"{idade} anos"
        except Exception as e:
            logger.warning(f"Erro ao calcular idade: {e}")

    sexo_raw = paciente.get("cs_sexo")
    sexo_mapa = {"M": "Masculino", "F": "Feminino"}
    sexo_texto = sexo_mapa.get(str(sexo_raw).upper(), "Não informado")

    keyboard = [
        [InlineKeyboardButton("📋 Registrar Triagem Diária", callback_data="acompanhamento")],
        [InlineKeyboardButton("📅 Ver Histórico de Atendimentos", callback_data="ver_historico")],
        [InlineKeyboardButton("📚 Guia Clínico - Ministério da Saúde", callback_data="baixar_cartilha")],
        [InlineKeyboardButton("⚙️ Atualizar Perfil de Saúde", callback_data="atualizar_dados")],
        [InlineKeyboardButton("🔄 Trocar Paciente", callback_data="trocar_paciente")],
    ]

    mensagem = (
        f"✅ *Paciente identificado\\!* \n\n"
        f"👤 *Nome:* {_escape_md(paciente.get('nm_usuario', 'Não informado'))}\n"
        f"🪪 *Carteira:* {_escape_md(str(paciente.get('nr_carteira', '---')))}\n"
        f"🎂 *Idade:* {_escape_md(idade_texto)}\n"
        f"🚻 *Sexo:* {_escape_md(sexo_texto)}\n\n"
        f"Olá, *{_escape_md(paciente.get('nm_usuario', 'Paciente'))}*\\! "
        f"Estou aqui para acompanhar sua recuperação\\.\n"
        f"Escolha uma opção abaixo:"
    )

    if update.message:
        await update.message.reply_text(mensagem, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(mensagem, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END


# ==========================================
# CALLBACKS: Histórico de Atendimentos
# ==========================================
async def callback_ver_historico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    paciente = context.user_data.get("paciente")
    if not paciente:
        await query.edit_message_text("⚠️ Sessão expirada\\. Use /start para se identificar novamente\\.", parse_mode="MarkdownV2")
        return ConversationHandler.END

    try:
        async with AsyncSessionLocal() as db:
            historico = await buscar_historico_atendimentos(db, paciente['id'], limite=5)
    except Exception as e:
        logger.error(f"Erro ao buscar historico: {e}")
        await query.edit_message_text("⚠️ Ocorreu um erro ao buscar o histórico\\.", parse_mode="MarkdownV2")
        return ConversationHandler.END

    if not historico:
        mensagem = "📅 *Histórico de Atendimentos*\n\nVocê ainda não possui nenhuma triagem registrada\\.\nUse a opção *Registrar Triagem Diária* no menu principal\\."
    else:
        mensagem = f"📅 *Últimos Atendimentos de {_escape_md(paciente.get('nm_usuario', 'Paciente'))}*\n\n"
        for reg in historico:
            data_formatada = reg['dt_fim'].strftime("%d/%m/%Y %H:%M") if reg.get('dt_fim') else "Desconhecido"
            risco = reg.get('grupo_risco', 'N/A')
            mensagem += f"🔹 *{_escape_md(data_formatada)}* \\- Risco: {risco}\n"
            
            sintomas_destaque = []
            if reg.get('febre') == '1' or reg.get('febre') == 1.0: sintomas_destaque.append('Febre')
            if reg.get('cefaleia') == '1' or reg.get('cefaleia') == 1.0: sintomas_destaque.append('Dor de Cabeça')
            if reg.get('mialgia') == '1' or reg.get('mialgia') == 1.0: sintomas_destaque.append('Dor no Corpo')
            
            sint_txt = ", ".join(sintomas_destaque) if sintomas_destaque else "Sem sintomas graves relatados"
            mensagem += f"  ↳ Sintomas: {_escape_md(sint_txt)}\n\n"

    teclado_final = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="voltar_menu")]
    ])

    await query.edit_message_text(mensagem, parse_mode="MarkdownV2", reply_markup=teclado_final)
    return ConversationHandler.END



# ==========================================
# CALLBACKS: Trocar paciente
# ==========================================
async def callback_trocar_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("paciente", None)
    await query.edit_message_text(
        "🔄 Certo\\! Digite o *número da carteira* do novo paciente:",
        parse_mode="MarkdownV2"
    )
    return AGUARDANDO_CARTEIRA


# ==========================================
# HANDLER: /cancelar
# ==========================================
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Operação cancelada. Use /start quando quiser retomar.")
    return ConversationHandler.END


# ==========================================
# UTILITÁRIO: Escape MarkdownV2
# ==========================================
def _escape_md(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for char in str(text):
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
            CallbackQueryHandler(callback_trocar_paciente, pattern="^trocar_paciente$"),
            CallbackQueryHandler(callback_atualizar_dados, pattern="^atualizar_dados$"),
            CallbackQueryHandler(callback_acompanhamento, pattern="^acompanhamento$"),
            CallbackQueryHandler(callback_ver_historico, pattern="^ver_historico$"),
            CallbackQueryHandler(callback_baixar_cartilha, pattern="^baixar_cartilha$"),
            CallbackQueryHandler(callback_voltar_menu, pattern="^voltar_menu$"),
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
            AGUARDANDO_DT_NASCIMENTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dt_nascimento)
            ],
            AGUARDANDO_SEXO: [
                CallbackQueryHandler(callback_sexo, pattern="^sexo_")
            ],
            AGUARDANDO_DIABETES:  [CallbackQueryHandler(callback_diabetes,  pattern="^diab_")],
            AGUARDANDO_HEMATOLOG: [CallbackQueryHandler(callback_hematolog, pattern="^hemato_")],
            AGUARDANDO_HEPATOPAT: [CallbackQueryHandler(callback_hepatopat, pattern="^hepato_")],
            AGUARDANDO_RENAL:     [CallbackQueryHandler(callback_renal,     pattern="^renal_")],
            AGUARDANDO_HIPERTENSA:[CallbackQueryHandler(callback_hipertensa,pattern="^hiper_")],
            AGUARDANDO_ACIDO_PEPT:[CallbackQueryHandler(callback_acido_pept,pattern="^acido_")],
            AGUARDANDO_AUTO_IMUNE:[CallbackQueryHandler(callback_auto_imune,pattern="^auto_")],
            AGUARDANDO_TELEFONE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telefone)],

            TRIAGEM_PERGUNTA: [
                CallbackQueryHandler(callback_triagem_resposta, pattern="^triagem_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", start_command),
        ],
    )