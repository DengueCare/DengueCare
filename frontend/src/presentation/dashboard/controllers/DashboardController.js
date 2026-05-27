import { PatientAPIRepository } from '../../../infrastructure/repositories/PatientAPIRepository.js?v=3';
import { GetPatientByIdUseCase, GetPatientsUseCase } from '../../../application/usecases/PatientUseCases.js';
import { API_BASE_URL } from '../../../config.js';

export class DashboardController {
    constructor() {
        const repo = new PatientAPIRepository();
        this.repo = repo;
        this.getPatientByIdUseCase = new GetPatientByIdUseCase(repo);
        this.getPatientsUseCase = new GetPatientsUseCase(repo);
        
        this.pacientesExibidos = [];
        this.ordenacao = { campo: null, direcao: 'asc' };
        this.chartRiscoInstance = null;
        this.chartIdadesInstance = null;
        this.chartSintomasInstance = null;
        this.chartAdmissoesInstance = null;
        
        // Expose functions to the window object so inline HTML onclicks work without rewriting HTML
        window.fazerLogin = this.fazerLogin.bind(this);
        window.navegar = this.navegar.bind(this);
        window.abrirDetalhes = this.abrirDetalhes.bind(this);
        window.descartarAlerta = this.descartarAlerta.bind(this);
        window.toggleAuthMode = this.toggleAuthMode.bind(this);
        window.toggleAdminRegistration = this.toggleAdminRegistration.bind(this);
        window.obterPerguntaSeguranca = this.obterPerguntaSeguranca.bind(this);
        window.redefinirSenha = this.redefinirSenha.bind(this);
        window.criarConta = this.criarConta.bind(this);
        window.fazerLogout = this.fazerLogout.bind(this);
        window.ordenarPor = this.ordenarPor.bind(this);
        window.filtrarPacientes = this.filtrarPacientes.bind(this);
        window.abrirModalCadastro = this.abrirModalCadastro.bind(this);
        window.fecharModalCadastro = this.fecharModalCadastro.bind(this);
        window.submeterPaciente = this.submeterPaciente.bind(this);
        window.editarPacienteAtual = this.editarPacienteAtual.bind(this);
        window.abrirModalInativarPaciente = this.abrirModalInativarPaciente.bind(this);
        window.confirmarInativarPaciente = this.confirmarInativarPaciente.bind(this);
        window.salvarConfiguracoes = this.salvarConfiguracoes.bind(this);
        window.inativarCadastroMedico = this.inativarCadastroMedico.bind(this);
        window.toggleAdmissionsChart = this.toggleAdmissionsChart.bind(this);
        window.filtrarGraficoAdmissoes = this.filtrarGraficoAdmissoes.bind(this);
        window.toggleAdminSubTab = this.toggleAdminSubTab.bind(this);
        window.reactivarUsuarioPaciente = this.reactivarUsuarioPaciente.bind(this);
        window.reactivarUsuarioProfissional = this.reactivarUsuarioProfissional.bind(this);
        window.toggleAdminStatusProfissional = this.toggleAdminStatusProfissional.bind(this);

        this.alertedPatients = new Set();
        this.alertasDescartados = {}; // Armazena { "id_paciente": "dt_ultima_triagem_descartada" }

        this.init();
    }

    async init() {
        // Verificar se há usuário logado no localStorage
        const userStr = localStorage.getItem('denguecare_user');
        if (userStr) {
            const user = JSON.parse(userStr);
            const loginScreen = document.getElementById('login-screen');
            const mainApp = document.getElementById('main-app');
            if (loginScreen) loginScreen.style.display = 'none';
            if (mainApp) mainApp.style.display = 'flex';
            
            this.atualizarPerfilSidebar(user);
        }

        await this.carregarEstatisticas();
        await this.carregarTabelaPacientes();
        // Polling para tempo real a cada 10 segundos
        setInterval(async () => {
            await this.carregarTabelaPacientes(true);
            await this.carregarEstatisticas();
        }, 10000);
    }

    async carregarEstatisticas() {
        try {
            const repo = new PatientAPIRepository();
            const stats = await repo.getDashboardStats();
            if (!stats) return;

            const totalEl = document.getElementById('metric-total');
            const altoRiscoEl = document.getElementById('metric-alto-risco');
            const admissoesEl = document.getElementById('metric-admissoes');

            if (totalEl) totalEl.textContent = stats.total_pacientes ?? 0;
            if (altoRiscoEl) altoRiscoEl.textContent = stats.alto_risco ?? 0;
            if (admissoesEl) admissoesEl.textContent = stats.admissoes_hoje ?? 0;

            const trendAltoRiscoEl = document.getElementById('trend-alto-risco');
            if (trendAltoRiscoEl && stats.alto_risco_delta !== undefined) {
                const delta = stats.alto_risco_delta;
                if (delta > 0) {
                    trendAltoRiscoEl.textContent = `▲ +${delta} hoje`;
                    trendAltoRiscoEl.className = 'stat-trend red';
                    trendAltoRiscoEl.style.display = 'inline-block';
                } else if (delta < 0) {
                    trendAltoRiscoEl.textContent = `▼ ${delta} hoje`;
                    trendAltoRiscoEl.className = 'stat-trend green';
                    trendAltoRiscoEl.style.display = 'inline-block';
                } else {
                    trendAltoRiscoEl.style.display = 'none';
                }
            }

            const trendAdmissoesEl = document.getElementById('trend-admissoes');
            if (trendAdmissoesEl && stats.admissoes_delta !== undefined) {
                const delta = stats.admissoes_delta;
                if (delta > 0) {
                    trendAdmissoesEl.textContent = `▲ +${delta} em relação a ontem`;
                    trendAdmissoesEl.className = 'stat-trend green';
                    trendAdmissoesEl.style.display = 'inline-block';
                } else if (delta < 0) {
                    trendAdmissoesEl.textContent = `▼ ${delta} em relação a ontem`;
                    trendAdmissoesEl.className = 'stat-trend red';
                    trendAdmissoesEl.style.display = 'inline-block';
                } else {
                    trendAdmissoesEl.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas do dashboard:', error);
        }
    }

    atualizarAlertasCriticos(pacientesArray) {
        // Delega inteiramente para renderizarAlertas para centralizar lógica e evitar conflitos de DOM concorrente
        this.renderizarAlertas(pacientesArray);
    }

    async carregarTabelaPacientes(isPolling = false) {
        const tbody = document.getElementById('lista-pacientes-tabela');
        if (!tbody) return; 

        // Adiciona um loading visual apenas na primeira carga
        if (!isPolling && tbody.innerHTML.trim() === '') {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #666; padding: 30px;">Carregando pacientes da API...</td></tr>`;
        }

        try {
            const pacientesDict = await this.getPatientsUseCase.execute();
            const pacientesArray = Object.values(pacientesDict || {}).map(p => {
                if (p.dt_sin_pri) {
                    const diffTime = Math.abs(new Date() - new Date(p.dt_sin_pri));
                    p.dias = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                }
                // Garante que o campo grupoAtual esteja mapeado corretamente para o frontend
                p.grupoAtual = p.grupoAtual || p.riscoTexto || (p.riscoPuro ? 'Grupo ' + p.riscoPuro : '') || 'Grupo A';
                return p;
            });

            this.atualizarAlertasCriticos(pacientesArray);

            const countBox = document.getElementById('total-pacientes-list-count');
            if (countBox) {
                countBox.textContent = pacientesArray.length;
            }

            this.pacientesExibidos = pacientesArray;

            if (this.ordenacao.campo) {
                this.aplicarOrdenacao();
            }

            this.renderizarPacientesNaTabela();
        } catch (error) {
            console.error("Erro ao carregar tabela de pacientes:", error);
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red; padding: 30px;">Erro ao carregar dados da API.</td></tr>`;
        }
    }

    renderizarPacientesNaTabela() {
        const tbody = document.getElementById('lista-pacientes-tabela');
        if (!tbody) return;

        tbody.innerHTML = ''; 

        if (this.pacientesExibidos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 40px; color: #888;">
                        <div style="font-size: 30px; margin-bottom: 10px;">📋</div>
                        <strong>Nenhum paciente cadastrado</strong>
                        <p style="font-size: 13px; margin-top: 5px;">A fila está vazia no momento.</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.pacientesExibidos.forEach(p => {
            let riscoBadgeClass = 'badge-gray';
            const riscoNome = p.grupoAtual || p.riscoTexto || '';
            if (riscoNome.includes('Grupo A')) riscoBadgeClass = 'badge-blue';
            else if (riscoNome.includes('Grupo B')) riscoBadgeClass = 'badge-green';
            else if (riscoNome.includes('Grupo C')) riscoBadgeClass = 'badge-yellow';
            else if (riscoNome.includes('Grupo D')) riscoBadgeClass = 'badge-red';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="patient-name-col">
                        <div class="avatar-sm">${p.iniciais || p.nome.substring(0, 2).toUpperCase()}</div>
                        <strong>${p.nome}</strong>
                    </div>
                </td>
                <td><span class="badge ${riscoBadgeClass}">${riscoNome || 'Risco Indefinido'}</span></td>
                <td>${p.dias || 0} dias</td>
                <td><a class="action-link" style="cursor: pointer;" onclick="window.abrirDetalhes('${p.id}')">Ver Detalhes</a></td>
            `;
            tbody.appendChild(tr);

            // Alerta de Piora Clínica
            if (p.piorou && !this.alertedPatients.has(p.id)) {
                this.alertedPatients.add(p.id);
                this.mostrarAlertaPiora(p);
            }
        });
        
        // Atualiza a Visão Geral com o feed dinâmico de alertas cronológicos
        this.renderizarAlertas(this.pacientesExibidos);
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

        // Se não houver nenhum alerta ativo, exibe o banner verde de sucesso
        if (alertas.length === 0) {
            container.innerHTML = `
                <div class="alert-card" style="border-color: #e6f4ea; background: #f4fbf7; pointer-events: none; margin-bottom: 0; padding: 15px; border-radius: 8px; border: 1px solid #e6f4ea;">
                    <div style="color: #1e8e3e; font-weight: 600; display: flex; align-items: center; gap: 8px; font-size: 14px;">
                        <span>✅</span> Sem alertas de urgência ou alto risco no momento.
                    </div>
                </div>
            `;
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

            // Define descrição do alerta de forma premium e detalhada baseada no grupo (C vs D)
            let desc = alerta.grupoAtual === 'Grupo D' 
                ? 'Sinais de choque/gravidade máxima detectados. Encaminhamento imediato.' 
                : 'Sinais de alarme ativos. Requer avaliação prioritária.';
            
            if (alerta.comorbidades && alerta.comorbidades.length > 0) {
                desc += ` Comorbidades: ${alerta.comorbidades.join(', ')}.`;
            }

            const card = document.createElement('div');
            card.className = 'alert-card';
            card.onclick = () => window.abrirDetalhes(alerta.id);
            card.style.cursor = 'pointer';
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h4 style="margin: 0; font-size: 14px; color: var(--text-main); font-weight: 600;">${alerta.nome}</h4>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="badge ${alerta.riscoBadge || 'badge-red'}" style="font-size: 11px;">${alerta.grupoAtual}</span>
                        <span style="color: #999; cursor: pointer; font-size: 16px; transition: color 0.2s;" onmouseover="this.style.color='#f44336'" onmouseout="this.style.color='#999'" onclick="event.stopPropagation(); window.descartarAlerta('${alerta.id}', '${alerta.dt_ultima_triagem}')" title="Descartar Alerta">✕</span>
                    </div>
                </div>
                <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin: 8px 0;">${desc}</p>
                <span class="time-ago" style="font-size: 11px; color: #999;">${timeAgo}</span>
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

    ordenarPor(campo) {
        if (this.ordenacao.campo === campo) {
            this.ordenacao.direcao = this.ordenacao.direcao === 'asc' ? 'desc' : 'asc';
        } else {
            this.ordenacao.campo = campo;
            this.ordenacao.direcao = 'asc';
        }

        this.atualizarIconesOrdenacao();
        this.aplicarOrdenacao();
        this.renderizarPacientesNaTabela();
    }

    atualizarIconesOrdenacao() {
        const icones = {
            nome: document.getElementById('sort-nome-icon'),
            risco: document.getElementById('sort-risco-icon'),
            dias: document.getElementById('sort-dias-icon')
        };

        for (const key in icones) {
            if (icones[key]) {
                icones[key].textContent = '⇅';
                icones[key].style.color = '#aaa';
            }
        }

        const activeIcon = icones[this.ordenacao.campo];
        if (activeIcon) {
            activeIcon.textContent = this.ordenacao.direcao === 'asc' ? '▲' : '▼';
            activeIcon.style.color = 'var(--primary-blue)';
        }
    }

    aplicarOrdenacao() {
        const campo = this.ordenacao.campo;
        const direcao = this.ordenacao.direcao;

        const getGrupoRisco = p => {
            const gr = p.grupoAtual || p.grupo || p.riscoTexto || '';
            if (gr.includes('D')) return 4;
            if (gr.includes('C')) return 3;
            if (gr.includes('B')) return 2;
            if (gr.includes('A')) return 1;
            return 0;
        };

        this.pacientesExibidos.sort((a, b) => {
            let valA, valB;

            if (campo === 'nome') {
                valA = (a.nome || '').toLowerCase();
                valB = (b.nome || '').toLowerCase();
                if (valA < valB) return direcao === 'asc' ? -1 : 1;
                if (valA > valB) return direcao === 'asc' ? 1 : -1;
                return 0;
            } else if (campo === 'risco') {
                valA = getGrupoRisco(a);
                valB = getGrupoRisco(b);
                return direcao === 'asc' ? valA - valB : valB - valA;
            } else if (campo === 'dias') {
                valA = Number(a.dias || 0);
                valB = Number(b.dias || 0);
                return direcao === 'asc' ? valA - valB : valB - valA;
            }
            return 0;
        });
    }

    toggleAuthMode(mode) {
        document.getElementById('form-login').style.display = 'none';
        document.getElementById('form-register').style.display = 'none';
        document.getElementById('form-recovery').style.display = 'none';
        
        if (mode === 'register') {
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('reg-error').style.display = 'none';
            const regIsAdmin = document.getElementById('reg-is-admin');
            if (regIsAdmin) regIsAdmin.checked = false;
            this.toggleAdminRegistration(false);
        } else if (mode === 'recovery') {
            document.getElementById('form-recovery').style.display = 'block';
            document.getElementById('rec-error').style.display = 'none';
            document.getElementById('rec-success').style.display = 'none';
            document.getElementById('recovery-step-1').style.display = 'block';
            document.getElementById('recovery-step-2').style.display = 'none';
            document.getElementById('rec-id').value = '';
            document.getElementById('rec-resposta').value = '';
            document.getElementById('rec-nova-senha').value = '';
        } else {
            document.getElementById('form-login').style.display = 'block';
            document.getElementById('login-error').style.display = 'none';
        }
    }

    toggleAdminRegistration(checked) {
        const regIdInput = document.getElementById('reg-id');
        if (regIdInput) {
            const group = regIdInput.parentElement;
            const groupLabel = group.querySelector('label');
            if (groupLabel) {
                groupLabel.innerHTML = checked 
                    ? "Identificador do Administrador <strong>*</strong> (ex: admin_joao)" 
                    : "Número da Carteirinha (CRM/COREN) <strong>*</strong>";
            }
            regIdInput.placeholder = checked
                ? "Ex: admin_hospital"
                : "Ex: CRM/SP 123456";
        }
    }

    validarCarteiraProfissional(carteirinha, isAdmin = false) {
        const credencial = carteirinha.trim().toUpperCase();

        // Se for cadastrado como administrador ou o login começar com "ADMIN", ignora a validação do CRM/COREN
        if (isAdmin || credencial.startsWith('ADMIN')) {
            return credencial.length >= 4; // Exige pelo menos 4 caracteres
        }

        // Regex CRM: Exige 'CRM/' seguido de 2 letras da UF, espaço e números (Ex: CRM/SP 123456)
        const regexCRM = /^CRM\/[A-Z]{2}\s\d+$/;
        
        // Regex COREN: Exige 'COREN-' seguido de 2 letras da UF, espaço, números, hífen e a sigla da categoria (Ex: COREN-SP 123456-ENF)
        const regexCOREN = /^COREN-[A-Z]{2}\s\d+-[A-Z]{2,3}$/;

        return regexCRM.test(credencial) || regexCOREN.test(credencial);
    }

    validarSenha(senha) {
        if (senha.length < 8) {
            return "A senha deve ter pelo menos 8 caracteres.";
        }
        if (!/[A-Z]/.test(senha)) {
            return "A senha deve conter pelo menos uma letra maiúscula.";
        }
        if (!/[^a-zA-Z0-9áéíóúÁÉÍÓÚâêîôûÂÊÎÔÛãõÃÕçÇ\s]/.test(senha)) {
            return "A senha deve conter pelo menos um caractere especial.";
        }
        return null;
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

        if (!this.validarCarteiraProfissional(id) && !this.validarCarteiraProfissional(id, true)) {
            errorEl.textContent = "Formato inválido! Use 'CRM/XX 000000', 'COREN-XX 000000-SIGLA' ou seu identificador admin.";
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
                
                this.atualizarPerfilSidebar(data.data);
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
        const nomeEl = document.getElementById('reg-nome');
        const idEl = document.getElementById('reg-id');
        const senhaEl = document.getElementById('reg-senha');
        const perguntaEl = document.getElementById('reg-pergunta');
        const respostaEl = document.getElementById('reg-resposta');
        const isAdminEl = document.getElementById('reg-is-admin');
        const errorEl = document.getElementById('reg-error');
        
        if (!nomeEl || !idEl || !senhaEl || !errorEl) {
            console.error("Elementos do formulário de cadastro não foram encontrados no DOM!");
            alert("Erro: O formulário de cadastro está desatualizado no cache do seu navegador. Por favor, limpe o histórico/cache e atualize a página.");
            return;
        }

        const nome = nomeEl.value.trim();
        const id = idEl.value.trim();
        const senha = senhaEl.value.trim();
        const pergunta = perguntaEl ? perguntaEl.value : "";
        const resposta = respostaEl ? respostaEl.value.trim() : "";
        const isAdmin = isAdminEl ? isAdminEl.checked : false;
        
        if(nome === '' || id === '' || senha === '' || (perguntaEl && pergunta === '') || (respostaEl && resposta === '')) {
            errorEl.textContent = 'Preencha todos os campos obrigatórios!';
            errorEl.style.display = 'block';
            return;
        }

        if (!this.validarCarteiraProfissional(id, isAdmin)) {
            errorEl.textContent = isAdmin
                ? "Identificador de administrador inválido! Deve conter pelo menos 4 caracteres."
                : "Formato inválido! Use 'CRM/XX 000000' ou 'COREN-XX 000000-SIGLA'.";
            errorEl.style.display = 'block';
            return;
        }

        const erroSenha = this.validarSenha(senha);
        if (erroSenha) {
            errorEl.textContent = erroSenha;
            errorEl.style.display = 'block';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    nome: nome, 
                    carteira: id, 
                    senha: senha,
                    pergunta_seguranca: pergunta,
                    resposta_seguranca: resposta,
                    is_admin: isAdmin
                })
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

    async obterPerguntaSeguranca() {
        const id = document.getElementById('rec-id').value.trim();
        const errorEl = document.getElementById('rec-error');
        
        if (id === '') {
            errorEl.textContent = 'Preencha o CRM/COREN ou usuário admin!';
            errorEl.style.display = 'block';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/auth/recovery-question?carteira=${id}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                errorEl.style.display = 'none';
                document.getElementById('rec-pergunta-texto').textContent = data.pergunta;
                document.getElementById('recovery-step-1').style.display = 'none';
                document.getElementById('recovery-step-2').style.display = 'block';
            } else {
                errorEl.textContent = data.detail || 'Não foi possível encontrar a pergunta de segurança para essa conta.';
                errorEl.style.display = 'block';
            }
        } catch (error) {
            console.error(error);
            errorEl.textContent = 'Erro de conexão com o servidor.';
            errorEl.style.display = 'block';
        }
    }

    async redefinirSenha() {
        const id = document.getElementById('rec-id').value.trim();
        const resposta = document.getElementById('rec-resposta').value.trim();
        const novaSenha = document.getElementById('rec-nova-senha').value.trim();
        const errorEl = document.getElementById('rec-error');
        const successEl = document.getElementById('rec-success');
        
        if (resposta === '' || novaSenha === '') {
            errorEl.textContent = 'Preencha todos os campos!';
            errorEl.style.display = 'block';
            return;
        }

        // Validação dos critérios de força da nova senha
        const erroSenha = this.validarSenha(novaSenha);
        if (erroSenha) {
            errorEl.textContent = erroSenha;
            errorEl.style.display = 'block';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/auth/recover-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    carteira: id,
                    resposta: resposta,
                    nova_senha: novaSenha
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                errorEl.style.display = 'none';
                successEl.textContent = 'Senha redefinida com sucesso! Redirecionando...';
                successEl.style.display = 'block';
                
                setTimeout(() => {
                    this.toggleAuthMode('login');
                    document.getElementById('login-id').value = id;
                    document.getElementById('login-senha').value = '';
                }, 2000);
            } else {
                errorEl.textContent = data.detail || 'Resposta de segurança incorreta ou erro ao redefinir.';
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

        if (idView === 'relatorios') {
            this.carregarRelatorios();
        } else if (idView === 'configuracoes') {
            this.carregarConfiguracoes();
        } else if (idView === 'administracao') {
            this.carregarAdministracao();
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
        document.getElementById('det-idade').textContent = p.idade + ' anos';
        const telefone = p.tel || p.telefone;
        document.getElementById('det-tel').textContent = telefone ? ('📞 ' + telefone) : '';
        
        const btnLigar = document.getElementById('btn-ligar');
        const btnWpp = document.getElementById('btn-whatsapp');
        
        if (telefone && telefone.trim() !== '') {
            const numeroLimpo = telefone.replace(/\D/g, '');
            
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
        trendEl.textContent = p.trend || '';
        trendEl.style.color = p.trendColor || '#666';
        
        let riscoBadgeClass = 'badge-gray';
        const riscoNome = p.grupo || p.grupoAtual || 'Risco Indefinido';
        if (riscoNome.includes('Grupo A')) riscoBadgeClass = 'badge-blue';
        else if (riscoNome.includes('Grupo B')) riscoBadgeClass = 'badge-green';
        else if (riscoNome.includes('Grupo C')) riscoBadgeClass = 'badge-yellow';
        else if (riscoNome.includes('Grupo D')) riscoBadgeClass = 'badge-red';

        const badge = document.getElementById('det-badge');
        badge.textContent = riscoNome;
        badge.className = 'badge ' + riscoBadgeClass;

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

                let histBadgeClass = 'badge-green';
                if (h.grupo === 'Grupo D') histBadgeClass = 'badge-red';
                else if (h.grupo === 'Grupo C') histBadgeClass = 'badge-orange-outline';
                else if (h.grupo === 'Grupo B') histBadgeClass = 'badge-yellow';

                const histCard = `
                    <div class="history-card">
                        <div class="history-header">
                            <div><strong>Dia ${h.dia}</strong></div>
                            <span class="badge ${histBadgeClass}">${h.grupo}</span>
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

    async toggleAdmissionsChart() {
        const container = document.getElementById('admissoes-chart-container');
        if (!container) return;

        if (container.style.display === 'none') {
            container.style.display = 'block';
            await this.atualizarGraficoAdmissoes(7); // padrão: 7 dias
        } else {
            container.style.display = 'none';
        }
    }

    async filtrarGraficoAdmissoes(dias, buttonEl) {
        const buttons = document.querySelectorAll('.chart-filter-buttons .btn-filter');
        buttons.forEach(btn => btn.classList.remove('active'));
        if (buttonEl) buttonEl.classList.add('active');

        await this.atualizarGraficoAdmissoes(dias);
    }

    async atualizarGraficoAdmissoes(dias) {
        try {
            const data = await this.repo.getAdmissionsData(dias);
            if (!data) return;

            const ctx = document.getElementById('chartAdmissoes').getContext('2d');
            if (this.chartAdmissoesInstance) this.chartAdmissoesInstance.destroy();

            // Ordenando chaves (datas) cronologicamente
            const sortedDates = Object.keys(data).sort();
            const values = sortedDates.map(date => data[date]);
            
            // Formatando as datas para exibição (ex: "22/05")
            const labels = sortedDates.map(dateStr => {
                const parts = dateStr.split('-');
                if (parts.length === 3) {
                    return `${parts[2]}/${parts[1]}`;
                }
                return dateStr;
            });

            this.chartAdmissoesInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Novos Pacientes',
                        data: values,
                        borderColor: '#9334e6',
                        backgroundColor: 'rgba(147, 52, 230, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#9334e6',
                        pointRadius: 4,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } },
                        x: { grid: { display: false } }
                    }
                }
            });
        } catch (error) {
            console.error('Erro ao atualizar gráfico de admissões:', error);
        }
    }

    async carregarRelatorios() {
        try {
            const data = await this.repo.getReportsData();
            if (!data) return;

            this.renderizarRelatorioRisco(data.risco);
            this.renderizarRelatorioIdades(data.faixas_etarias);
            this.renderizarRelatorioSintomas(data.sintomas);
            this.renderizarRelatorioComorbidades(data.comorbidades);
        } catch (error) {
            console.error('Erro ao carregar relatórios:', error);
        }
    }

    renderizarRelatorioRisco(risco) {
        const ctx = document.getElementById('chartRisco').getContext('2d');
        if (this.chartRiscoInstance) this.chartRiscoInstance.destroy();

        const mappedLabels = [];
        const mappedValues = [];
        const mappedColors = [];
        
        if (risco['Grupo A'] !== undefined) { mappedLabels.push('Grupo A'); mappedValues.push(risco['Grupo A']); mappedColors.push('#00a2e8'); }
        if (risco['Grupo B'] !== undefined) { mappedLabels.push('Grupo B'); mappedValues.push(risco['Grupo B']); mappedColors.push('#22b14c'); }
        if (risco['Grupo C'] !== undefined) { mappedLabels.push('Grupo C'); mappedValues.push(risco['Grupo C']); mappedColors.push('#ffc20e'); }
        if (risco['Grupo D'] !== undefined) { mappedLabels.push('Grupo D'); mappedValues.push(risco['Grupo D']); mappedColors.push('#ed1c24'); }

        this.chartRiscoInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: mappedLabels,
                datasets: [{
                    data: mappedValues,
                    backgroundColor: mappedColors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, font: { family: 'Segoe UI', size: 12 } }
                    }
                },
                cutout: '60%'
            }
        });
    }

    renderizarRelatorioIdades(idades) {
        const ctx = document.getElementById('chartIdades').getContext('2d');
        if (this.chartIdadesInstance) this.chartIdadesInstance.destroy();

        const labels = Object.keys(idades || {});
        const values = Object.values(idades || {});

        this.chartIdadesInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quantidade',
                    data: values,
                    backgroundColor: '#1a73e8',
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    renderizarRelatorioSintomas(sintomas) {
        const ctx = document.getElementById('chartSintomas').getContext('2d');
        if (this.chartSintomasInstance) this.chartSintomasInstance.destroy();

        const sortedEntries = Object.entries(sintomas || {}).sort((a, b) => b[1] - a[1]);
        const labels = sortedEntries.map(e => e[0]);
        const values = sortedEntries.map(e => e[1]);

        this.chartSintomasInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Incidências',
                    data: values,
                    backgroundColor: 'rgba(79, 70, 229, 0.85)',
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, ticks: { precision: 0 } },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    renderizarRelatorioComorbidades(comorbidades) {
        const tbody = document.getElementById('relatorios-comorbidades-tabela');
        if (!tbody) return;

        tbody.innerHTML = '';

        const sortedComorb = Object.entries(comorbidades || {}).sort((a, b) => b[1] - a[1]);
        
        if (sortedComorb.length === 0 || sortedComorb.every(c => c[1] === 0)) {
            tbody.innerHTML = `<tr><td colspan="2" style="text-align: center; color: #666; padding: 20px;">Nenhuma comorbidade registrada nos pacientes.</td></tr>`;
            return;
        }

        sortedComorb.forEach(([nome, qtd]) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 12px 15px; border-bottom: 1px solid var(--border-color); color: var(--text-main); font-weight: 500;">
                    ${nome}
                </td>
                <td style="padding: 12px 15px; border-bottom: 1px solid var(--border-color); text-align: right; font-weight: 600; color: #333;">
                    ${qtd} ${qtd === 1 ? 'paciente' : 'pacientes'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ==========================================
    // LÓGICA DE PERFIL E CONFIGURAÇÕES DO MÉDICO
    // ==========================================
    atualizarPerfilSidebar(user) {
        if (!user) return;
        const nomeEl = document.getElementById('sidebar-dr-nome');
        const ubsEl = document.getElementById('sidebar-dr-ubs');
        const avatarEl = document.getElementById('sidebar-dr-avatar');
        const navAdminEl = document.getElementById('nav-admin');
        
        if (nomeEl) nomeEl.textContent = "Dr(a). " + user.nome;
        if (ubsEl) ubsEl.textContent = user.ubs || "Nenhuma UBS vinculada";
        if (avatarEl) {
            const iniciais = user.nome.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
            avatarEl.textContent = iniciais;
        }

        if (navAdminEl) {
            if (user.is_admin) {
                navAdminEl.style.display = 'flex';
            } else {
                navAdminEl.style.display = 'none';
            }
        }
    }

    carregarConfiguracoes() {
        const userStr = localStorage.getItem('denguecare_user');
        if (!userStr) return;
        const user = JSON.parse(userStr);
        
        document.getElementById('conf-nome').value = user.nome || '';
        document.getElementById('conf-crm').value = user.carteira || '';
        document.getElementById('conf-ubs').value = user.ubs || '';
        document.getElementById('conf-senha').value = '';
        document.getElementById('conf-msg').style.display = 'none';
    }

    async salvarConfiguracoes() {
        const userStr = localStorage.getItem('denguecare_user');
        if (!userStr) return;
        const user = JSON.parse(userStr);
        
        const novoNome = document.getElementById('conf-nome').value.trim();
        const novaSenha = document.getElementById('conf-senha').value.trim();
        const novaUbs = document.getElementById('conf-ubs').value;
        const msgEl = document.getElementById('conf-msg');
        
        if (novaSenha !== '') {
            const erroSenha = this.validarSenha(novaSenha);
            if (erroSenha) {
                msgEl.textContent = erroSenha;
                msgEl.style.color = "var(--red-alert)";
                msgEl.style.display = "block";
                return;
            }
        }
        
        try {
            const dataToUpdate = {
                carteira: user.carteira,
                nome: novoNome !== '' ? novoNome : undefined,
                senha: novaSenha !== '' ? novaSenha : undefined,
                ubs: novaUbs !== '' ? novaUbs : undefined
            };
            
            const response = await this.repo.updateProfile(dataToUpdate);
            if (response && response.success) {
                msgEl.textContent = "Configurações atualizadas com sucesso!";
                msgEl.style.color = "var(--primary-blue)";
                msgEl.style.display = "block";
                
                // Atualizar cache local
                user.nome = response.data.nome;
                user.ubs = response.data.ubs;
                localStorage.setItem('denguecare_user', JSON.stringify(user));
                this.atualizarPerfilSidebar(user);
            }
        } catch (error) {
            console.error(error);
            msgEl.textContent = "Erro ao atualizar configurações.";
            msgEl.style.color = "var(--red-alert)";
            msgEl.style.display = "block";
        }
    }

    async inativarCadastroMedico() {
        const userStr = localStorage.getItem('denguecare_user');
        if (!userStr) return;
        const user = JSON.parse(userStr);
        
        const confirmacao = confirm("ATENÇÃO: Você está prestes a inativar seu cadastro. Após confirmar, você será deslogado imediatamente e precisará entrar em contato com o administrador do sistema para reativar seu acesso. Deseja continuar?");
        if (!confirmacao) return;
        
        try {
            const response = await this.repo.inactivateProfile(user.carteira);
            if (response && response.success) {
                alert("Seu cadastro foi inativado com sucesso. Você será deslogado.");
                this.fazerLogout();
            }
        } catch (error) {
            console.error(error);
            alert("Ocorreu um erro ao inativar o cadastro.");
        }
    }

    // ==========================================
    // LÓGICA DE PACIENTES (BUSCA, MODAL, CADASTRO, INATIVAÇÃO)
    // ==========================================
    filtrarPacientes(termo) {
        termo = termo.toLowerCase().trim();
        const trs = document.querySelectorAll('#lista-pacientes-tabela tr');
        
        let countVisible = 0;
        trs.forEach(tr => {
            // Assume the name is in the first column strong tag
            const nameEl = tr.querySelector('.patient-name-col strong');
            if(!nameEl) return;
            const nome = nameEl.textContent.toLowerCase();
            // We can't search telephone easily from the TR since we don't display it in the table.
            // But we have this.pacientesExibidos to map it if needed. 
            // For simplicity, let's search via DOM if possible, or using the array.
            
            // Wait, to support searching by phone, we should use this.pacientesExibidos
            const a = tr.querySelector('a');
            if(!a) return;
            const onclickText = a.getAttribute('onclick') || '';
            const match = onclickText.match(/'([^']+)'/);
            const id = match ? match[1] : null;
            
            let matchEncontrado = false;
            if(id) {
                const pacienteData = this.pacientesExibidos.find(p => p.id == id);
                if(pacienteData) {
                    const telMatch = (pacienteData.tel || pacienteData.telefone || '').toLowerCase().includes(termo);
                    const nomeMatch = (pacienteData.nome || '').toLowerCase().includes(termo);
                    matchEncontrado = telMatch || nomeMatch;
                }
            } else {
                matchEncontrado = nome.includes(termo);
            }
            
            if (matchEncontrado) {
                tr.style.display = '';
                countVisible++;
            } else {
                tr.style.display = 'none';
            }
        });
        
        document.getElementById('total-pacientes-list-count').textContent = countVisible;
    }

    abrirModalCadastro() {
        document.getElementById('modal-cadastro-title').textContent = "Cadastrar Novo Paciente";
        document.getElementById('btn-submit-paciente').textContent = "Iniciar Monitoramento";
        document.getElementById('paciente-edit-id').value = "";
        document.getElementById('form-paciente').reset();
        document.getElementById('modal-cadastro').style.display = 'flex';
    }

    fecharModalCadastro() {
        document.getElementById('modal-cadastro').style.display = 'none';
    }

    async editarPacienteAtual() {
        // Obter os detalhes do paciente já carregados na página
        const avatar = document.getElementById('det-avatar');
        if(!avatar) return;
        
        // Puxar da view atual (podemos fazer uma requisição novamente, mas vamos puxar o ID da nav)
        // Para simplificar, vou puxar o nome do h2 e tentar achar no array de pacientes
        const nomeAtual = document.getElementById('det-nome').textContent;
        const p = this.pacientesExibidos.find(x => x.nome === nomeAtual);
        if(!p) {
            alert("Não foi possível carregar os dados completos do paciente.");
            return;
        }
        
        const pacienteDetalhe = await this.repo.getPatientById(p.id);
        if(!pacienteDetalhe) {
            alert("Erro ao buscar dados do paciente.");
            return;
        }

        document.getElementById('modal-cadastro-title').textContent = "Alterar Dados do Paciente";
        document.getElementById('btn-submit-paciente').textContent = "Confirmar Modificações";
        document.getElementById('paciente-edit-id').value = pacienteDetalhe.id;
        
        document.getElementById('cad-nome').value = pacienteDetalhe.nome || '';
        document.getElementById('cad-tel').value = pacienteDetalhe.tel || pacienteDetalhe.telefone || '';
        document.getElementById('cad-data').value = ""; // não temos esse dado exato retornado na rota detalhe, mas...
        document.getElementById('cad-ubs').value = pacienteDetalhe.ubs || '';
        
        document.getElementById('cad-diabetes').checked = (pacienteDetalhe.comorb || []).includes('Diabetes');
        document.getElementById('cad-hipertensa').checked = (pacienteDetalhe.comorb || []).includes('Hipertensão');
        document.getElementById('cad-renal').checked = (pacienteDetalhe.comorb || []).includes('Doença Renal');
        document.getElementById('cad-hematolog').checked = (pacienteDetalhe.comorb || []).includes('Hematológica');
        document.getElementById('cad-hepatopat').checked = (pacienteDetalhe.comorb || []).includes('Hepatopatia');
        document.getElementById('cad-acido').checked = (pacienteDetalhe.comorb || []).includes('Úlcera Péptica');
        document.getElementById('cad-auto').checked = (pacienteDetalhe.comorb || []).includes('Doença Autoimune');
        
        document.getElementById('cad-termo').checked = true;
        
        document.getElementById('modal-cadastro').style.display = 'flex';
    }

    async submeterPaciente() {
        const idEdicao = document.getElementById('paciente-edit-id').value;
        const reqData = {
            nome: document.getElementById('cad-nome').value,
            telefone: document.getElementById('cad-tel').value,
            dt_sin_pri: document.getElementById('cad-data').value,
            ubs_atual: document.getElementById('cad-ubs').value,
            diabetes: document.getElementById('cad-diabetes').checked,
            hipertensa: document.getElementById('cad-hipertensa').checked,
            renal: document.getElementById('cad-renal').checked,
            hematolog: document.getElementById('cad-hematolog').checked,
            hepatopat: document.getElementById('cad-hepatopat').checked,
            acido_pept: document.getElementById('cad-acido').checked,
            auto_imune: document.getElementById('cad-auto').checked
        };
        
        try {
            if(idEdicao && idEdicao !== "") {
                const res = await this.repo.updatePatient(idEdicao, reqData);
                if(res && res.success) {
                    alert("Dados do paciente atualizados com sucesso!");
                    this.fecharModalCadastro();
                    await this.abrirDetalhes(idEdicao); // recarrega tela de detalhes
                    await this.carregarTabelaPacientes(); // recarrega fila de fundo
                    await this.carregarEstatisticas(); // recarrega estatísticas do dashboard
                }
            } else {
                const res = await this.repo.createPatient(reqData);
                if(res && res.success) {
                    alert("Paciente cadastrado e monitoramento iniciado!");
                    this.fecharModalCadastro();
                    await this.carregarTabelaPacientes(); // recarrega fila
                    await this.carregarEstatisticas(); // recarrega estatísticas do dashboard
                }
            }
        } catch(error) {
            console.error(error);
            alert("Erro ao salvar paciente.");
        }
    }

    abrirModalInativarPaciente() {
        document.getElementById('modal-inativar').style.display = 'flex';
    }

    async confirmarInativarPaciente() {
        const motivo = document.getElementById('inativar-motivo').value;
        const nomeAtual = document.getElementById('det-nome').textContent;
        const p = this.pacientesExibidos.find(x => x.nome === nomeAtual);
        if(!p) return;
        
        try {
            const res = await this.repo.inactivatePatient(p.id, motivo);
            if(res && res.success) {
                alert("Paciente inativado. O administrador poderá reativá-lo futuramente.");
                document.getElementById('modal-inativar').style.display = 'none';
                this.navegar('pacientes'); // volta para a fila
                await this.carregarTabelaPacientes(); // recarrega
                await this.carregarEstatisticas(); // recarrega estatísticas do dashboard
            }
        } catch(error) {
            console.error(error);
            alert("Erro ao inativar paciente.");
        }
    }

    // ==========================================
    // MÉTODOS DE ADMINISTRAÇÃO (DASHBOARD ADMIN)
    // ==========================================
    toggleAdminSubTab(tabName) {
        document.querySelectorAll('.admin-tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.admin-sub-view').forEach(view => view.classList.remove('active'));

        if (tabName === 'profissionais') {
            document.getElementById('btn-tab-profissionais').classList.add('active');
            document.getElementById('sub-view-profissionais').classList.add('active');
        } else {
            document.getElementById('btn-tab-pacientes').classList.add('active');
            document.getElementById('sub-view-pacientes').classList.add('active');
        }
    }

    async carregarAdministracao() {
        await Promise.all([
            this.carregarTabelaAdminProfissionais(),
            this.carregarTabelaAdminPacientesInativos()
        ]);
    }

    async carregarTabelaAdminProfissionais() {
        const tbody = document.getElementById('lista-admin-profissionais');
        const countLabel = document.getElementById('admin-prof-count');
        if (!tbody) return;

        try {
            const data = await this.repo.getAllProfessionals();
            tbody.innerHTML = '';
            
            if (countLabel) {
                countLabel.textContent = `${data.length} profissional${data.length !== 1 ? 's' : ''}`;
            }

            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #888; padding: 20px;">Nenhum profissional cadastrado.</td></tr>`;
                return;
            }

            const currentUserStr = localStorage.getItem('denguecare_user');
            const currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;

            data.forEach(p => {
                const statusBadge = p.status === 'ativo' 
                    ? `<span class="badge badge-green">Ativo</span>` 
                    : `<span class="badge badge-gray">Inativo</span>`;

                const roleBadge = p.is_admin 
                    ? `<span class="badge badge-blue">Admin</span>` 
                    : `<span class="badge badge-gray">Profissional</span>`;

                // Botão de reativação
                let reactivateBtn = '';
                if (p.status === 'inativo') {
                    reactivateBtn = `
                        <button class="btn-small btn-success" onclick="window.reactivarUsuarioProfissional('${p.carteira}')" title="Reativar profissional">
                            <span>✅</span> Reativar
                        </button>
                    `;
                }

                // Botão de alternar admin
                const isSelf = currentUser && currentUser.carteira === p.carteira;
                const toggleAdminText = p.is_admin ? 'Remover Admin' : 'Tornar Admin';
                const toggleAdminClass = p.is_admin ? 'btn-danger' : 'btn-blue';
                const toggleAdminIcon = p.is_admin ? '🔑' : '🛡️';
                
                const toggleAdminBtn = isSelf 
                    ? `<span style="font-size: 12px; color: #999; font-style: italic;">(Você)</span>` 
                    : `
                        <button class="btn-small ${toggleAdminClass}" onclick="window.toggleAdminStatusProfissional('${p.carteira}')">
                            <span>${toggleAdminIcon}</span> ${toggleAdminText}
                        </button>
                    `;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${p.nome}</strong></td>
                    <td><code>${p.carteira}</code></td>
                    <td>${p.ubs || '<span style="color: #999; font-style: italic;">Sem UBS vinculada</span>'}</td>
                    <td>${roleBadge}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            ${toggleAdminBtn}
                            ${reactivateBtn}
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error('Erro ao carregar profissionais no painel admin:', error);
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red; padding: 20px;">Erro ao carregar profissionais.</td></tr>`;
        }
    }

    async carregarTabelaAdminPacientesInativos() {
        const tbody = document.getElementById('lista-admin-pacientes');
        const countLabel = document.getElementById('admin-pac-count');
        if (!tbody) return;

        try {
            const data = await this.repo.getInactivePatients();
            tbody.innerHTML = '';

            if (countLabel) {
                countLabel.textContent = `${data.length} paciente${data.length !== 1 ? 's' : ''}`;
            }

            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #888; padding: 20px;">Nenhum paciente inativo.</td></tr>`;
                return;
            }

            data.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>
                        <div class="patient-name-col">
                            <div class="avatar-sm">${p.nm_usuario ? p.nm_usuario.substring(0, 2).toUpperCase() : '--'}</div>
                            <strong>${p.nm_usuario || 'Sem Nome'}</strong>
                        </div>
                    </td>
                    <td><code>${p.nr_carteira || '--'}</code></td>
                    <td>${p.telefone || '<span style="color: #999; font-style: italic;">Sem telefone</span>'}</td>
                    <td><span class="badge badge-orange-outline">${p.motivo_inativacao || 'Não informado'}</span></td>
                    <td>
                        <button class="btn-small btn-success" onclick="window.reactivarUsuarioPaciente('${p.id}')">
                            <span>🔄</span> Reativar
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error('Erro ao carregar pacientes inativos no painel admin:', error);
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: red; padding: 20px;">Erro ao carregar pacientes inativos.</td></tr>`;
        }
    }

    async reactivarUsuarioPaciente(id) {
        if (!confirm('Deseja realmente reativar este paciente e inseri-lo de volta no monitoramento ativo?')) return;

        try {
            const res = await this.repo.reactivatePatient(id);
            if (res && res.success) {
                alert('Paciente reativado com sucesso! Ele já consta na Fila Geral de Monitoramento.');
                await this.carregarTabelaAdminPacientesInativos();
                await this.carregarTabelaPacientes();
                await this.carregarEstatisticas();
            }
        } catch (error) {
            console.error('Erro ao reativar paciente:', error);
            alert('Falha ao reativar o paciente.');
        }
    }

    async reactivarUsuarioProfissional(carteira) {
        if (!confirm('Deseja realmente reativar a conta deste profissional de saúde?')) return;

        try {
            const res = await this.repo.reactivateProfessional(carteira);
            if (res && res.success) {
                alert('Profissional de saúde reativado com sucesso!');
                await this.carregarTabelaAdminProfissionais();
            }
        } catch (error) {
            console.error('Erro ao reativar profissional:', error);
            alert('Falha ao reativar profissional de saúde.');
        }
    }

    async toggleAdminStatusProfissional(carteira) {
        const currentUserStr = localStorage.getItem('denguecare_user');
        const currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;

        if (currentUser && currentUser.carteira === carteira) {
            alert('Ação Negada: Você não pode revogar suas próprias permissões de administrador.');
            return;
        }

        if (!confirm('Tem certeza que deseja alterar o nível de acesso administrativo deste profissional de saúde?')) return;

        try {
            const res = await this.repo.toggleAdminProfessional(carteira);
            if (res && res.success) {
                alert('Nível de acesso do profissional alterado com sucesso!');
                await this.carregarTabelaAdminProfissionais();
            }
        } catch (error) {
            console.error('Erro ao alterar nível admin do profissional:', error);
            alert('Falha ao alterar nível de acesso administrativo.');
        }
    }
}

// Initialize the controller
new DashboardController();
