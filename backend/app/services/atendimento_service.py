# app/services/atendimento_service.py
"""
Camada de Serviço — Lógica de negócios para atendimentos e triagens.
Gerencia as operações no banco de dados para a tabela 'atendimento_paciente'.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

logger = logging.getLogger(__name__)

async def salvar_atendimento(
    db: AsyncSession,
    paciente_id: int, # Mapeia para a coluna 'id' (chave estrangeira)
    dt_inicio: datetime,
    dt_fim: datetime,
    febre: str,
    mialgia: str,
    cefaleia: str,
    exantema: str,
    vomito: str,
    nausea: str,
    dor_costas: str,
    conjuntvit: str,
    artrite: str,
    artralgia: str,
    dor_retro: str,
    dor_abd: str,
    sangram: str,
    letargia: str,
    grupo_risco: str
) -> dict:
    """
    Insere uma nova triagem. A coluna 'id' recebe o ID do paciente.
    A coluna 'nr_atendimento' é gerada automaticamente pelo banco.
    """
    try:
        result = await db.execute(
            text(
                """
                INSERT INTO atendimento_paciente (
                    id, dt_inicio, dt_fim, 
                    febre, mialgia, cefaleia, exantema, vomito, nausea, 
                    dor_costas, conjuntvit, artrite, artralgia, dor_retro, 
                    dor_abd, sangram, letargia,
                    grupo_risco
                ) 
                VALUES (
                    :paciente_id, :inicio, :fim, 
                    :febre, :mialgia, :cefaleia, :exantema, :vomito, :nausea, 
                    :dor_costas, :conjuntvit, :artrite, :artralgia, :dor_retro, 
                    :dor_abd, :sangram, :letargia,
                    :risco
                ) 
                RETURNING nr_atendimento, id, grupo_risco, dt_fim
                """
            ),
            {
                "paciente_id": paciente_id,
                "inicio": dt_inicio,
                "fim": dt_fim,
                "febre": febre,
                "mialgia": mialgia,
                "cefaleia": cefaleia,
                "exantema": exantema,
                "vomito": vomito,
                "nausea": nausea,
                "dor_costas": dor_costas,
                "conjuntvit": conjuntvit,
                "artrite": artrite,
                "artralgia": artralgia,
                "dor_retro": dor_retro,
                "dor_abd": dor_abd,
                "sangram": sangram,
                "letargia": letargia,
                "risco": grupo_risco
            }
        )
        await db.commit()
        row = result.fetchone()
        
        atendimento = dict(row._mapping) if row else {}
        logger.info(f"✅ Triagem salva. Atendimento Nº: {atendimento.get('nr_atendimento')} | Paciente ID: {paciente_id}")
        return atendimento

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Erro ao salvar atendimento do paciente '{paciente_id}': {e}")
        raise


async def buscar_ultimo_atendimento(db: AsyncSession, paciente_id: int) -> dict | None:
    """
    Busca a última triagem filtrando pela coluna 'id' (ID do paciente).
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT nr_atendimento, grupo_risco, dt_fim 
                FROM atendimento_paciente 
                WHERE id = :paciente_id 
                ORDER BY dt_fim DESC 
                LIMIT 1
                """
            ),
            {"paciente_id": paciente_id}
        )
        row = result.fetchone()
        
        if row:
            return dict(row._mapping)
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar último atendimento do paciente '{paciente_id}': {e}")
        return None


async def buscar_historico_atendimentos(db: AsyncSession, paciente_id: int, limite: int = 5) -> list[dict]:
    """
    Busca os últimos atendimentos (triagens) de um paciente para exibir no histórico.
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT nr_atendimento, dt_fim, grupo_risco,
                       febre, cefaleia, mialgia
                FROM atendimento_paciente 
                WHERE id = :paciente_id 
                ORDER BY dt_fim DESC 
                LIMIT :lim
                """
            ),
            {"paciente_id": paciente_id, "lim": limite}
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error(f"❌ Erro ao buscar histórico de atendimentos do paciente '{paciente_id}': {e}")
        return []