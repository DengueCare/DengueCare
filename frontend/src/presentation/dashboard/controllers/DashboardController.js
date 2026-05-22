import { PatientAPIRepository } from '../../../infrastructure/repositories/PatientAPIRepository.js';
import { GetPatientByIdUseCase, GetPatientsUseCase } from '../../../application/usecases/PatientUseCases.js';
import { API_BASE_URL } from '../../../config.js';

export class DashboardController {
    constructor() {
        const repo = new PatientAPIRepository();
        this.getPatientByIdUseCase = new GetPatientByIdUseCase(repo);
        this.getPatientsUseCase = new GetPatientsUseCase(repo);
        
        // Expose functions to the window object so inline HTML onclicks work without rewriting HTML
        window.fazerLogin = this.fazerLogin.bind(this);
        window.navegar = this.navegar.bind(this);
        window.abrirDetalhes = this.abrirDetalhes.bind(this);
        window.descartarAlerta = this.descartarAlerta.bind(this);
        window.toggleAuthMode = this.toggleAuthMode.bind(this);
        window.criarConta = this.criarConta.bind(this);
        window.fazerLogout = this.fazerLogout.bind(this);

        this.alertedPatients = new Set();
        this.alertasDescartados = {}; // Armazena { "id_paciente": "dt_ultima_triagem_descartada" }

        this.init();
    }

    async init() {
        // Verificar se há usuário logado no localStorage
        const user = localStorage.getItem('denguecare_user');
        if (user) {
            const loginScreen = document.getElementById('login-screen');
            const mainApp = document.getElementById('main-app');
            if (loginScreen) loginScreen.style.display = 'none';
            if (mainApp) mainApp.style.display = 'flex';
        }

        await this.carregarTabelaPacientes();
        // Polling para tempo real a cada 10 segundos
        setInterval(() => this.carregarTabelaPacientes(true), 10000);
    }

    async carregarTabelaPacientes(isPolling = false) {
        const tbody = document.getElementById('lista-pacientes-tabela');
        if (!tbody) return; 

        tbody.innerHTML = ''; 

        // Adiciona um loading visual apenas na primeira carga
        if (!isPolling) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #666; padding: 30px;">Carregando pacientes da API...</td></tr>`;
        }

        const pacientesDict = await this.getPatientsUseCase.execute();
        const pacientesArray = Object.values(pacientesDict || {});

        tbody.innerHTML = ''; 

        if (pacientesArray.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 40px; color: #888;">
                        <div style="font-size: 30px; margin-bottom: 10px;">📋</div>
                        <strong>Nenhum paciente cadastrado</strong>
                        <p style="font-size: 13px; margin-top: 5px;">A fila está vazia no momento.</p>
                    </td>
                </tr>
            `;
            
            // Atualiza os contadores estáticos da tela para 0
            document.querySelectorAll('.stat-card h2').forEach(el => el.textContent = '0');
            return;
        }

        pacientesArray.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="patient-name-col">
                        <div class="avatar-sm">${p.iniciais || p.nome.substring(0, 2).toUpperCase()}</div>
                        <strong>${p.nome}</strong>
                    </div>
                </td>
                <td><span class="badge ${p.riscoBadge || 'badge-green'}">${p.riscoTexto || 'Risco Indefinido'}</span></td>
                <td>${p.dias || 0} dias</td>
                <td><a class="action-link" style="cursor: pointer;" onclick="abrirDetalhes('${p.id || Object.keys(pacientesDict).find(k => pacientesDict[k] === p)}')">Ver Detalhes</a></td>
            `;
            tbody.appendChild(tr);

            // Alerta de Piora Clínica
            if (p.piorou && !this.alertedPatients.has(p.id)) {
                this.alertedPatients.add(p.id);
                this.mostrarAlertaPiora(p);
            }
        });
        
        // Atualiza a Visão Geral com o feed dinâmico de alertas cronológicos
        this.renderizarAlertas(pacientesArray);
    }

    mostrarAlertaPiora(paciente) {
        const alertBox = document.getElementById('global-alert');
        const alertText = document.getElementById('global-alert-text');
        
        if (alertBox && alertText) {
            alertText.innerHTML = `O paciente <strong>${paciente.nome}</strong> apresentou piora para <strong>${paciente.riscoTexto}</strong>.`;
            alertBox.classList.add('show');
            alertBox.classList.add('flash');
            
            // Toca um beep (opcional)
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'); // Beep simples em base64 ou som curto
                audio.play().catch(e => {});
            } catch(e) {}
        }
    }

    renderizarAlertas(pacientesArray) {
        const container = document.getElementById('alerts-container');
        const countLabel = document.getElementById('alerts-count');
        
        if (!container || !countLabel) return;

        // Filtrar pacientes graves ou que tiveram piora, e que NÃO foram descartados na triagem atual
        let alertas = pacientesArray.filter(p => {
            const isGraveOuPiorou = p.piorou || p.riscoPuro === 'C' || p.riscoPuro === 'D';
            const isDescartadoNestaTriagem = this.alertasDescartados[p.id] && this.alertasDescartados[p.id] === p.dt_ultima_triagem;
            return isGraveOuPiorou && !isDescartadoNestaTriagem;
        });

        // Ordenar cronologicamente pelo dt_ultima_triagem (mais recente no topo)
        alertas.sort((a, b) => {
            const dataA = a.dt_ultima_triagem ? new Date(a.dt_ultima_triagem) : new Date(0);
            const dataB = b.dt_ultima_triagem ? new Date(b.dt_ultima_triagem) : new Date(0);
            return dataB - dataA;
        });

        // Atualizar contador
        countLabel.textContent = `${alertas.length} paciente${alertas.length !== 1 ? 's' : ''} requerem atenção imediata`;

        if (alertas.length === 0) {
            container.innerHTML = '<p style="color: #666; font-size: 13px; text-align: center; padding: 20px;">Nenhum alerta crítico no momento.</p>';
            return;
        }

        container.innerHTML = '';
        
        alertas.forEach(alerta => {
            // Calcular tempo decorrido
            let timeAgo = "recentemente";
            if (alerta.dt_ultima_triagem) {
                const diffMs = new Date() - new Date(alerta.dt_ultima_triagem);
                const diffMin = Math.floor(diffMs / 60000);
                if (diffMin < 60) timeAgo = `há ${diffMin} minuto${diffMin !== 1 ? 's' : ''}`;
                else {
                    const diffHr = Math.floor(diffMin / 60);
                    timeAgo = `há ${diffHr} hora${diffHr !== 1 ? 's' : ''}`;
                }
            }

            const card = document.createElement('div');
            card.className = 'alert-card';
            card.onclick = () => window.abrirDetalhes(alerta.id);
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h4>${alerta.nome}</h4>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="badge ${alerta.riscoBadge}" style="font-size: 11px;">${alerta.riscoTexto}</span>
                        <span style="color: #999; cursor: pointer; font-size: 16px;" onclick="event.stopPropagation(); window.descartarAlerta('${alerta.id}', '${alerta.dt_ultima_triagem}')" title="Descartar Alerta">✕</span>
                    </div>
                </div>
                <p>O paciente encontra-se em quadro clínico de alto risco (Gravidade ou Piora recente). Requer avaliação médica prioritária.</p>
                <span class="time-ago">${timeAgo}</span>
            `;
            container.appendChild(card);
        });
    }

    descartarAlerta(pacienteId, dtUltimaTriagem) {
        // Registra que esse alerta específico foi fechado pelo usuário
        this.alertasDescartados[pacienteId] = dtUltimaTriagem;
        // Força a re-renderização puxando a tabela novamente (o filtro vai atuar)
        this.carregarTabelaPacientes();
    }

    toggleAuthMode(mode) {
        if (mode === 'register') {
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('reg-error').style.display = 'none';
        } else {
            document.getElementById('form-register').style.display = 'none';
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('login-error').style.display = 'none';
        }
    }

    async fazerLogin() {
        const id = document.getElementById('login-id').value.trim();
        const senha = document.getElementById('login-senha').value.trim();
        const errorEl = document.getElementById('login-error');
        
        if(id === '' || senha === '') {
            errorEl.textContent = 'Preencha todos os campos!';
            errorEl.style.display = 'block';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ carteira: id, senha: senha })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Guarda um "token" ou info no localStorage se quiser manter a sessão
                localStorage.setItem('denguecare_user', JSON.stringify(data.data));
                
                document.getElementById('login-screen').style.display = 'none';
                document.getElementById('main-app').style.display = 'flex';
                
                // Atualizar o nome do médico logado na sidebar (opcional)
                // Ex: document.querySelector('.doctor-name').textContent = data.data.nome;
            } else {
                errorEl.textContent = data.detail || 'Carteira ou senha incorretos.';
                errorEl.style.display = 'block';
            }
        } catch (error) {
            console.error(error);
            errorEl.textContent = 'Erro de conexão com o servidor.';
            errorEl.style.display = 'block';
        }
    }

    fazerLogout() {
        // Remover dados de login da sessão local
        localStorage.removeItem('denguecare_user');
        
        // Ocultar painel principal e mostrar tela de login
        const loginScreen = document.getElementById('login-screen');
        const mainApp = document.getElementById('main-app');
        if (loginScreen) loginScreen.style.display = 'flex';
        if (mainApp) mainApp.style.display = 'none';

        // Resetar campos de entrada
        const idInput = document.getElementById('login-id');
        const passInput = document.getElementById('login-senha');
        if (idInput) idInput.value = '';
        if (passInput) passInput.value = '';

        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.style.display = 'none';
    }

    async criarConta() {
        const nome = document.getElementById('reg-nome').value.trim();
        const id = document.getElementById('reg-id').value.trim();
        const senha = document.getElementById('reg-senha').value.trim();
        const errorEl = document.getElementById('reg-error');
        
        if(nome === '' || id === '' || senha === '') {
            errorEl.textContent = 'Preencha todos os campos!';
            errorEl.style.display = 'block';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: nome, carteira: id, senha: senha })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Conta criada com sucesso! Faça login para continuar.');
                this.toggleAuthMode('login');
                document.getElementById('login-id').value = id;
                document.getElementById('login-senha').value = '';
            } else {
                errorEl.textContent = data.detail || 'Erro ao criar conta. Verifique se a carteirinha já existe.';
                errorEl.style.display = 'block';
            }
        } catch (error) {
            console.error(error);
            errorEl.textContent = 'Erro de conexão com o servidor.';
            errorEl.style.display = 'block';
        }
    }

    navegar(idView, elementoMenu = null) {
        document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
        document.getElementById('view-' + idView).classList.add('active');

        if (elementoMenu) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            elementoMenu.classList.add('active');
        }
    }

    async abrirDetalhes(idPac) {
        const p = await this.getPatientByIdUseCase.execute(idPac);
        if(!p) {
            alert("Paciente não encontrado ou indisponível.");
            return;
        }

        document.getElementById('det-avatar').textContent = p.iniciais || p.nome.substring(0, 2).toUpperCase();
        document.getElementById('det-nome').textContent = p.nome;
        document.getElementById('det-idade').textContent = p.idade;
        document.getElementById('det-tel').textContent = p.tel ? ('📞 ' + p.tel) : '';
        
        const btnLigar = document.getElementById('btn-ligar');
        const btnWpp = document.getElementById('btn-whatsapp');
        
        if (p.tel && p.tel.trim() !== '') {
            const numeroLimpo = p.tel.replace(/\D/g, '');
            
            // Botão Clássico de Ligação
            if (btnLigar) {
                btnLigar.href = `tel:+55${numeroLimpo}`;
                btnLigar.style.pointerEvents = 'auto';
                btnLigar.style.opacity = '1';
                btnLigar.title = "Iniciar chamada telefônica";
            }
            
            // Botão WhatsApp Web Direto (pula a tela de download)
            if (btnWpp) {
                btnWpp.href = `https://web.whatsapp.com/send?phone=55${numeroLimpo}&text=Olá,%20aqui%20é%20da%20equipe%20DengueCare.`;
                btnWpp.style.pointerEvents = 'auto';
                btnWpp.style.opacity = '1';
                btnWpp.title = "Abrir conversa no WhatsApp Web";
            }
        } else {
            if (btnLigar) {
                btnLigar.removeAttribute('href');
                btnLigar.style.pointerEvents = 'none';
                btnLigar.style.opacity = '0.5';
                btnLigar.title = "Sem telefone";
            }
            if (btnWpp) {
                btnWpp.removeAttribute('href');
                btnWpp.style.pointerEvents = 'none';
                btnWpp.style.opacity = '0.5';
                btnWpp.title = "Sem telefone";
            }
        }

        document.getElementById('det-status-box').textContent = p.status || p.statusBox;
        document.getElementById('det-score').textContent = p.score || p.scoreAtual;
        
        const trendEl = document.getElementById('det-trend');
        trendEl.textContent = p.trend;
        trendEl.style.color = p.trendColor || '#666';
        
        const badge = document.getElementById('det-badge');
        badge.textContent = p.grupo || p.grupoAtual;
        badge.className = 'badge ' + (p.grupo === 'Grupo C' ? 'badge-orange-outline' : 'badge-yellow-outline');

        const comorbContainer = document.getElementById('det-comorb');
        comorbContainer.innerHTML = '';
        if (p.comorb || p.comorbidades) {
            (p.comorb || p.comorbidades).forEach(c => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.textContent = c;
                comorbContainer.appendChild(span);
            });
        }

        const histContainer = document.getElementById('det-historico-container');
        histContainer.innerHTML = '';
        if (p.historico) {
            p.historico.forEach(h => {
                let vitaisHtml = '';
                if(h.vitais || (h.temp && h.pa && h.bpm)) {
                    vitaisHtml = `
                        <div class="vitals-grid">
                            <div><p>Temp</p><strong>${h.vitais?.t || h.temp}</strong></div>
                            <div><p>PA</p><strong>${h.vitais?.p || h.pa}</strong></div>
                            <div><p>BPM</p><strong>${h.vitais?.b || h.bpm}</strong></div>
                        </div>
                    `;
                }

                let sintomasHtml = '';
                if (h.sintomas) {
                    h.sintomas.forEach(s => {
                        sintomasHtml += `<span class="tag ${s.c || s.classe}">${s.n || s.nome}</span> `;
                    });
                }

                const histCard = `
                    <div class="history-card">
                        <div class="history-header">
                            <div><strong>Dia ${h.dia}</strong></div>
                            <span class="badge ${h.grupo === 'Grupo C' ? 'badge-orange-outline' : 'badge-yellow-outline'}">${h.grupo}</span>
                        </div>
                        ${vitaisHtml}
                        <div class="tags-container">${sintomasHtml}</div>
                    </div>
                `;
                histContainer.innerHTML += histCard;
            });
        }

        this.renderizarGrafico(p.grafico || p.dadosGrafico);
        this.navegar('detalhes');
    }

    renderizarGrafico(dados) {
        const ctx = document.getElementById('riscoChart').getContext('2d');
        if(window.meuGrafico) window.meuGrafico.destroy();
        
        // Tratamento de erro: se não houver dados
        if (!dados || dados.length === 0) {
            // Oculta canvas ou reseta e sai
            return;
        }

        window.meuGrafico = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dados.map((_, i) => 'D' + (i+1)),
                datasets: [{
                    label: 'Pontuação de Risco',
                    data: dados,
                    borderColor: '#1a73e8',
                    backgroundColor: 'rgba(26, 115, 232, 0.1)',
                    borderWidth: 3,
                    pointBackgroundColor: '#1a73e8',
                    pointRadius: 6,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 }, x: { grid: { display: false } } }
            }
        });
    }
}

// Initialize the controller
new DashboardController();
