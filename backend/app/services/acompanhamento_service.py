# app/services/acompanhamento_service.py
"""
Camada de Serviço — Lógica de negócios para acompanhamento diário.
Encapsula as consultas ao banco para registrar e listar os sintomas.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def criar_acompanhamento(db: AsyncSession, paciente_id: int, sintomas: str) -> dict:
    """
    Insere um novo registro de acompanhamento diário no banco.
    """
    try:
        result = await db.execute(
            text(
                "INSERT INTO acompanhamento (paciente_id, sintomas) "
                "VALUES (:p_id, :sint) RETURNING id, paciente_id, sintomas, data_registro"
            ),
            {"p_id": paciente_id, "sint": sintomas}
        )
        await db.commit()
        row = result.fetchone()
        registro = dict(row._mapping)
        logger.info(f"Acompanhamento registrado com sucesso para paciente {paciente_id}")
        return registro
    except Exception as e:
        await db.rollback()
        logger.error(f"Erro ao criar acompanhamento para paciente {paciente_id}: {e}")
        raise


async def buscar_historico_paciente(db: AsyncSession, paciente_id: int, limite: int = 10) -> list[dict]:
    """
    Busca o histórico recente de acompanhamentos de um paciente.
    """
    try:
        result = await db.execute(
            text(
                "SELECT id, paciente_id, sintomas, data_registro "
                "FROM acompanhamento "
                "WHERE paciente_id = :p_id "
                "ORDER BY data_registro DESC "
                "LIMIT :lim"
            ),
            {"p_id": paciente_id, "lim": limite}
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error(f"Erro ao buscar histórico do paciente {paciente_id}: {e}")
        raise
