from locust import HttpUser, task, between
import random

class DengueCarePatient(HttpUser):
    # Simula o tempo de digitação de um paciente real (entre 1 e 3 segundos)
    wait_time = between(1, 3)

    @task
    def send_chat_message(self):
        """
        Envia requisições POST simulando as respostas fechadas (numéricas) dos pacientes.
        """
        payload = {
            "telefone": f"551999{random.randint(1000000, 9999999)}",
            "mensagem": str(random.randint(1, 3))
        }
        
        # Faz a requisição para o endpoint e agrupa no relatório sob o nome "Chat Send API"
        self.client.post(
            "/api/v1/chat/send",
            json=payload,
            name="Chat Send API"
        )