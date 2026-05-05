from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db

router = APIRouter()

@router.get("/")
async def get_all_patients(db: AsyncSession = Depends(get_db)):
    """
    Busca todos os pacientes/usuários cadastrados no banco de dados.
    Utiliza conexão assíncrona do pool do SQLAlchemy.
    """
    try:
        # Executa a query de forma não-bloqueante
        # Se a tabela no Supabase estiver como 'usuario', troque a palavra abaixo.
        result = await db.execute(text("SELECT * FROM paciente"))
        
        # Extrai todas as linhas retornadas
        pacientes = result.fetchall()
        
        # Mapeia os resultados para uma lista de dicionários compatível com JSON
        formatted_data = [dict(row._mapping) for row in pacientes]
        
        return {
            "status": "success",
            "count": len(formatted_data),
            "data": formatted_data
        }
        
    except Exception as e:
        # Captura e formata erros de sintaxe SQL ou falha de tabela ausente
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao consultar o banco de dados: {str(e)}"
        )