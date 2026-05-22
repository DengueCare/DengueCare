import os
import hashlib
import binascii
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
    Levanta exceção se a carteira já existir.
    """
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
            INSERT INTO profissional (nome, carteira, senha_hash, salt)
            VALUES (:nome, :carteira, :senha_hash, :salt)
            RETURNING id, nome, carteira, dt_criacao
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
        text("SELECT id, nome, carteira, senha_hash, salt FROM profissional WHERE carteira = :carteira"),
        {"carteira": carteira}
    )
    row = result.fetchone()
    
    if not row:
        return None # Profissional não encontrado
        
    prof = dict(row._mapping)
    
    if verify_password(prof["senha_hash"], prof["salt"], senha):
        # Remove dados sensíveis antes de retornar
        prof.pop("senha_hash")
        prof.pop("salt")
        return prof
        
    return None # Senha incorreta

async def atualizar_profissional(db: AsyncSession, carteira: str, novo_nome: str = None, nova_senha: str = None) -> dict | None:
    """
    Atualiza o nome e/ou a senha do profissional.
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
        
    if nova_senha:
        senha_hash, salt = hash_password(nova_senha)
        updates.append("senha_hash = :senha_hash")
        updates.append("salt = :salt")
        params["senha_hash"] = senha_hash
        params["salt"] = salt

    if not updates:
        return None

    query += ", ".join(updates) + " WHERE carteira = :carteira RETURNING id, nome, carteira, dt_criacao"
    
    update_result = await db.execute(text(query), params)
    await db.commit()
    
    row = update_result.fetchone()
    return dict(row._mapping) if row else None
