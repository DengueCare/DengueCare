export class Message {
    constructor({ id, texto, tipo, timestamp }) {
        this.id = id;
        this.texto = texto;
        this.tipo = tipo; // 'sent', 'received', 'system'
        this.timestamp = timestamp;
    }
}
