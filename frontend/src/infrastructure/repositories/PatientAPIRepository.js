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

    async createPatient(data) {
        try {
            const response = await fetch(`${this.baseUrl}/patients/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao criar paciente:', error);
            throw error;
        }
    }

    async updatePatient(id, data) {
        try {
            const response = await fetch(`${this.baseUrl}/patients/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao atualizar paciente:', error);
            throw error;
        }
    }

    async inactivatePatient(id, motivo) {
        try {
            const response = await fetch(`${this.baseUrl}/patients/${id}/inactivate`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ motivo_inativacao: motivo })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao inativar paciente:', error);
            throw error;
        }
    }

    async updateProfile(data) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/update`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao atualizar perfil:', error);
            throw error;
        }
    }

    async inactivateProfile(carteira) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/inactivate`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ carteira })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao inativar perfil:', error);
            throw error;
        }
    }

    async getDashboardStats() {
        try {
            const response = await fetch(`${this.baseUrl}/dashboard/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const res = await response.json();
            return res.data;
        } catch (error) {
            console.error('Erro ao buscar estatísticas do dashboard:', error);
            return null;
        }
    }

    async getReportsData() {
        try {
            const response = await fetch(`${this.baseUrl}/dashboard/reports`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const res = await response.json();
            return res.data;
        } catch (error) {
            console.error('Erro ao buscar relatórios:', error);
            return null;
        }
    }

    async getAdmissionsData(days = 30) {
        try {
            const response = await fetch(`${this.baseUrl}/dashboard/admissions?days=${days}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const res = await response.json();
            return res.data;
        } catch (error) {
            console.error('Erro ao buscar admissões:', error);
            return null;
        }
    }

    async getInactivePatients() {
        try {
            const response = await fetch(`${this.baseUrl}/patients/inactive`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const res = await response.json();
            return res.data;
        } catch (error) {
            console.error('Erro ao buscar pacientes inativos:', error);
            throw error;
        }
    }

    async reactivatePatient(id) {
        try {
            const response = await fetch(`${this.baseUrl}/patients/${id}/reactivate`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao reativar paciente:', error);
            throw error;
        }
    }

    async getAllProfessionals() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/professionals`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const res = await response.json();
            return res.data;
        } catch (error) {
            console.error('Erro ao buscar profissionais:', error);
            throw error;
        }
    }

    async reactivateProfessional(carteira) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/professionals/${carteira}/reactivate`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao reativar profissional:', error);
            throw error;
        }
    }

    async toggleAdminProfessional(carteira) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/professionals/${carteira}/toggle-admin`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erro ao alterar permissão de administrador do profissional:', error);
            throw error;
        }
    }
}
