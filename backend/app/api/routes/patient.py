from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db
from app.services.atendimento_service import buscar_historico_atendimentos
from app.services.bot_service import detectar_evolucao
from app.services.patient_service import listar_pacientes_inativos, reativar_paciente
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional

class PatientCreateRequest(BaseModel):
    nome: str
    telefone: str
    nr_carteira: str
    dt_sin_pri: str
    ubs_atual: Optional[str] = None
    diabetes: bool = False
    hematolog: bool = False
    hepatopat: bool = False
    renal: bool = False
    hipertensa: bool = False
    acido_pept: bool = False
    auto_imune: bool = False

class PatientUpdateRequest(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    dt_sin_pri: Optional[str] = None
    ubs_atual: Optional[str] = None
    diabetes: Optional[bool] = None
    hematolog: Optional[bool] = None
    hepatopat: Optional[bool] = None
    renal: Optional[bool] = None
    hipertensa: Optional[bool] = None
    acido_pept: Optional[bool] = None
    auto_imune: Optional[bool] = None

class PatientInactivateRequest(BaseModel):
    motivo_inativacao: str

router = APIRouter()

@router.get("/")
async def get_all_patients(db: AsyncSession = Depends(get_db)):
    """
    Busca todos os pacientes e anexa os dados de risco baseados no histórico.
    """
    try:
        result = await db.execute(text("SELECT * FROM paciente"))
        pacientes = result.fetchall()
        
        formatted_data = []
        for row in pacientes:
            paciente = dict(row._mapping)
            
            # Filtra inativos pelo Python para não quebrar em DBs sem a coluna 'status'
            if paciente.get("status") == "inativo":
                continue
            historico = await buscar_historico_atendimentos(db, paciente["id"], limite=2)
            
            piorou = False
            risco = "Desconhecido"
            if len(historico) >= 2:
                risco_atual = historico[0].get("grupo_risco", "")
                risco_anterior = historico[1].get("grupo_risco", "")
                piorou = detectar_evolucao(risco_anterior, risco_atual)
                risco = risco_atual
            elif len(historico) == 1:
                risco = historico[0].get("grupo_risco", "")
            
            # Formatar para o frontend
            badge = "badge-green"
            if risco == "B": badge = "badge-yellow"
            elif risco == "C": badge = "badge-orange"
            elif risco == "D": badge = "badge-red"
            
            dias_doenca = 0
            if len(historico) > 0 and historico[-1].get("dt_fim"):
                dt_primeiro = historico[-1]["dt_fim"]
                if dt_primeiro:
                    delta = datetime.now() - dt_primeiro
                    dias_doenca = max(0, delta.days)
            
            dt_ultima_triagem = None
            if len(historico) > 0 and historico[0].get("dt_fim"):
                dt_ultima_triagem = historico[0]["dt_fim"].isoformat()

            formatted_data.append({
                "id": paciente["id"],
                "nome": paciente["nm_usuario"],
                "iniciais": paciente["nm_usuario"][:2].upper() if paciente["nm_usuario"] else "--",
                "riscoTexto": f"Grupo {risco}" if risco != "Desconhecido" else "Risco Indefinido",
                "riscoBadge": badge,
                "dias": dias_doenca,
                "piorou": piorou,
                "riscoPuro": risco,
                "dt_ultima_triagem": dt_ultima_triagem,
                "telefone": paciente.get("telefone", None)
            })
            
        return {
            "status": "success",
            "count": len(formatted_data),
            "data": formatted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar pacientes: {str(e)}")

@router.get("/inactive")
async def get_inactive_patients(db: AsyncSession = Depends(get_db)):
    try:
        patients = await listar_pacientes_inativos(db)
        return {
            "status": "success",
            "count": len(patients),
            "data": patients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar pacientes inativos: {str(e)}")

@router.get("/{patient_id}")
async def get_patient_by_id(patient_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna os detalhes completos do paciente, incluindo histórico de triagens e dados para o gráfico.
    """
    try:
        # Busca paciente
        res_pac = await db.execute(text("SELECT * FROM paciente WHERE id = :id"), {"id": patient_id})
        row = res_pac.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
            
        paciente = dict(row._mapping)
        
        # Busca historico
        historico_db = await buscar_historico_atendimentos(db, patient_id, limite=20)
        
        # Formatando historico
        historico_formatado = []
        dados_grafico = []
        mapa_risco_num = {"A": 25, "B": 50, "C": 75, "D": 100}
        
        # O histórico do BD vem DESC (mais novo primeiro). O grafico precisa ASC (mais antigo primeiro).
        historico_asc = list(reversed(historico_db))
        
        for idx, h in enumerate(historico_asc):
            grupo = h.get("grupo_risco", "A")
            dados_grafico.append(mapa_risco_num.get(grupo, 0))
            
            sintomas = []
            if h.get("febre") in ["1", 1, 1.0]: sintomas.append({"n": "Febre", "c": "badge-red"})
            if h.get("cefaleia") in ["1", 1, 1.0]: sintomas.append({"n": "Dor de Cabeça", "c": "badge-yellow"})
            if h.get("mialgia") in ["1", 1, 1.0]: sintomas.append({"n": "Dor Muscular", "c": "badge-orange"})
            if h.get("exantema") in ["1", 1, 1.0]: sintomas.append({"n": "Manchas", "c": "badge-red"})
            if h.get("vomito") in ["1", 1, 1.0]: sintomas.append({"n": "Vômito", "c": "badge-orange"})
            if h.get("dor_costas") in ["1", 1, 1.0]: sintomas.append({"n": "Dor Costas", "c": "badge-yellow"})
            
            dt = h.get("dt_fim")
            dia_texto = dt.strftime("%d/%m/%Y %H:%M") if dt else f"Triagem {idx+1}"
            
            historico_formatado.append({
                "dia": dia_texto,
                "grupo": f"Grupo {grupo}",
                "sintomas": sintomas
            })
            
        # Reverte para mostrar mais recente no topo do historico visual
        historico_formatado.reverse()
        
        # Calculando Idade
        idade = "--"
        if paciente.get("DT_NASCIMENTO"):
            dt_nasc = paciente["DT_NASCIMENTO"]
            if isinstance(dt_nasc, str) and len(dt_nasc) >= 10:
                try:
                    dt_nasc = datetime.strptime(dt_nasc[:10], "%Y-%m-%d").date()
                except:
                    pass
            if isinstance(dt_nasc, date):
                hoje = date.today()
                idade = hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day))
        
        comorbidades = []
        if paciente.get("diabetes") in [1, 1.0, "1"]: comorbidades.append("Diabetes")
        if paciente.get("hipertensa") in [1, 1.0, "1"]: comorbidades.append("Hipertensão")
        if paciente.get("renal") in [1, 1.0, "1"]: comorbidades.append("Doença Renal")
        if paciente.get("hematolog") in [1, 1.0, "1"]: comorbidades.append("Hematológica")
        
        # Trend
        trend = "Estável"
        trendColor = "#666"
        scoreAtual = dados_grafico[-1] if dados_grafico else 0
        if len(dados_grafico) >= 2:
            diff = dados_grafico[-1] - dados_grafico[-2]
            if diff > 0:
                trend = f"▲ +{diff}"
                trendColor = "#d93025"
            elif diff < 0:
                trend = f"▼ {diff}"
                trendColor = "#1e8e3e"
                
        # Analise de piora global do historico mais recente
        piorou = False
        if len(historico_db) >= 2:
            piorou = detectar_evolucao(historico_db[1].get("grupo_risco", ""), historico_db[0].get("grupo_risco", ""))
            
        return {
            "id": paciente["id"],
            "nome": paciente["nm_usuario"],
            "iniciais": paciente["nm_usuario"][:2].upper() if paciente["nm_usuario"] else "--",
            "idade": f"{idade}",
            "tel": paciente.get("telefone", ""),
            "ubs": paciente.get("ubs_atual", ""),
            "status": "Monitoramento Ativo" if not piorou else "Atenção Requerida",
            "score": scoreAtual,
            "trend": trend,
            "trendColor": trendColor,
            "grupo": f"Grupo {historico_db[0].get('grupo_risco', 'A')}" if historico_db else "Risco Indefinido",
            "comorb": comorbidades if comorbidades else ["Nenhuma declarada"],
            "grafico": dados_grafico,
            "historico": historico_formatado,
            "piorou": piorou
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_patient(req: PatientCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        query = """
            INSERT INTO paciente (
                nm_usuario, nr_carteira, telefone, diabetes, hematolog, hepatopat, renal, hipertensa, acido_pept, auto_imune, status, ubs_atual
            ) VALUES (
                :nome, :nr_carteira, :telefone, :diabetes, :hematolog, :hepatopat, :renal, :hipertensa, :acido_pept, :auto_imune, 'ativo', :ubs_atual
            ) RETURNING id
        """
        params = {
            "nome": req.nome,
            "nr_carteira": float(req.nr_carteira),
            "telefone": req.telefone,
            "diabetes": "1" if req.diabetes else "0",
            "hematolog": "1" if req.hematolog else "0",
            "hepatopat": "1" if req.hepatopat else "0",
            "renal": "1" if req.renal else "0",
            "hipertensa": "1" if req.hipertensa else "0",
            "acido_pept": "1" if req.acido_pept else "0",
            "auto_imune": "1" if req.auto_imune else "0",
            "ubs_atual": req.ubs_atual,
        }
        res = await db.execute(text(query), params)
        await db.commit()
        row = res.fetchone()
        
        # Opcional: criar um atendimento inicial para gravar a data dt_sin_pri se fosse necessário
        # ...
        
        return {"success": True, "message": "Paciente cadastrado com sucesso", "id": row[0] if row else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{patient_id}")
async def update_patient(patient_id: int, req: PatientUpdateRequest, db: AsyncSession = Depends(get_db)):
    try:
        updates = []
        params = {"id": patient_id}
        
        if req.nome is not None:
            updates.append("nm_usuario = :nome")
            params["nome"] = req.nome
        if req.telefone is not None:
            updates.append("telefone = :telefone")
            params["telefone"] = req.telefone
        if req.ubs_atual is not None:
            updates.append("ubs_atual = :ubs_atual")
            params["ubs_atual"] = req.ubs_atual
        if req.diabetes is not None:
            updates.append("diabetes = :diabetes")
            params["diabetes"] = "1" if req.diabetes else "0"
        if req.hematolog is not None:
            updates.append("hematolog = :hematolog")
            params["hematolog"] = "1" if req.hematolog else "0"
        if req.hepatopat is not None:
            updates.append("hepatopat = :hepatopat")
            params["hepatopat"] = "1" if req.hepatopat else "0"
        if req.renal is not None:
            updates.append("renal = :renal")
            params["renal"] = "1" if req.renal else "0"
        if req.hipertensa is not None:
            updates.append("hipertensa = :hipertensa")
            params["hipertensa"] = "1" if req.hipertensa else "0"
        if req.acido_pept is not None:
            updates.append("acido_pept = :acido_pept")
            params["acido_pept"] = "1" if req.acido_pept else "0"
        if req.auto_imune is not None:
            updates.append("auto_imune = :auto_imune")
            params["auto_imune"] = "1" if req.auto_imune else "0"
            
        if not updates:
            return {"success": True, "message": "Nada a atualizar"}
            
        query = "UPDATE paciente SET " + ", ".join(updates) + " WHERE id = :id"
        res = await db.execute(text(query), params)
        await db.commit()
        
        return {"success": True, "message": "Paciente atualizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{patient_id}/inactivate")
async def inactivate_patient(patient_id: int, req: PatientInactivateRequest, db: AsyncSession = Depends(get_db)):
    try:
        query = "UPDATE paciente SET status = 'inativo', motivo_inativacao = :motivo WHERE id = :id"
        res = await db.execute(text(query), {"id": patient_id, "motivo": req.motivo_inativacao})
        await db.commit()
        
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
            
        return {"success": True, "message": "Paciente inativado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{patient_id}/reactivate")
async def reactivate_patient_route(patient_id: int, db: AsyncSession = Depends(get_db)):
    try:
        success = await reativar_paciente(db, patient_id)
        if not success:
            raise HTTPException(status_code=404, detail="Paciente não encontrado ou erro na reativação")
        return {"success": True, "message": "Paciente reativado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))