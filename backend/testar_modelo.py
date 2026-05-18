# testar_modelo.py
"""
Script simples para testar se o modelo está sendo carregado
e classificando corretamente, SEM precisar subir o bot.

Execução: python testar_modelo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from app.services.ml_service import predict_classification, FEATURE_NAMES

print("\n" + "="*55)
print("  TESTE DO MODELO ML — DengueCare")
print("="*55)
print(f"\nFeatures esperadas ({len(FEATURE_NAMES)}):")
for i, nome in enumerate(FEATURE_NAMES, 1):
    print(f"  {i:2}. {nome}")

# ==========================================
# CASOS DE TESTE
# Convenção: 1=Sim, 2=Não | cs_sexo: 1=M, 0=F
# ==========================================
casos = [
    {
        "nome": "Paciente A — Dengue leve, sem alarme",
        "features": {
            "idade_anos": 30.0, "cs_sexo": 1,
            "febre": 1, "mialgia": 1, "cefaleia": 1, "exantema": 2,
            "vomito": 2, "nausea": 1, "dor_costas": 1, "conjuntvit": 2,
            "artrite": 2, "artralgia": 2, "dor_retro": 1,
            "diabetes": 2, "hematolog": 2, "hepatopat": 2, "renal": 2,
            "hipertensa": 2, "acido_pept": 2, "auto_imune": 2,
        },
        "esperado": "A",
    },
    {
        "nome": "Paciente B — Com comorbidade (diabetes)",
        "features": {
            "idade_anos": 55.0, "cs_sexo": 0,
            "febre": 1, "mialgia": 1, "cefaleia": 2, "exantema": 2,
            "vomito": 2, "nausea": 2, "dor_costas": 2, "conjuntvit": 2,
            "artrite": 2, "artralgia": 2, "dor_retro": 2,
            "diabetes": 1, "hematolog": 2, "hepatopat": 2, "renal": 2,
            "hipertensa": 1, "acido_pept": 2, "auto_imune": 2,
        },
        "esperado": "B",
    },
    {
        "nome": "Paciente C/D — Sinais graves (vômito, dor abdominal)",
        "features": {
            "idade_anos": 42.0, "cs_sexo": 1,
            "febre": 1, "mialgia": 1, "cefaleia": 1, "exantema": 1,
            "vomito": 1, "nausea": 1, "dor_costas": 1, "conjuntvit": 2,
            "artrite": 2, "artralgia": 1, "dor_retro": 1,
            "diabetes": 2, "hematolog": 2, "hepatopat": 2, "renal": 2,
            "hipertensa": 2, "acido_pept": 2, "auto_imune": 2,
        },
        "esperado": "C ou D",
    },
    {
        "nome": "Paciente D — Sinais muito graves",
        "features": {
            "idade_anos": 42.0, "cs_sexo": 1,
            "febre": 1, "mialgia": 1, "cefaleia": 1, "exantema": 1,
            "vomito": 1, "nausea": 1, "dor_costas": 1, "conjuntvit": 2,
            "artrite": 2, "artralgia": 1, "dor_retro": 1,
            "diabetes": 2, "hematolog": 2, "hepatopat": 1, "renal": 1,
            "hipertensa": 1, "acido_pept": 2, "auto_imune": 1,
        },
        "esperado": "D",
    },
]

print("\n" + "-"*55)
print("RESULTADOS:")
print("-"*55)

todos_ok = True
for caso in casos:
    resultado = predict_classification(caso["features"])
    esperado = caso["esperado"]
    # Verifica se o resultado bate com o esperado (ou range)
    ok = resultado in esperado
    status = "✅" if ok else "⚠️ "
    if not ok:
        todos_ok = False
    print(f"\n{status} {caso['nome']}")
    print(f"   Esperado: {esperado} | Obtido: {resultado}")

print("\n" + "="*55)
if todos_ok:
    print("✅ MODELO OK — Pronto para integrar ao bot!")
else:
    print("⚠️  Alguns resultados divergiram do esperado.")
    print("   Isso pode ser normal dependendo dos dados de treino.")
    print("   Verifique se faz sentido clinicamente.")
print("="*55 + "\n")