import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.db.database import engine
from app.services.auth_service import hash_password

async def migrate():
    async with engine.begin() as conn:
        print("Adicionando coluna is_admin à tabela profissional...")
        try:
            await conn.execute(text("ALTER TABLE profissional ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
            print("[OK] Coluna is_admin adicionada.")
        except Exception as e:
            print(f"[Aviso/Erro] {e} (provavelmente a coluna já existe)")
            
        print("Inserindo administrador mestre padrão...")
        try:
            # 1. Gerar hash e salt para a senha 'DengueCareAdmin2026!'
            senha_hash, salt = hash_password("DengueCareAdmin2026!")
            
            # 2. Verificar se já existe o profissional com carteira 'admin'
            result = await conn.execute(
                text("SELECT id FROM profissional WHERE carteira = 'admin'")
            )
            row = result.fetchone()
            if not row:
                await conn.execute(
                    text('''
                        INSERT INTO profissional (nome, carteira, senha_hash, salt, status, is_admin)
                        VALUES ('Administrador', 'admin', :senha_hash, :salt, 'ativo', TRUE)
                    '''),
                    {
                        "senha_hash": senha_hash,
                        "salt": salt
                    }
                )
                print("[OK] Administrador padrão cadastrado com sucesso!")
            else:
                # O administrador já existe. Vamos apenas garantir que ele é admin
                await conn.execute(
                    text("UPDATE profissional SET is_admin = TRUE WHERE carteira = 'admin'")
                )
                print("[OK] Administrador existente atualizado para is_admin = TRUE.")
        except Exception as e:
            print(f"[Erro] Falha ao cadastrar/atualizar administrador padrão: {e}")
            
    print("Migração concluída.")

if __name__ == "__main__":
    asyncio.run(migrate())
