from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    telefone: str = Field(..., description="Identificador único do paciente (telefone ou ID)")
    mensagem: str = Field(..., description="Mensagem enviada pelo paciente no chat")

class ChatResponse(BaseModel):
    status: str = Field(..., description="Status do processamento (success, error)")
    reply: str = Field(..., description="Mensagem que o bot responderá no chat")
    risk_group: Optional[str] = Field(None, description="Grupo de risco classificado (A, B, C, D)")
    requires_action: bool = Field(False, description="Flag (true/false) se o front-end deve disparar alerta vermelho")