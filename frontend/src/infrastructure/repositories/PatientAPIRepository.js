import { Patient } from '../../domain/entities/Patient.js';
import { API_BASE_URL } from '../../config.js';

export class PatientAPIRepository {
    constructor(baseUrl = API_BASE_URL) {
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
            throw error;
        }
    }

    async getPatientById(id) {
        try {
            const response = await fetch(`${this.baseUrl}/patients/${id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Erro ao buscar paciente ${id} na API:`, error);
            return null;
        }
    }
}
