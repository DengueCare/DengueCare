// =====================================================================
// PARTE 1: MOCK DO BANCO DE DADOS (PREPARAÇÃO PARA SUPABASE)
// =====================================================================

const STORAGE_KEY = 'denguecare_appState';

const estadoPadrao = {
    sessaoAtualId: null,
    sessoes:[
        {
            id: 'paciente_1',
            nomePaciente: 'DengueCare',
            avatarBg: 'url("../images/Logo01.png")',
            mensagens: [] // Array 100% limpo, aguardando o paciente começar
        }
    ]
};

function carregarDoStorage() {
    try {
        const dados = localStorage.getItem(STORAGE_KEY);
        if (dados) return JSON.parse(dados);
    } catch(e) {
        console.warn('Erro ao carregar dados salvos:', e);
    }
    return null;
}

function salvarNoStorage() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(appState));
    } catch(e) {
        console.warn('Erro ao salvar dados:', e);
    }
}

// Carrega estado salvo ou usa o padrão
const appState = carregarDoStorage() || JSON.parse(JSON.stringify(estadoPadrao));

async function dbGetSessoes() {
    return appState.sessoes;
}

async function dbCriarSessao(nomePaciente, avatarBg) {
    const novaSessao = {
        id: 'paciente_' + Date.now(),
        nomePaciente,
        avatarBg,
        mensagens:[] // Novas conversas nascem totalmente limpas
    };
    appState.sessoes.unshift(novaSessao);
    salvarNoStorage();
    return novaSessao;
}

async function dbSalvarMensagem(sessaoId, texto, tipo) {
    const sessao = appState.sessoes.find(s => s.id === sessaoId);
    if (!sessao) return null;
    
    const novaMsg = { id: 'msg_' + Date.now(), texto, tipo, timestamp: getHoraAtual() };
    sessao.mensagens.push(novaMsg);
    salvarNoStorage();
    return novaMsg;
}

async function dbApagarSessao(sessaoId) {
    appState.sessoes = appState.sessoes.filter(s => s.id !== sessaoId);
    salvarNoStorage();
}

async function dbLimparMensagens(sessaoId) {
    const sessao = appState.sessoes.find(s => s.id === sessaoId);
    if (sessao) sessao.mensagens =[];
    salvarNoStorage();
}

// =====================================================================
// PARTE 2: CONTROLE DE INTERFACE (UI)
// =====================================================================

const chatBox = document.getElementById('chat-box');
const chatArea = document.getElementById('chat-area');
const blankState = document.getElementById('blank-state');

function getHoraAtual() {
    const agora = new Date();
    return agora.getHours().toString().padStart(2, '0') + ':' + agora.getMinutes().toString().padStart(2, '0');
}

// CARREGA A LISTA DE PACIENTES NA BARRA LATERAL
async function carregarSessoes() {
    const lista = document.getElementById('contact-list');
    lista.innerHTML = '';
    const sessoes = await dbGetSessoes();
    
    sessoes.forEach(sessao => {
        const div = document.createElement('div');
        div.className = 'contact';
        if(appState.sessaoAtualId === sessao.id) div.classList.add('active');
        
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
        
        div.onclick = () => abrirSessao(sessao.id);
        lista.appendChild(div);
    });
}

// ABRE O HISTÓRICO DE UM PACIENTE
async function abrirSessao(sessaoId) {
    appState.sessaoAtualId = sessaoId;
    await carregarSessoes(); 
    
    const sessao = appState.sessoes.find(s => s.id === sessaoId);
    if (!sessao) return;

    document.getElementById('header-name').textContent = sessao.nomePaciente;
    document.getElementById('header-avatar').style.backgroundImage = sessao.avatarBg;
    
    blankState.style.display = 'none';
    chatArea.style.display = 'flex';
    chatBox.innerHTML = ''; 
    
    sessao.mensagens.forEach(m => renderizarMensagemNaTela(m));
}

function renderizarMensagemNaTela(msg) {
    const div = document.createElement('div');
    div.classList.add('message', msg.tipo);
    
    if (msg.tipo === 'system') {
        div.innerHTML = `🔒 ${msg.texto}`;
    } else {
        let checkHtml = msg.tipo === 'sent' ? '<span class="msg-time" style="color:#53bdeb; margin-left:3px;">✓✓</span>' : '';
        div.innerHTML = `${msg.texto} <span class="msg-time">${msg.timestamp || getHoraAtual()} ${checkHtml}</span>`;
    }
    
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight; 
}

// LOGICA DE ENVIO DO PACIENTE E RESPOSTA DO BOT
async function enviarTexto() {
    const inputMsg = document.getElementById('input-msg');
    const texto = inputMsg.value.trim();
    if (!texto) return;
    
    inputMsg.value = '';
    
    // Registra a mensagem do paciente
    const msgSalva = await dbSalvarMensagem(appState.sessaoAtualId, texto, 'sent');
    renderizarMensagemNaTela(msgSalva);
    await carregarSessoes(); 

    // Identifica quantas mensagens o paciente enviou até agora
    const sessao = appState.sessoes.find(s => s.id === appState.sessaoAtualId);
    const qtdMensagensPaciente = sessao.mensagens.filter(m => m.tipo === 'sent').length;

    // Simula delay de digitação do bot
    setTimeout(async () => {
        let respostaBot = "";
        
        if (qtdMensagensPaciente === 1) {
            // Bot responde à PRIMEIRA interação do paciente
            respostaBot = "Olá! Sou o assistente cuidador virtual. Para acessarmos o seu diagnóstico e iniciarmos o acompanhamento, por favor, digite o seu CPF ou Número de Identificação.";
        } else {
            // Bot responde às interações SEGUINTES
            respostaBot = "Entendido. Registrei essa informação no seu prontuário. Lembre-se de manter o repouso e a hidratação!";
        }

        const msgRecebida = await dbSalvarMensagem(appState.sessaoAtualId, respostaBot, 'received');
        renderizarMensagemNaTela(msgRecebida);
        await carregarSessoes(); 
    }, 1200);
}

// =====================================================================
// PARTE 3: EVENTOS AUXILIARES (UI, ENTER, DROPDOWNS E MODAIS)
// =====================================================================

const inputMsg = document.getElementById('input-msg');
inputMsg.addEventListener('keypress', function(e) { 
    if (e.key === 'Enter' && this.value.trim() !== '') enviarTexto(); 
});

function fecharDropdowns() {
    document.querySelectorAll('.dropdown, .emoji-picker').forEach(m => m.classList.remove('active'));
}
document.addEventListener('click', fecharDropdowns);

function toggleDropdown(id, event) {
    event.stopPropagation();
    const menu = document.getElementById(id);
    if(menu.classList.contains('active')) {
        menu.classList.remove('active');
    } else {
        fecharDropdowns();
        menu.classList.add('active');
    }
}

function abrirModalInput(titulo) {
    fecharDropdowns();
    document.getElementById('modal-title').textContent = titulo;
    document.getElementById('modal-input').value = '';
    document.getElementById('input-modal').classList.add('active');
    document.getElementById('modal-input').focus();
}

function fecharModais() {
    document.querySelectorAll('.overlay').forEach(modal => modal.classList.remove('active'));
}

async function criarSessaoSimulada() {
    const nome = document.getElementById('modal-input').value.trim();
    if (nome !== '') {
        const cores =['#FF8008', '#11998e', '#4CB8C4', '#8A2387'];
        const corRandom = cores[Math.floor(Math.random() * cores.length)];
        const bgGradient = 'url("../images/Logo01.png")';

        const novaSessao = await dbCriarSessao(nome, bgGradient);
        fecharModais();
        await abrirSessao(novaSessao.id);
    }
}

async function apagarConversa() {
    if(appState.sessaoAtualId) {
        await dbApagarSessao(appState.sessaoAtualId);
        appState.sessaoAtualId = null;
    }
    chatArea.style.display = 'none';
    blankState.style.display = 'flex';
    fecharDropdowns();
    await carregarSessoes();
}

async function limparMensagens() {
    if(appState.sessaoAtualId) {
        await dbLimparMensagens(appState.sessaoAtualId);
        chatBox.innerHTML = '';
        await carregarSessoes();
    }
    fecharDropdowns();
}

function inserirEmoji(emoji) {
    inputMsg.value += emoji;
    inputMsg.focus();
}

function abrirChamada(tipo) {
    fecharDropdowns();
    document.getElementById('call-name').textContent = document.getElementById('header-name').textContent;
    document.getElementById('call-avatar').style.backgroundImage = document.getElementById('header-avatar').style.backgroundImage;
    document.getElementById('call-status').textContent = tipo === 'video' ? 'Chamada de vídeo simulada...' : 'Chamada de voz simulada...';
    document.getElementById('call-modal').classList.add('active');
}

document.getElementById('theme-toggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-theme');
    this.textContent = document.body.classList.contains('dark-theme') ? '🌙' : '🔆';
    fecharDropdowns();
});

// INIT AO CARREGAR A PÁGINA
window.onload = async () => {
    await carregarSessoes();
    if (appState.sessoes.length > 0) {
        abrirSessao(appState.sessoes[0].id);
    } else {
        blankState.style.display = 'flex';
    }
};