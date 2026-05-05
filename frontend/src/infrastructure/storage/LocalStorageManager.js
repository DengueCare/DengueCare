export class LocalStorageManager {
    constructor(storageKey) {
        this.storageKey = storageKey;
    }

    load() {
        try {
            const data = localStorage.getItem(this.storageKey);
            if (data) return JSON.parse(data);
        } catch (e) {
            console.warn('Erro ao carregar dados salvos:', e);
        }
        return null;
    }

    save(data) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            console.warn('Erro ao salvar dados:', e);
        }
    }
}
