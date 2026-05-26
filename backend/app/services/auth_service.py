import os
import hashlib
import binascii
import re
import unicodedata
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

def validar_senha(senha: str) -> None:
    """
    Valida se a senha atende aos critérios de segurança:
    1) Pelo menos 8 caracteres
    2) Pelo menos uma letra maiúscula
    3) Pelo menos 1 caractere especial
    """
    if len(senha) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if not re.search(r"[A-Z]", senha):
        raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
    if not re.search(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚâêîôûÂÊÎÔÛãõÃÕçÇ\s]", senha):
        raise ValueError("A senha deve conter pelo menos um caractere especial (ex: !, @, #, $, %, etc.).")

def normalizar_resposta(texto: str) -> str:
    """
    Remove acentos, espaços extras e converte para minúsculas.
    Exemplo: "São Paulo " -> "sao paulo"
    """
    if not texto:
        return ""
    texto = " ".join(texto.lower().strip().split())
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def validar_carteira(carteira: str, is_admin: bool) -> None:
    """
    Valida a carteira profissional (CRM/COREN).
    Se for administrador (ou começar com ADMIN), ignora a validação de CRM/COREN e exige min de 4 caracteres.
    """
    credencial = carteira.strip().upper()
    if is_admin or credencial.startswith('ADMIN'):
        if len(credencial) < 4:
            raise ValueError("O identificador de administrador deve ter pelo menos 4 caracteres.")
        return

    # CRM/COREN validation: extract digits
    apenas_digitos = re.sub(r"\D", "", credencial)
    if len(apenas_digitos) < 4 or len(apenas_digitos) > 10:
        raise ValueError("CRM ou COREN inválido. Deve conter entre 4 e 10 números (ex: 123456 ou 123456/SP).")

def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    """
    Gera um hash seguro para a senha usando PBKDF2 HMAC.
    Retorna uma tupla (senha_hash_hex, salt_hex).
    """
    if salt is None:
        salt = os.urandom(32) # Gera um novo salt de 32 bytes
    
    # Parâmetros recomendados
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    return binascii.hexlify(pwd_hash).decode('ascii'), binascii.hexlify(salt).decode('ascii')

def verify_password(stored_password_hash: str, stored_salt_hex: str, provided_password: str) -> bool:
    """
    Verifica se a senha fornecida corresponde ao hash armazenado.
    """
    salt = binascii.unhexlify(stored_salt_hex)
    provided_hash, _ = hash_password(provided_password, salt)
    return provided_hash == stored_password_hash

async def registrar_profissional(db: AsyncSession, nome: str, carteira: str, senha: str, pergunta_seguranca: str, resposta_seguranca: str, is_admin: bool = False) -> dict:
    """
    Registra um novo profissional de saúde no banco de dados.
    Levanta exceção se a carteira já existir ou se a senha/carteira/resposta forem inválidas.
    """
    # 0. Validar critérios
    validar_senha(senha)
    validar_carteira(carteira, is_admin)
    
    resposta_normalizada = normalizar_resposta(resposta_seguranca)
    if not pergunta_seguranca or not resposta_normalizada:
        raise ValueError("Pergunta e resposta de segurança são obrigatórias.")

    # 1. Checar se já existe
    result = await db.execute(
        text("SELECT id FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    if result.fetchone():
        raise ValueError("Já existe um profissional cadastrado com esta carteira.")

    # 2. Gerar hash e salt
    senha_hash, salt = hash_password(senha)

    # 3. Inserir no banco
    insert_result = await db.execute(
        text('''
            INSERT INTO profissional (nome, carteira, senha_hash, salt, status, pergunta_seguranca, resposta_seguranca, is_admin)
            VALUES (:nome, :carteira, :senha_hash, :salt, 'ativo', :pergunta, :resposta, :is_admin)
            RETURNING id, nome, carteira, ubs, status, dt_criacao, is_admin
        '''),
        {
            "nome": nome,
            "carteira": carteira,
            "senha_hash": senha_hash,
            "salt": salt,
            "pergunta": pergunta_seguranca,
            "resposta": resposta_normalizada,
            "is_admin": is_admin
        }
    )
    await db.commit()
    row = insert_result.fetchone()
    return dict(row._mapping)

async def autenticar_profissional(db: AsyncSession, carteira: str, senha: str) -> dict | None:
    """
    Autentica o profissional verificando a carteira e a senha.
    Retorna os dados do profissional se sucesso, ou None se falhar.
    """
    result = await db.execute(
        text("SELECT id, nome, carteira, senha_hash, salt, ubs, status, is_admin FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    row = result.fetchone()
    
    if not row:
        return None # Profissional não encontrado
        
    prof = dict(row._mapping)
    
    if prof.get("status") == "inativo":
        raise ValueError("Conta inativada. Entre em contato com o administrador.")
    
    if verify_password(prof["senha_hash"], prof["salt"], senha):
        # Remove dados sensíveis antes de retornar
        prof.pop("senha_hash")
        prof.pop("salt")
        return prof
        
    return None # Senha incorreta

async def atualizar_profissional(db: AsyncSession, carteira: str, novo_nome: str = None, nova_senha: str = None, nova_ubs: str = None) -> dict | None:
    """
    Atualiza o nome, senha e/ou ubs do profissional.
    """
    # Verifica se existe
    result = await db.execute(
        text("SELECT id FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    if not result.fetchone():
        return None

    query = "UPDATE profissional SET "
    params = {"carteira": carteira}
    updates = []

    if novo_nome:
        updates.append("nome = :nome")
        params["nome"] = novo_nome
        
    if nova_ubs:
        updates.append("ubs = :ubs")
        params["ubs"] = nova_ubs
        
    if nova_senha:
        validar_senha(nova_senha)
        senha_hash, salt = hash_password(nova_senha)
        updates.append("senha_hash = :senha_hash")
        updates.append("salt = :salt")
        params["senha_hash"] = senha_hash
        params["salt"] = salt

    if not updates:
        return None

    query += ", ".join(updates) + " WHERE carteira = :carteira RETURNING id, nome, carteira, ubs, status, dt_criacao, is_admin"
    
    update_result = await db.execute(text(query), params)
    await db.commit()
    
    row = update_result.fetchone()
    return dict(row._mapping) if row else None

async def inativar_profissional(db: AsyncSession, carteira: str) -> bool:
    """
    Inativa a conta de um profissional da saúde.
    """
    result = await db.execute(
        text("UPDATE profissional SET status = 'inativo' WHERE carteira = :carteira RETURNING id"),
        {"carteira": carteira}
    )
    await db.commit()
    return result.fetchone() is not None

async def listar_todos_profissionais(db: AsyncSession) -> list[dict]:
    """
    Retorna todos os profissionais de saúde cadastrados.
    """
    result = await db.execute(
        text("SELECT id, nome, carteira, ubs, status, is_admin, dt_criacao FROM profissional ORDER BY nome ASC")
    )
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]

async def reativar_profissional(db: AsyncSession, carteira: str) -> bool:
    """
    Reativa a conta de um profissional da saúde.
    """
    result = await db.execute(
        text("UPDATE profissional SET status = 'ativo' WHERE carteira = :carteira RETURNING id"),
        {"carteira": carteira}
    )
    await db.commit()
    return result.fetchone() is not None

async def alterar_status_admin(db: AsyncSession, carteira: str, is_admin: bool) -> bool:
    """
    Altera a permissão de administrador de um profissional médico no banco de dados.
    """
    try:
        # Altere "is_admin" para o nome exato da sua coluna no Supabase, caso seja diferente
        result = await db.execute(
            text("""
                UPDATE profissional 
                SET is_admin = :admin 
                WHERE nr_carteira = :carteira
            """),
            {"admin": is_admin, "carteira": carteira}
        )
        await db.commit()
        
        # Verifica se alguma linha foi afetada (se o profissional realmente existe)
        if result.rowcount > 0:
            return True
        return False
        
    except Exception as e:
        await db.rollback()
        raise e

async def obter_pergunta_seguranca(db: AsyncSession, carteira: str) -> str | None:
    """
    Retorna a pergunta de segurança cadastrada para o profissional.
    """
    result = await db.execute(
        text("SELECT pergunta_seguranca FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    row = result.fetchone()
    if row:
        return row[0]
    return None

async def recuperar_senha_por_pergunta(db: AsyncSession, carteira: str, resposta: str, nova_senha: str) -> bool:
    """
    Verifica a resposta de segurança e, se correta, atualiza para a nova senha.
    """
    # 0. Validar critérios da nova senha
    validar_senha(nova_senha)

    # 1. Buscar a resposta correta no banco
    result = await db.execute(
        text("SELECT resposta_seguranca FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    row = result.fetchone()
    if not row:
        raise ValueError("Profissional não encontrado.")
    
    resposta_correta = row[0]
    if not resposta_correta:
        raise ValueError("Este profissional não possui pergunta de segurança cadastrada.")

    # 2. Comparar respostas normalizadas
    if normalizar_resposta(resposta) != resposta_correta:
        raise ValueError("Resposta de segurança incorreta.")

    # 3. Atualizar a senha
    senha_hash, salt = hash_password(nova_senha)
    await db.execute(
        text("UPDATE profissional SET senha_hash = :senha_hash, salt = :salt WHERE carteira = :carteira"),
        {
            "senha_hash": senha_hash,
            "salt": salt,
            "carteira": carteira
        }
    )
    await db.commit()
    return True
