from fastapi import APIRouter, HTTPException
from app.schemas.pydantic_models import ChatRequest, ChatResponse
from app.services.ml_service import predict_risk_score_mock # <-- Import atualizado

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Recebe a mensagem do frontend Web, valida as respostas estruturadas e executa a IA.
    """
    user_message = request.mensagem.strip()
    
    if not user_message.isdigit():
        return ChatResponse(
            status="error",
            reply="Não consigo entender textos longos. Por favor, digite apenas o número da opção desejada. Se for uma emergência, vá à UPA.",
            requires_action=False
        )
    
    try:
        features_baseline = [5, 1, 0, 0]
        current_features = [features_baseline + [int(user_message)]]
        
        # Chamada atualizada para o mock assíncrono do teste de carga
        risk_group = await predict_risk_score_mock(current_features)
        
        requires_action = risk_group in ["C", "D"]
        if requires_action:
            bot_reply = "⚠️ Alerta Médico: O sistema detectou sinais de alarme. Por favor, dirija-se IMEDIATAMENTE à UPA ou Unidade de Saúde mais próxima."
        else:
            bot_reply = "Obrigado por informar. Seu quadro está estável. Lembre-se de manter a hidratação constante."

        return ChatResponse(
            status="success",
            reply=bot_reply,
            risk_group=risk_group,
            requires_action=requires_action
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao processar predição.")