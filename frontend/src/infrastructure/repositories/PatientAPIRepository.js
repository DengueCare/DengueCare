import { Patient } from '../../domain/entities/Patient.js';

export class PatientAPIRepository {
    constructor(baseUrl = 'http://localhost:8000/api/v1') {
        this.baseUrl = baseUrl;
    }

    async getAllPatients() {
        try {
            // Placeholder para a chamada real da API
            // const response = await fetch(`${this.baseUrl}/patients`);
            // if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            // const data = await response.json();
            
            // Retornamos um objeto vazio ou array vazio para simular o banco sem pacientes
            const data = {}; 
            
            return data;
        } catch (error) {
            console.error('Erro ao buscar pacientes na API:', error);
            // Retorna vazio em caso de falha de conexão (evita quebrar o frontend)
            return {};
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
