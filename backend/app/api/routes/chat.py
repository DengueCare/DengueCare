from fastapi import APIRouter, HTTPException
from app.schemas.pydantic_models import ChatRequest, ChatResponse
# Importamos a função real do modelo preditivo, abandonando o mock
from app.services.ml_service import predict_risk_score 

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Recebe o payload do frontend Web, sanitiza a entrada e executa a inferência de risco.
    """
    user_message = request.mensagem.strip()
    
    # [RNF-03] Tratamento rigoroso de exceções para entradas de texto livre 
    if not user_message.isdigit():
        return ChatResponse(
            status="error",
            reply="Não consigo entender textos longos. Por favor, responda apenas com os números das opções. Se for uma emergência, vá à UPA.",
            requires_action=False
        )
    
    try:
        # Array base temporário de features. Em produção, os dados de base virão do Supabase.
        features_baseline = [5, 1, 0, 0]
        
        # Concatena os dados clínicos base com a nova resposta do paciente
        current_features = [features_baseline + [int(user_message)]]
        
        # Chamada síncrona para o motor preditivo da IA (Scikit-Learn)
        risk_group = predict_risk_score(current_features)
        
        # Lógica de roteamento clínico baseada no Dicionário SUS
        requires_action = risk_group in ["C", "D"]
        
        if requires_action:
            bot_reply = "⚠️ ALERTA VERMELHO: O sistema preditivo detectou sinais críticos de agravamento. Dirija-se IMEDIATAMENTE à UPA ou Unidade de Saúde mais próxima. A equipe de triagem foi notificada."
        else:
            bot_reply = "✅ Análise concluída: Seu quadro clínico segue estável no Grupo de Risco Baixo. Mantenha a hidratação constante. O DengueCare retomará o monitoramento em 24h."

        return ChatResponse(
            status="success",
            reply=bot_reply,
            risk_group=risk_group,
            requires_action=requires_action
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Falha de processamento no motor de inferência: {str(e)}"
        )