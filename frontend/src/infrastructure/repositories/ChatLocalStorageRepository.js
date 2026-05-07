import { LocalStorageManager } from '../storage/LocalStorageManager.js';
import { ChatSession } from '../../domain/entities/ChatSession.js';
import { Message } from '../../domain/entities/Message.js';

export class ChatLocalStorageRepository {
    constructor() {
        this.storage = new LocalStorageManager('denguecare_appState');
        this.estadoPadrao = {
            sessaoAtualId: null,
            sessoes: [
                new ChatSession({
                    id: 'paciente_1',
                    nomePaciente: 'DengueCare',
                    avatarBg: 'url("../../../../../images/Logo01.png")',
                    mensagens: []
                })
            ]
        };
        this.appState = this.storage.load() || JSON.parse(JSON.stringify(this.estadoPadrao));
    }

    _save() {
        this.storage.save(this.appState);
    }

    async getSessions() {
        return this.appState.sessoes;
    }

    async getSessionById(sessionId) {
        return this.appState.sessoes.find(s => s.id === sessionId) || null;
    }

    async createSession(nomePaciente, avatarBg) {
        const novaSessao = new ChatSession({
            id: 'paciente_' + Date.now(),
            nomePaciente,
            avatarBg,
            mensagens: []
        });
        this.appState.sessoes.unshift(novaSessao);
        this._save();
        return novaSessao;
    }

    async saveMessage(sessaoId, texto, tipo, timestamp) {
        const sessao = await this.getSessionById(sessaoId);
        if (!sessao) return null;

        const novaMsg = new Message({
            id: 'msg_' + Date.now(),
            texto,
            tipo,
            timestamp
        });
        sessao.mensagens.push(novaMsg);
        this._save();
        return novaMsg;
    }

    async deleteSession(sessaoId) {
        this.appState.sessoes = this.appState.sessoes.filter(s => s.id !== sessaoId);
        if (this.appState.sessaoAtualId === sessaoId) {
            this.appState.sessaoAtualId = null;
        }
        this._save();
    }

    async clearMessages(sessaoId) {
        const sessao = await this.getSessionById(sessaoId);
        if (sessao) {
            sessao.mensagens = [];
            this._save();
        }
    }

    async getCurrentSessionId() {
        return this.appState.sessaoAtualId;
    }

    async setCurrentSessionId(id) {
        this.appState.sessaoAtualId = id;
        this._save();
    }
}
