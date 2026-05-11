import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.db.database import engine

async def get_schema():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'paciente'"))
        rows = result.fetchall()
        for row in rows:
            print(row)

asyncio.run(get_schema())