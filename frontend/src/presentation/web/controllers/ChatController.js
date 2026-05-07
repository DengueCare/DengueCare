import { ChatLocalStorageRepository } from '../../../infrastructure/repositories/ChatLocalStorageRepository.js';
import * as ChatUseCases from '../../../application/usecases/ChatUseCases.js';

export class ChatController {
    constructor() {
        const chatRepo = new ChatLocalStorageRepository();
        this.getChatSessions = new ChatUseCases.GetChatSessionsUseCase(chatRepo);
        this.createChatSession = new ChatUseCases.CreateChatSessionUseCase(chatRepo);
        this.sendChatMessage = new ChatUseCases.SendChatMessageUseCase(chatRepo);
        this.deleteChatSession = new ChatUseCases.DeleteChatSessionUseCase(chatRepo);
        this.clearChatMessages = new ChatUseCases.ClearChatMessagesUseCase(chatRepo);
        this.getCurrentSessionId = new ChatUseCases.GetCurrentSessionIdUseCase(chatRepo);
        this.setCurrentSessionId = new ChatUseCases.SetCurrentSessionIdUseCase(chatRepo);

        this.chatBox = document.getElementById('chat-box');
        this.chatArea = document.getElementById('chat-area');
        this.blankState = document.getElementById('blank-state');
        this.inputMsg = document.getElementById('input-msg');

        this._bindEvents();
        this._init();
    }

    _bindEvents() {
        // Expose to window for inline onclick attributes
        window.abrirSessao = this.abrirSessao.bind(this);
        window.enviarTexto = this.enviarTexto.bind(this);
        window.fecharDropdowns = this.fecharDropdowns.bind(this);
        window.toggleDropdown = this.toggleDropdown.bind(this);
        window.abrirModalInput = this.abrirModalInput.bind(this);
        window.fecharModais = this.fecharModais.bind(this);
        window.criarSessaoSimulada = this.criarSessaoSimulada.bind(this);
        window.apagarConversa = this.apagarConversa.bind(this);
        window.limparMensagens = this.limparMensagens.bind(this);
        window.inserirEmoji = this.inserirEmoji.bind(this);
        window.abrirChamada = this.abrirChamada.bind(this);

        this.inputMsg.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && this.inputMsg.value.trim() !== '') this.enviarTexto();
        });

        document.addEventListener('click', this.fecharDropdowns);

        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', (e) => {
                document.body.classList.toggle('dark-theme');
                e.target.textContent = document.body.classList.contains('dark-theme') ? '🌙' : '🔆';
                this.fecharDropdowns();
            });
        }
    }

    async _init() {
        await this.carregarSessoes();
        const sessoes = await this.getChatSessions.execute();
        if (sessoes.length > 0) {
            this.abrirSessao(sessoes[0].id);
        } else {
            this.blankState.style.display = 'flex';
        }
    }

    getHoraAtual() {
        const agora = new Date();
        return agora.getHours().toString().padStart(2, '0') + ':' + agora.getMinutes().toString().padStart(2, '0');
    }

    async carregarSessoes() {
        const lista = document.getElementById('contact-list');
        lista.innerHTML = '';
        const sessoes = await this.getChatSessions.execute();
        const sessaoAtualId = await this.getCurrentSessionId.execute();
        
        sessoes.forEach(sessao => {
            const div = document.createElement('div');
            div.className = 'contact';
            if(sessaoAtualId === sessao.id) div.classList.add('active');
            
            let lastMsg = "Nenhuma mensagem";
            if(sessao.mensagens.length > 0) {
                const ultima = sessao.mensagens[sessao.mensagens.length - 1];
                if (ultima.tipo === 'system') lastMsg = '🔒 ' + ultima.texto;
                else lastMsg = ultima.tipo === 'sent' ? 'Você: ' + ultima.texto : ultima.texto;
            }

            div.innerHTML = `
                <div class="avatar" style="background-image: ${sessao.avatarBg};"></div>
                <div class="contact-content">
                    <div class="contact-top"><span class="contact-name">${sessao.nomePaciente}</span></div>
                    <span class="contact-msg">${lastMsg}</span>
                </div>
            `;
            
            div.onclick = () => this.abrirSessao(sessao.id);
            lista.appendChild(div);
        });
    }

    async abrirSessao(sessaoId) {
        await this.setCurrentSessionId.execute(sessaoId);
        await this.carregarSessoes(); 
        
        const sessoes = await this.getChatSessions.execute();
        const sessao = sessoes.find(s => s.id === sessaoId);
        if (!sessao) return;

        document.getElementById('header-name').textContent = sessao.nomePaciente;
        document.getElementById('header-avatar').style.backgroundImage = sessao.avatarBg;
        
        this.blankState.style.display = 'none';
        this.chatArea.style.display = 'flex';
        this.chatBox.innerHTML = ''; 
        
        sessao.mensagens.forEach(m => this.renderizarMensagemNaTela(m));
    }

    renderizarMensagemNaTela(msg) {
        const div = document.createElement('div');
        div.classList.add('message', msg.tipo);
        
        if (msg.tipo === 'system') {
            div.innerHTML = `🔒 ${msg.texto}`;
        } else {
            let checkHtml = msg.tipo === 'sent' ? '<span class="msg-time" style="color:#53bdeb; margin-left:3px;">✓✓</span>' : '';
            div.innerHTML = `${msg.texto} <span class="msg-time">${msg.timestamp || this.getHoraAtual()} ${checkHtml}</span>`;
        }
        
        this.chatBox.appendChild(div);
        this.chatBox.scrollTop = this.chatBox.scrollHeight; 
    }

    async enviarTexto() {
        const texto = this.inputMsg.value.trim();
        if (!texto) return;
        
        this.inputMsg.value = '';
        
        // 1. Renderiza e salva a mensagem do usuário no front-end
        const sessaoAtualId = await this.getCurrentSessionId.execute();
        const msgSalva = await this.sendChatMessage.execute(sessaoAtualId, texto, 'sent', this.getHoraAtual());
        this.renderizarMensagemNaTela(msgSalva);
        await this.carregarSessoes(); 

        // 2. Integração com o Backend: Chamada HTTP para a API Preditiva
        try {
            const response = await fetch('http://localhost:8000/api/v1/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    telefone: "00000000000", // Placeholder estrutural exigido pelo backend
                    mensagem: texto
                })
            });

            if (!response.ok) {
                throw new Error(`Servidor retornou status ${response.status}`);
            }

            // 3. Processa o JSON retornado pela IA
            const data = await response.json();

            // 4. Renderiza a resposta do Bot na interface
            const sessaoAtualIdNow = await this.getCurrentSessionId.execute();
            
            if (sessaoAtualIdNow === sessaoAtualId) {
                const msgRecebida = await this.sendChatMessage.execute(sessaoAtualId, data.reply, 'received', this.getHoraAtual());
                this.renderizarMensagemNaTela(msgRecebida);
                
                // Triggers visuais de emergência baseados no Risco Clínico
                if (data.requires_action) {
                    const alertaCritico = await this.sendChatMessage.execute(
                        sessaoAtualId, 
                        "PROTOCOLO DE EMERGÊNCIA ACIONADO", 
                        'system', 
                        this.getHoraAtual()
                    );
                    this.renderizarMensagemNaTela(alertaCritico);
                }
                
                await this.carregarSessoes();
            } else {
                // Caso o usuário tenha trocado de aba enquanto o servidor processava
                await this.sendChatMessage.execute(sessaoAtualId, data.reply, 'received', this.getHoraAtual());
            }

        } catch (error) {
            console.error("Erro na comunicação com o motor de inferência:", error);
            
            // Fallback de segurança (Fail-Safe)
            if (await this.getCurrentSessionId.execute() === sessaoAtualId) {
                const msgErro = await this.sendChatMessage.execute(
                    sessaoAtualId, 
                    "⚠️ Sistema de IA indisponível. Se você apresenta sinais de alarme, vá imediatamente à UPA.", 
                    'received', 
                    this.getHoraAtual()
                );
                this.renderizarMensagemNaTela(msgErro);
                await this.carregarSessoes();
            }
        }
    }

    fecharDropdowns() {
        document.querySelectorAll('.dropdown, .emoji-picker').forEach(m => m.classList.remove('active'));
    }

    toggleDropdown(id, event) {
        event.stopPropagation();
        const menu = document.getElementById(id);
        if(menu.classList.contains('active')) {
            menu.classList.remove('active');
        } else {
            this.fecharDropdowns();
            menu.classList.add('active');
        }
    }

    abrirModalInput(titulo) {
        this.fecharDropdowns();
        document.getElementById('modal-title').textContent = titulo;
        document.getElementById('modal-input').value = '';
        document.getElementById('input-modal').classList.add('active');
        document.getElementById('modal-input').focus();
    }

    fecharModais() {
        document.querySelectorAll('.overlay').forEach(modal => modal.classList.remove('active'));
    }

    async criarSessaoSimulada() {
        const nome = document.getElementById('modal-input').value.trim();
        if (nome !== '') {
            const cores =['#FF8008', '#11998e', '#4CB8C4', '#8A2387'];
            const bgGradient = 'url("../../../../../images/Logo01.png")'; // Path updated for views folder
            const novaSessao = await this.createChatSession.execute(nome, bgGradient);
            this.fecharModais();
            await this.abrirSessao(novaSessao.id);
        }
    }

    async apagarConversa() {
        const sessaoAtualId = await this.getCurrentSessionId.execute();
        if(sessaoAtualId) {
            await this.deleteChatSession.execute(sessaoAtualId);
        }
        this.chatArea.style.display = 'none';
        this.blankState.style.display = 'flex';
        this.fecharDropdowns();
        await this.carregarSessoes();
    }

    async limparMensagens() {
        const sessaoAtualId = await this.getCurrentSessionId.execute();
        if(sessaoAtualId) {
            await this.clearChatMessages.execute(sessaoAtualId);
            this.chatBox.innerHTML = '';
            await this.carregarSessoes();
        }
        this.fecharDropdowns();
    }

    inserirEmoji(emoji) {
        this.inputMsg.value += emoji;
        this.inputMsg.focus();
    }

    abrirChamada(tipo) {
        this.fecharDropdowns();
        document.getElementById('call-name').textContent = document.getElementById('header-name').textContent;
        document.getElementById('call-avatar').style.backgroundImage = document.getElementById('header-avatar').style.backgroundImage;
        document.getElementById('call-status').textContent = tipo === 'video' ? 'Chamada de vídeo simulada...' : 'Chamada de voz simulada...';
        document.getElementById('call-modal').classList.add('active');
    }
}

// Initialize the controller
new ChatController();
