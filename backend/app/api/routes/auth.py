from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.services.auth_service import registrar_profissional, autenticar_profissional

router = APIRouter()

class RegisterRequest(BaseModel):
    nome: str
    carteira: str
    senha: str

class LoginRequest(BaseModel):
    carteira: str
    senha: str

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        if not req.nome or not req.carteira or not req.senha:
            raise ValueError("Nome, carteira e senha são obrigatórios.")
            
        prof = await registrar_profissional(db, req.nome, req.carteira, req.senha)
        return {"success": True, "message": "Usuário criado com sucesso", "data": prof}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao registrar usuário.")

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        prof = await autenticar_profissional(db, req.carteira, req.senha)
        if prof:
            return {"success": True, "message": "Login efetuado com sucesso", "data": prof}
        else:
            raise HTTPException(status_code=401, detail="Carteira ou senha incorretos.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao efetuar login.")
