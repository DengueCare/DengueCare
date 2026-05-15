"""
Serviço de inferência do modelo de Machine Learning de Dengue

O modelo é carregado uma única vez na memória quando o servidor sobe (padrão Singleton), evitando
leitura de disco a cada predição
"""

import pickle
import logging
import os

logger = logging.getLogger("denguecare.ml")

FEATURE_NAMES = [
    "idade_anos", "cs_sexo",
    "febre", "mialgia", "cefaleia", "exantema", "vomito", "nausea",
    "dor_costas", "conjuntvit", "artrite", "artralgia", "dor_retro",
    "diabetes", "hematolog", "hepatopat", "renal", "hipertensa",
    "acido_pept", "auto_imune",
]

_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "modelos_ml", "modelo_dengue_v1.pkl"
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
    logger.error("    Coloque o arquivo em backend/modelos_ml/modelo_dengue_v1.pkl")
except Exception as e:
    logger.error(f"❌ [ML] Erro ao carregar o modelo: {e}")

def predict_classification(features: dict) -> str:
    """
    Realiza a predição do quadro clínico do paciente
    """
    if _model is None:
        logger.warning("⚠️ [ML] Modelo não disponível - retornando 'C' por segurança")
        return "C"

    try:
        # Monta o vetor na ordem exata que o modelo espera
        vetor = [[features[nome] for nome in FEATURE_NAMES]]
        resultado = _model.predict(vetor)
        classificacao = str(resultado[0])
        logger.info(f"🤖 [ML] Predição: {classificacao} | Input: {vetor[0]}")
        return classificacao
    
    except KeyError as e:
        logger.error(f"❌ [ML] Feature ausente no dicionário: {e}")
        return "C"
    except Exception as e:
        logger.error(f"❌ [ML] Erro na predição: {e}")
        return "C"

def predict_risk_score(features_array: list) -> str:
    """
    Wrapper legado — aceita lista/matriz como o código antigo esperava.
    Preferir predict_classification() para novos desenvolvimentos.
    """
    if _model is None:
        logger.warning("⚠️ [ML] Modelo não disponível - retornando 'C' por segurança")
        return "C"

    try:
        resultado = _model.predict(features_array)
        return str(resultado[0])
    except Exception as e:
        logger.error(f"❌ [ML] Erro na predição (legado): {e}")
        return "C"