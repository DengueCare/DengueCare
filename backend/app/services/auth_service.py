import os
import hashlib
import binascii
import re
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

async def registrar_profissional(db: AsyncSession, nome: str, carteira: str, senha: str) -> dict:
    """
    Registra um novo profissional de saúde no banco de dados.
    Levanta exceção se a carteira já existir ou se a senha for inválida.
    """
    # 0. Validar critérios de senha
    validar_senha(senha)

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
            INSERT INTO profissional (nome, carteira, senha_hash, salt, status)
            VALUES (:nome, :carteira, :senha_hash, :salt, 'ativo')
            RETURNING id, nome, carteira, ubs, status, dt_criacao, is_admin
        '''),
        {
            "nome": nome,
            "carteira": carteira,
            "senha_hash": senha_hash,
            "salt": salt
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

async def toggle_admin_profissional(db: AsyncSession, carteira: str) -> dict | None:
    """
    Alterna a permissão de administrador (is_admin) de um profissional.
    """
    # Primeiro busca o estado atual
    result = await db.execute(
        text("SELECT is_admin FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    row = result.fetchone()
    if not row:
        return None
    
    novo_is_admin = not bool(row[0])
    
    update_result = await db.execute(
        text("UPDATE profissional SET is_admin = :novo_is_admin WHERE carteira = :carteira RETURNING id, nome, carteira, ubs, status, is_admin"),
        {"novo_is_admin": novo_is_admin, "carteira": carteira}
    )
    await db.commit()
    updated_row = update_result.fetchone()
    return dict(updated_row._mapping) if updated_row else None
