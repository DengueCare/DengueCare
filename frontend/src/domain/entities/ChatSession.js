export class ChatSession {
    constructor({ id, nomePaciente, avatarBg, mensagens }) {
        this.id = id;
        this.nomePaciente = nomePaciente;
        this.avatarBg = avatarBg;
        this.mensagens = mensagens || [];
    }
}
