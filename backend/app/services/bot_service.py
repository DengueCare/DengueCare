# app/services/bot_service.py
"""
Serviço de interface conversacional e regras de negócio de triagem do bot.
Contém a parametrização das perguntas de acompanhamento, classificação de risco
e algoritmos para detecção de agravamento do quadro clínico.
"""

from typing import Dict, Tuple, List

# Estrutura: (chave_banco_dados, texto_da_pergunta, prefixo_callback)
# Importante: Escapes \\( e \\) adicionados para compatibilidade com MarkdownV2 do Telegram.
PERGUNTAS_TRIAGEM: List[Tuple[str, str, str]] = [
    ("febre", "🌡️ Você apresentou *febre* hoje ou nos últimos dias?", "febre"),
    ("mialgia", "💪 Você está sentindo *dor muscular* \\(mialgia\\)?", "mialgia"),
    ("cefaleia", "🤕 Você está com *dor de cabeça* \\(cefaleia\\)?", "cefaleia"),
    ("exantema", "🔴 Você notou o aparecimento de *manchas ou erupções vermelhas* na pele \\(exantema\\)?", "exantema"),
    ("vomito", "🤢 Você teve episódios de *vômito*?", "vomito"),
    ("nausea", "🤢 Você está sentindo *enjoo ou náuseas*?", "nausea"),
    ("dor_costas", "🦴 Você está sentindo *dor nas costas*?", "dor_costas"),
    ("conjuntvit", "👁️ Seus olhos estão vermelhos ou irritados, semelhante a uma *conjuntivite*?", "conjuntvit"),
    ("artralgia", "🦴 Você está sentindo *dor nas articulações* \\(nas juntas\\)?", "artralgia"),
    ("artrite", "🦵 Você notou *inchaço ou inflamação* nas articulações \\(artrite\\)?", "artrite"),
    ("dor_retro", "👀 Você está sentindo *dor atrás dos olhos*?", "dor_retro"),
    # --- Sinais de Alarme (Protocolo MS) ---
    ("dor_abd", "😣 Você está sentindo *dor abdominal intensa e contínua*?", "dor_abd"),
    ("sangram", "🩸 Você notou algum tipo de *sangramento* \\(ex: nariz, gengiva, manchas roxas na pele\\)?", "sangram"),
    ("letargia", "😴 Você está se sentindo excessivamente *sonolento, confuso ou irritado* \\(letargia/irritabilidade\\)?", "letargia"),
]

# Mensagens dinâmicas ajustadas rigorosamente para o MarkdownV2 do Telegram
RESPOSTAS_CLASSIFICACAO: Dict[str, str] = {
    "A": (
        "Tudo indica que você está com um *quadro leve*\\.\n\n"
        "💧 *O que fazer:* O mais importante agora é manter o repouso e iniciar uma "
        "*hidratação intensa* \\(beba muita água, soro caseiro ou água de coco\\)\\. "
        "Continue monitorando seus sintomas diariamente pelo nosso aplicativo e evite automedicação "
        "\\(não tome anti\\-inflamatórios como ibuprofeno ou aspirina\\)\\.\n\n"
        "_Se notar dor abdominal forte ou qualquer sangramento, procure um médico\\._"
    ),
    "B": (
        "Seus sintomas indicam um *quadro moderado* que exige um pouco mais de atenção\\.\n\n"
        "🩺 *O que fazer:* É altamente recomendável que você procure um *posto de saúde ou atendimento "
        "médico* para avaliação clínica e possível realização de exames laboratoriais \\(hemograma\\)\\. "
        "Mantenha a hidratação constante e fique atento a sinais de piora\\."
    ),
    "C": (
        "Atenção\\! Você apresenta sintomas que são considerados *sinais de alarme*\\.\n\n"
        "🚨 *O que fazer:* Procure uma *Unidade de Pronto Atendimento \\(UPA\\) ou hospital IMEDIATAMENTE*\\. "
        "A avaliação médica rápida é crucial para estabilizar seu quadro, ajustar a hidratação via soro "
        "e evitar complicações graves\\. Não adie a ida ao hospital\\!"
    ),
    "D": (
        "ALERTA VERMELHO\\! Seus sintomas indicam um *quadro grave*\\.\n\n"
        "🚑 *O que fazer:* Dirija\\-se *AGORA MESMO para a emergência* do hospital mais próximo\\. "
        "Sua condição de saúde requer hidratação intravenosa imediata e acompanhamento médico intensivo "
        "com urgência\\."
    )
}

RESPOSTA_FALLBACK: str = (
    "Não foi possível processar seu risco com precisão no momento\\.\n\n"
    "⚠️ *Recomendação:* Em caso de dúvida sobre a gravidade dos seus sintomas, "
    "mantenha\\-se hidratado e busque a avaliação presencial de um médico\\."
)

MENSAGEM_EVOLUCAO: str = (
    "⚠️ *Alerta do Sistema:* Notamos que os seus sintomas pioraram ou evoluíram em relação "
    "à sua última triagem\\.\n\n"
)

def detectar_evolucao(risco_anterior: str, risco_atual: str) -> bool:
    """
    Algoritmo de inferência cronológica para detectar agravamento no quadro de saúde.
    Retorna True se o paciente subiu de classificação de risco em relação à triagem anterior.
    """
    mapa_gravidade = {"A": 1, "B": 2, "C": 3, "D": 4}

    try:
        nivel_ant = mapa_gravidade.get(risco_anterior.upper(), 0)
        nivel_atual = mapa_gravidade.get(risco_atual.upper(), 0)
        
        # Só há inferência de piora se já havia um quadro válido registrado anteriormente.
        if nivel_ant == 0:
            return False

        return nivel_atual > nivel_ant
    except Exception:
        # Failsafe: Se houver anomalia nos dados lidos, silencia o alerta de agravamento
        return False