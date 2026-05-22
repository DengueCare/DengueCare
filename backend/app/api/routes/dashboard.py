from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db

router = APIRouter()

@router.get("/")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """
    Retorna métricas consolidadas em tempo real do banco de dados para os cards do topo do Dashboard.
    """
    try:
        # 1. Total de Pacientes cadastrados no banco
        res_total = await db.execute(text("SELECT COUNT(*) FROM paciente"))
        total_pacientes = res_total.scalar() or 0
        
        # 2. Pacientes em Alto Risco hoje (última triagem classificada como C ou D)
        query_alto_risco_hoje = """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT ON (id) grupo_risco
                FROM atendimento_paciente
                ORDER BY id, nr_atendimento DESC
            ) latests WHERE grupo_risco IN ('C', 'D')
        """
        res_alto_hoje = await db.execute(text(query_alto_risco_hoje))
        alto_risco_hoje = res_alto_hoje.scalar() or 0
        
        # 2.1 Pacientes em Alto Risco até ontem
        query_alto_risco_ontem = """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT ON (id) grupo_risco
                FROM atendimento_paciente
                WHERE dt_inicio <= CURRENT_DATE - 1
                ORDER BY id, nr_atendimento DESC
            ) latests WHERE grupo_risco IN ('C', 'D')
        """
        res_alto_ontem = await db.execute(text(query_alto_risco_ontem))
        alto_risco_ontem = res_alto_ontem.scalar() or 0
        
        alto_risco_delta = alto_risco_hoje - alto_risco_ontem
        
        # 3. Admissões de Hoje (novos pacientes cadastrados/triados hoje)
        query_admissoes_hoje = """
            SELECT COUNT(*) FROM (
                SELECT p.id, COALESCE(CAST(MIN(ap.dt_inicio) AS DATE), CURRENT_DATE) as dt
                FROM paciente p
                LEFT JOIN atendimento_paciente ap ON p.id = ap.id
                GROUP BY p.id
            ) registrations WHERE dt = CURRENT_DATE
        """
        res_hoje = await db.execute(text(query_admissoes_hoje))
        admissoes_hoje = res_hoje.scalar() or 0
        
        # 3.1 Admissões de Ontem (para calcular variação)
        query_admissoes_ontem = """
            SELECT COUNT(*) FROM (
                SELECT p.id, COALESCE(CAST(MIN(ap.dt_inicio) AS DATE), CURRENT_DATE) as dt
                FROM paciente p
                LEFT JOIN atendimento_paciente ap ON p.id = ap.id
                GROUP BY p.id
            ) registrations WHERE dt = CURRENT_DATE - 1
        """
        res_ontem = await db.execute(text(query_admissoes_ontem))
        admissoes_ontem = res_ontem.scalar() or 0
        
        admissoes_delta = admissoes_hoje - admissoes_ontem
        
        return {
            "status": "success",
            "data": {
                "total_pacientes": total_pacientes,
                "alto_risco": alto_risco_hoje,
                "alto_risco_delta": alto_risco_delta,
                "admissoes_hoje": admissoes_hoje,
                "admissoes_delta": admissoes_delta
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular estatísticas do painel: {str(e)}"
        )

@router.get("/reports")
async def get_dashboard_reports(db: AsyncSession = Depends(get_db)):
    """
    Retorna dados consolidados para os relatórios clínicos e epidemiológicos.
    """
    try:
        from datetime import datetime, date

        # 1. Distribuição por Grupo de Risco (Pizza/Rosca)
        query_risco = """
            SELECT COALESCE(ap.grupo_risco, 'A') as grupo, COUNT(*) as qtd
            FROM paciente p
            LEFT JOIN (
                SELECT DISTINCT ON (id) id, grupo_risco
                FROM atendimento_paciente
                ORDER BY id, nr_atendimento DESC
            ) ap ON p.id = ap.id
            GROUP BY grupo
        """
        res_risco = await db.execute(text(query_risco))
        risco_rows = res_risco.fetchall()
        
        risco_map = {"A": 0, "B": 0, "C": 0, "D": 0}
        for r in risco_rows:
            g = r[0] or "A"
            risco_map[g] = r[1]
            
        risco_data = {f"Grupo {k}": v for k, v in risco_map.items()}

        # 2. Ranking de Sintomas Mais Frequentes (Barras)
        query_sintomas = """
            SELECT 
                SUM(CASE WHEN febre = '1' THEN 1 ELSE 0 END) as febre,
                SUM(CASE WHEN mialgia = '1' THEN 1 ELSE 0 END) as mialgia,
                SUM(CASE WHEN cefaleia = '1' THEN 1 ELSE 0 END) as cefaleia,
                SUM(CASE WHEN exantema = '1' THEN 1 ELSE 0 END) as exantema,
                SUM(CASE WHEN vomito = '1' THEN 1 ELSE 0 END) as vomito,
                SUM(CASE WHEN nausea = '1' THEN 1 ELSE 0 END) as nausea,
                SUM(CASE WHEN dor_costas = '1' THEN 1 ELSE 0 END) as dor_costas,
                SUM(CASE WHEN conjuntvit = '1' THEN 1 ELSE 0 END) as conjuntvit,
                SUM(CASE WHEN artrite = '1' THEN 1 ELSE 0 END) as artrite,
                SUM(CASE WHEN artralgia = '1' THEN 1 ELSE 0 END) as artralgia,
                SUM(CASE WHEN dor_retro = '1' THEN 1 ELSE 0 END) as dor_retro
            FROM atendimento_paciente
        """
        res_sintomas = await db.execute(text(query_sintomas))
        sintomas_row = res_sintomas.fetchone()
        
        sintomas_keys = [
            "Febre", "Dor Muscular", "Dor de Cabeça", "Manchas na Pele", 
            "Vômitos", "Náuseas", "Dor nas Costas", "Conjuntivite", 
            "Inchaço Articular", "Dor Articular", "Dor Atrás dos Olhos"
        ]
        
        sintomas_data = {}
        if sintomas_row:
            sintomas_data = {sintomas_keys[i]: int(sintomas_row[i] or 0) for i in range(len(sintomas_keys))}
        else:
            sintomas_data = {k: 0 for k in sintomas_keys}

        # 3. Distribuição por Faixa Etária (Colunas)
        res_idades = await db.execute(text('SELECT "DT_NASCIMENTO" FROM paciente'))
        idades = []
        for r in res_idades.fetchall():
            birth = r[0]
            if birth:
                if isinstance(birth, str):
                    try:
                        birth = datetime.strptime(birth, "%Y-%m-%d").date()
                    except:
                        birth = None
                if isinstance(birth, datetime):
                    birth = birth.date()
                if birth:
                    today = date.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    idades.append(age)
                else:
                    idades.append(30)
            else:
                idades.append(30)
                
        faixas = {"Crianças (<12)": 0, "Adolescentes (12-18)": 0, "Adultos (19-59)": 0, "Idosos (60+)": 0}
        for age in idades:
            if age < 12:
                faixas["Crianças (<12)"] += 1
            elif age <= 18:
                faixas["Adolescentes (12-18)"] += 1
            elif age <= 59:
                faixas["Adultos (19-59)"] += 1
            else:
                faixas["Idosos (60+)"] += 1

        # 4. Prevalência de Comorbidades (Tabela/Cards)
        query_comorb = """
            SELECT 
                SUM(CASE WHEN diabetes = '1' THEN 1 ELSE 0 END) as diabetes,
                SUM(CASE WHEN hipertensa = '1' THEN 1 ELSE 0 END) as hipertensa,
                SUM(CASE WHEN renal = '1' THEN 1 ELSE 0 END) as renal,
                SUM(CASE WHEN hepatopat = '1' THEN 1 ELSE 0 END) as hepatopat,
                SUM(CASE WHEN hematolog = '1' THEN 1 ELSE 0 END) as hematolog,
                SUM(CASE WHEN acido_pept = '1' THEN 1 ELSE 0 END) as acido_pept,
                SUM(CASE WHEN auto_imune = '1' THEN 1 ELSE 0 END) as auto_imune
            FROM paciente
        """
        res_comorb = await db.execute(text(query_comorb))
        comorb_row = res_comorb.fetchone()
        
        comorb_keys = [
            "Diabetes", "Hipertensão", "Doença Renal", "Hepatopatia", 
            "Doença Hematológica", "Doença Ácido-Péptica", "Doença Autoimune"
        ]
        
        comorb_data = {}
        if comorb_row:
            comorb_data = {comorb_keys[i]: int(comorb_row[i] or 0) for i in range(len(comorb_keys))}
        else:
            comorb_data = {k: 0 for k in comorb_keys}

        return {
            "status": "success",
            "data": {
                "risco": risco_data,
                "sintomas": sintomas_data,
                "faixas_etarias": faixas,
                "comorbidades": comorb_data
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular dados de relatórios: {str(e)}"
        )

@router.get("/admissions")
async def get_dashboard_admissions(days: int = 30, db: AsyncSession = Depends(get_db)):
    """
    Retorna a quantidade diária de admissões de pacientes nos últimos X dias.
    """
    try:
        query = """
            SELECT dt, COUNT(*) as count
            FROM (
                SELECT p.id, COALESCE(CAST(MIN(ap.dt_inicio) AS DATE), CURRENT_DATE) as dt
                FROM paciente p
                LEFT JOIN atendimento_paciente ap ON p.id = ap.id
                GROUP BY p.id
            ) registrations
            WHERE dt >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
            GROUP BY dt
            ORDER BY dt ASC
        """
        res = await db.execute(text(query), {"days": days})
        rows = res.fetchall()
        
        data_map = {}
        for r in rows:
            dt_str = r[0].strftime("%Y-%m-%d") if r[0] else None
            if dt_str:
                data_map[dt_str] = r[1]
                
        return {
            "status": "success",
            "data": data_map
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico de admissões: {str(e)}"
        )