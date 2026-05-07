export class GetChatSessionsUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute() {
        return await this.chatRepository.getSessions();
    }
}

export class CreateChatSessionUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute(nomePaciente, avatarBg) {
        return await this.chatRepository.createSession(nomePaciente, avatarBg);
    }
}

export class SendChatMessageUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute(sessaoId, texto, tipo, timestamp) {
        return await this.chatRepository.saveMessage(sessaoId, texto, tipo, timestamp);
    }
}

export class DeleteChatSessionUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute(sessaoId) {
        await this.chatRepository.deleteSession(sessaoId);
    }
}

export class ClearChatMessagesUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute(sessaoId) {
        await this.chatRepository.clearMessages(sessaoId);
    }
}

export class GetCurrentSessionIdUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute() {
        return await this.chatRepository.getCurrentSessionId();
    }
}

export class SetCurrentSessionIdUseCase {
    constructor(chatRepository) {
        this.chatRepository = chatRepository;
    }
    async execute(sessaoId) {
        await this.chatRepository.setCurrentSessionId(sessaoId);
    }
}
