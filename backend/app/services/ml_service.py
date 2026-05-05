import asyncio
import random

async def predict_risk_score_mock(features_array: list) -> str:
    """
    Mock temporário para simular o tempo de processamento da IA durante os testes de carga.
    """
    # Simula o tempo de inferência do Random Forest (entre 20ms e 50ms)
    delay = random.uniform(0.02, 0.05)
    await asyncio.sleep(delay)
    
    # Retorna uma classificação aleatória para variar as respostas do servidor
    return random.choice(["A", "B", "C", "D"])