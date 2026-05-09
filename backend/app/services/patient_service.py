# app/services/patient_service.py
"""
Camada de Serviço — Lógica de negócios para pacientes.
Encapsula todas as consultas ao Supabase/PostgreSQL relacionadas à tabela 'paciente'.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def buscar_paciente_por_carteira(db: AsyncSession, nr_carteira: str) -> dict | None:
    """
    Busca um paciente no Supabase pela coluna 'nr_carteira'.
    
    Args:
        db: Sessão assíncrona do SQLAlchemy conectada ao Supabase.
        nr_carteira: Número da carteira informado pelo usuário no Telegram.
    
    Returns:
        Dicionário com os dados do paciente (id, nome, nr_carteira) ou None se não encontrado.
    """
    try:
        result = await db.execute(
            text("SELECT id, nm_usuario, nr_carteira FROM paciente WHERE nr_carteira = :nr"),
            {"nr": nr_carteira}
        )
        row = result.fetchone()
        
        if row:
            paciente = dict(row._mapping)
            logger.info(f"Paciente encontrado: {paciente['nm_usuario']} (carteira: {nr_carteira})")
            return paciente
        
        logger.info(f"Nenhum paciente encontrado com carteira: {nr_carteira}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao consultar paciente por carteira '{nr_carteira}': {e}")
        raise


async def criar_paciente(db: AsyncSession, nm_usuario: str, nr_carteira: str) -> dict:
    """
    Insere um novo paciente no banco de dados.
    """
    try:
        # A coluna nr_carteira é numeric no banco
        result = await db.execute(
            text(
                "INSERT INTO paciente (nm_usuario, nr_carteira) "
                "VALUES (:nm, :nr) RETURNING id, nm_usuario, nr_carteira"
            ),
            {"nm": nm_usuario, "nr": float(nr_carteira)}
        )
        await db.commit()
        row = result.fetchone()
        paciente = dict(row._mapping)
        logger.info(f"Novo paciente criado: {paciente['nm_usuario']} (carteira: {paciente['nr_carteira']})")
        return paciente
    except Exception as e:
        await db.rollback()
        logger.error(f"Erro ao criar paciente '{nm_usuario}': {e}")
        raise


async def listar_todos_pacientes(db: AsyncSession) -> list[dict]:
    """
    Retorna todos os pacientes cadastrados no Supabase.
    Útil para listagens e estatísticas no bot.
    """
    try:
        result = await db.execute(text("SELECT id, nm_usuario, nr_carteira FROM paciente"))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error(f"Erro ao listar pacientes: {e}")
        raise
