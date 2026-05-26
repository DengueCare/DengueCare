from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.services.auth_service import (
    registrar_profissional,
    autenticar_profissional,
    atualizar_profissional,
    inativar_profissional,
    listar_todos_profissionais,
    reativar_profissional,
    toggle_admin_profissional
)

router = APIRouter()

class RegisterRequest(BaseModel):
    nome: str
    carteira: str
    senha: str

class LoginRequest(BaseModel):
    carteira: str
    senha: str

class UpdateProfileRequest(BaseModel):
    carteira: str
    nome: str = None
    senha: str = None
    ubs: str = None

class InactivateRequest(BaseModel):
    carteira: str

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
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao efetuar login.")

@router.put("/update")
async def update_profile(req: UpdateProfileRequest, db: AsyncSession = Depends(get_db)):
    try:
        prof = await atualizar_profissional(db, req.carteira, novo_nome=req.nome, nova_senha=req.senha, nova_ubs=req.ubs)
        if prof:
            return {"success": True, "message": "Perfil atualizado com sucesso", "data": prof}
        else:
            raise HTTPException(status_code=404, detail="Profissional não encontrado.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar perfil.")

@router.patch("/inactivate")
async def inactivate_profile(req: InactivateRequest, db: AsyncSession = Depends(get_db)):
    try:
        success = await inativar_profissional(db, req.carteira)
        if success:
            return {"success": True, "message": "Perfil inativado com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Profissional não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao inativar perfil.")

@router.get("/professionals")
async def get_all_professionals(db: AsyncSession = Depends(get_db)):
    try:
        profs = await listar_todos_profissionais(db)
        return {"success": True, "data": profs}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao listar profissionais.")

@router.patch("/professionals/{carteira}/reactivate")
async def reactivate_professional(carteira: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await reativar_profissional(db, carteira)
        if success:
            return {"success": True, "message": "Profissional reativado com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Profissional não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao reativar profissional.")

@router.patch("/professionals/{carteira}/toggle-admin")
async def toggle_admin(carteira: str, db: AsyncSession = Depends(get_db)):
    try:
        prof = await toggle_admin_profissional(db, carteira)
        if prof:
            return {"success": True, "message": "Permissão de administrador alterada", "data": prof}
        else:
            raise HTTPException(status_code=404, detail="Profissional não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao alterar permissão do profissional.")
