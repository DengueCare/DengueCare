# app/services/ml_service.py

# import joblib  <-- Descomente isso quando for usar o seu modelo .pkl salvo

# Carregamento em memória (Singleton) do modelo real
# try:
#     model = joblib.load("models_ml/meu_modelo_random_forest.pkl")
# except Exception as e:
#     print(f"Aviso: Modelo não encontrado. {e}")
#     model = None

def predict_risk_score(features_array: list) -> str:
    """
    Motor de inferência real (Síncrono).
    Recebe a matriz de features do chat e retorna a classificação de risco.
    """
    try:
        # ==========================================
        # CÓDIGO DE PRODUÇÃO (Descomente quando o modelo estiver treinado)
        # ==========================================
        # if model:
        #     prediction = model.predict(features_array)
        #     return prediction[0] 
        
        # ==========================================
        # LÓGICA DE INTEGRAÇÃO (Fallback Temporário)
        # ==========================================
        # Pega a última resposta digitada pelo usuário na matriz [5, 1, 0, 0, user_input]
        user_input = features_array[0][-1] 
        
        # Simulador baseado em regras simples para o Front-end poder reagir aos testes
        if user_input in [1, 2]:
            return "A" # Risco Baixo
        elif user_input in [3, 4]:
            return "B" # Risco Moderado
        else:
            return "C" # Risco Alto (Aciona o alerta vermelho na UI)

    except Exception as e:
        print(f"Erro no processamento da IA: {e}")
        # Em caso de falha matemática, assume o pior cenário por segurança médica
        return "C"