import { Patient } from '../../domain/entities/Patient.js';

export class PatientAPIRepository {
    constructor(baseUrl = 'http://localhost:8000/api/v1') {
        this.baseUrl = baseUrl;
    }

    async getAllPatients() {
        try {
            const response = await fetch(`${this.baseUrl}/patients/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            const data = await response.json(); 
            
            return data.data;
        } catch (error) {
            console.error('Erro ao buscar pacientes na API:', error);
            // Retorna vazio em caso de falha de conexão (evita quebrar o frontend)
            throw error;
        }
    }

    async getPatientById(id) {
        try {
            // Placeholder para a chamada real da API
            // const response = await fetch(`${this.baseUrl}/patients/${id}`);
            // if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            // return await response.json();
            
            return null;
        } catch (error) {
            console.error(`Erro ao buscar paciente ${id} na API:`, error);
            return null;
        }
    }
}
