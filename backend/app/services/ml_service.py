# app/services/ml_service.py
"""
Serviço de inferência do modelo de Machine Learning de Dengue.

O modelo é carregado UMA ÚNICA VEZ na memória quando o servidor sobe
(padrão Singleton), evitando leitura de disco a cada predição.

Features esperadas pelo modelo (ordem obrigatória — 20 features):
    idade_anos, cs_sexo,
    febre, mialgia, cefaleia, exantema, vomito, nausea,
    dor_costas, conjuntvit, artrite, artralgia, dor_retro,
    diabetes, hematolog, hepatopat, renal, hipertensa, acido_pept, auto_imune

Convenções dos valores (conforme treinamento):
    - Sintomas/Comorbidades: 1 = Sim, 2 = Não (padrão SINAN)
    - cs_sexo: 1 = Masculino, 0 = Feminino, -1 = Ignorado
    - idade_anos: número real em anos (ex: 35.0)

Retorno: 'A', 'B', 'C' ou 'D'
    A = Sem sinais de alarme
    B = Com comorbidades / grupo de risco
    C = Com sinais de alarme
    D = Com sinais de choque / gravidade máxima
"""

import pickle
import logging
import os
import pandas as pd

logger = logging.getLogger("denguecare.ml")

# ==========================================
# ORDEM EXATA DAS FEATURES (conforme treinamento)
# Use isso como referência ao montar o vetor de entrada
# ==========================================
FEATURE_NAMES = [
    "idade_anos", "cs_sexo",
    "febre", "mialgia", "cefaleia", "exantema", "vomito", "nausea",
    "dor_costas", "conjuntvit", "artrite", "artralgia", "dor_retro",
    "diabetes", "hematolog", "hepatopat", "renal", "hipertensa",
    "acido_pept", "auto_imune",
]

# ==========================================
# CARREGAMENTO SINGLETON DO MODELO
# Executado uma única vez no import do módulo
# ==========================================
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # .../app/services/
    "..", "..", "modelos_ml", "modelo_dengue_v1.pkl"  # .../models_ml/
)
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

_model = None

try:
    with open(_MODEL_PATH, "rb") as f:
        _model = pickle.load(f)
    logger.info(f"✅ [ML] Modelo carregado com sucesso: {_MODEL_PATH}")
    logger.info(f"   Classes: {_model.classes_} | Features: {len(FEATURE_NAMES)}")
except FileNotFoundError:
    logger.error(f"❌ [ML] Arquivo do modelo não encontrado: {_MODEL_PATH}")
    logger.error("   Coloque o arquivo em backend/models_ml/modelo_dengue_v1.pkl")
except Exception as e:
    logger.error(f"❌ [ML] Erro ao carregar o modelo: {e}")


# ==========================================
# FUNÇÃO PRINCIPAL DE PREDIÇÃO
# ==========================================
def predict_classification(features: dict) -> str:
    """
    Realiza a predição do quadro clínico do paciente.
    """
    if _model is None:
        logger.warning("⚠️  [ML] Modelo não disponível — retornando 'C' por segurança.")
        return "C"

    try:
        # Monta o DataFrame na ordem exata que o modelo espera
        vetor = pd.DataFrame([features], columns=FEATURE_NAMES)
        resultado = _model.predict(vetor)
        classificacao = str(resultado[0])
        
        # CORREÇÃO: Usa o dicionário 'features' no log em vez do 'vetor[0]' do Pandas
        logger.info(f"🤖 [ML] Predição real do modelo: {classificacao} | Input: {features}")
        
        return classificacao

    except KeyError as e:
        logger.error(f"❌ [ML] Feature ausente no dicionário: {e}")
        return "C"
    except Exception as e:
        logger.error(f"❌ [ML] Erro na predição: {e}")
        return "C"

# ==========================================
# FUNÇÃO LEGADA (compatibilidade com o bot_service.py existente)
# Mantida para não quebrar código que já usa predict_risk_score
# ==========================================
def predict_risk_score(features_array: list) -> str:
    """
    Wrapper legado — aceita lista/matriz como o código antigo esperava.
    Preferir predict_classification() para novos desenvolvimentos.
    """
    if _model is None:
        logger.warning("⚠️  [ML] Modelo não disponível — retornando 'C' por segurança.")
        return "C"

    try:
        resultado = _model.predict(features_array)
        return str(resultado[0])
    except Exception as e:
        logger.error(f"❌ [ML] Erro na predição (legado): {e}")
        return "C"