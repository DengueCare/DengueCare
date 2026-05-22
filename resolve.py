import re

with open("frontend/src/presentation/dashboard/controllers/DashboardController.js", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(
r"<<<<<<< Updated upstream\n        window.descartarAlerta = this.descartarAlerta.bind\(this\);\n        window.toggleAuthMode = this.toggleAuthMode.bind\(this\);\n        window.criarConta = this.criarConta.bind\(this\);\n        window.fazerLogout = this.fazerLogout.bind\(this\);\n\n        this.alertedPatients = new Set\(\);\n        this.alertasDescartados = \{\}; // Armazena \{ \"id_paciente\": \"dt_ultima_triagem_descartada\" \}\n=======\n        window.ordenarPor = this.ordenarPor.bind\(this\);\n>>>>>>> Stashed changes",
"""        window.descartarAlerta = this.descartarAlerta.bind(this);
        window.toggleAuthMode = this.toggleAuthMode.bind(this);
        window.criarConta = this.criarConta.bind(this);
        window.fazerLogout = this.fazerLogout.bind(this);
        window.ordenarPor = this.ordenarPor.bind(this);

        this.alertedPatients = new Set();
        this.alertasDescartados = {}; // Armazena { "id_paciente": "dt_ultima_triagem_descartada" }""",
content)

content = re.sub(
r"<<<<<<< Updated upstream\n        // Verificar se há usuário logado no localStorage\n        const user = localStorage.getItem\('denguecare_user'\);\n        if \(user\) \{\n            const loginScreen = document.getElementById\('login-screen'\);\n            const mainApp = document.getElementById\('main-app'\);\n            if \(loginScreen\) loginScreen.style.display = 'none';\n            if \(mainApp\) mainApp.style.display = 'flex';\n        \}\n\n=======\n        await this.carregarEstatisticas\(\);\n>>>>>>> Stashed changes",
"""        // Verificar se há usuário logado no localStorage
        const user = localStorage.getItem('denguecare_user');
        if (user) {
            const loginScreen = document.getElementById('login-screen');
            const mainApp = document.getElementById('main-app');
            if (loginScreen) loginScreen.style.display = 'none';
            if (mainApp) mainApp.style.display = 'flex';
        }

        await this.carregarEstatisticas();""", content)

content = re.sub(
r"<<<<<<< Updated upstream\n    async carregarTabelaPacientes\(isPolling = false\) \{\n=======\n.*?    async carregarTabelaPacientes\(\) \{\n>>>>>>> Stashed changes",
"""    async carregarEstatisticas() {
        try {
            const repo = new PatientAPIRepository();
            const stats = await repo.getDashboardStats();
            if (!stats) return;

            const cards = document.querySelectorAll('.stat-card h2');
            if (cards.length >= 4) {
                cards[0].textContent = stats.total_pacientes ?? 0;
                cards[1].textContent = stats.alto_risco ?? 0;
                cards[2].textContent = stats.tempo_espera ?? '45 min';
                cards[3].textContent = stats.admissoes_hoje ?? 0;
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas do dashboard:', error);
        }
    }

    atualizarAlertasCriticos(pacientesArray) {
        const alertBox = document.querySelector('.alert-box');
        if (!alertBox) return;

        const criticos = pacientesArray.filter(p => p.grupoAtual === 'Grupo C' || p.grupoAtual === 'Grupo D');

        const alertSub = alertBox.querySelector('.alert-sub');
        if (alertSub) {
            alertSub.textContent = criticos.length === 1 
                ? '1 paciente requer atenção imediata' 
                : `${criticos.length} pacientes requerem atenção imediata`;
        }

        const oldCards = alertBox.querySelectorAll('.alert-card');
        oldCards.forEach(card => card.remove());

        if (criticos.length === 0) {
            const noAlertCard = document.createElement('div');
            noAlertCard.className = 'alert-card';
            noAlertCard.style.borderColor = '#e6f4ea';
            noAlertCard.style.background = '#f4fbf7';
            noAlertCard.style.pointerEvents = 'none';
            noAlertCard.innerHTML = `
                <div style="color: #1e8e3e; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                    <span>✅</span> Sem alertas de urgência ou alto risco no momento.
                </div>
            `;
            alertBox.appendChild(noAlertCard);
            return;
        }

        criticos.forEach(p => {
            const card = document.createElement('div');
            card.className = 'alert-card';
            card.setAttribute('onclick', `window.abrirDetalhes('${p.id}')`);
            card.style.cursor = 'pointer';
            
            let desc = p.grupoAtual === 'Grupo D' 
                ? 'Sinais de choque/gravidade máxima detectados. Encaminhamento imediato.' 
                : 'Sinais de alarme ativos. Requer avaliação prioritária.';
            
            if (p.comorbidades && p.comorbidades.length > 0) {
                desc += ` Comorbidades: ${p.comorbidades.join(', ')}.`;
            }

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4>${p.nome}</h4>
                    <span class="badge ${p.riscoBadge || 'badge-red'}">${p.grupoAtual}</span>
                </div>
                <p style="margin-top: 5px;">${desc}</p>
                <span class="time-ago">Triagem Recente</span>
            `;
            alertBox.appendChild(card);
        });
    }

    async carregarTabelaPacientes(isPolling = false) {""", content, flags=re.DOTALL)

content = re.sub(
r"<<<<<<< Updated upstream\n\n        // Adiciona um loading visual apenas na primeira carga\n        if \(\!isPolling\) \{\n            tbody.innerHTML = `<tr><td colspan=\"4\" style=\"text-align: center; color: #666; padding: 30px;\">Carregando pacientes da API...</td></tr>`;\n        \}\n=======\n        tbody.innerHTML = `<tr><td colspan=\"4\" style=\"text-align: center; color: #666; padding: 30px;\">Carregando pacientes da API...</td></tr>`;\n>>>>>>> Stashed changes",
"""        // Adiciona um loading visual apenas na primeira carga
        if (!isPolling) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #666; padding: 30px;">Carregando pacientes da API...</td></tr>`;
        }""", content)

content = re.sub(
r"<<<<<<< Updated upstream\n    descartarAlerta\(pacienteId, dtUltimaTriagem\) \{\n.*?=======\n.*?    fazerLogin\(\) \{\n.*?>>>>>>> Stashed changes",
"""    descartarAlerta(pacienteId, dtUltimaTriagem) {
        this.alertasDescartados[pacienteId] = dtUltimaTriagem;
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

        const mapaRisco = { 'A': 1, 'B': 2, 'C': 3, 'D': 4 };

        const getGrupoRisco = p => {
            const gr = p.grupoAtual || p.grupo || 'Grupo A';
            const char = gr.replace('Grupo ', '').trim();
            return mapaRisco[char] || 1;
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
        if (mode === 'register') {
            document.getElementById('form-login').style.display = 'none';
            document.getElementById('form-register').style.display = 'block';
            document.getElementById('reg-error').style.display = 'none';""", content, flags=re.DOTALL)

content = re.sub(
r"<<<<<<< Updated upstream\n        document.getElementById\('det-idade'\).textContent = p.idade;\n        document.getElementById\('det-tel'\).textContent = p.tel \? \('📞 ' \+ p.tel\) : '';\n.*?\n=======\n        document.getElementById\('det-idade'\).textContent = p.idade \+ ' anos';\n        document.getElementById\('det-tel'\).textContent = \(p.tel \|\| p.telefone\) \? \('📞 ' \+ \(p.tel \|\| p.telefone\)\) : '';\n>>>>>>> Stashed changes",
"""        document.getElementById('det-idade').textContent = p.idade + ' anos';
        const telefone = p.tel || p.telefone;
        document.getElementById('det-tel').textContent = telefone ? ('📞 ' + telefone) : '';
        
        const btnLigar = document.getElementById('btn-ligar');
        const btnWpp = document.getElementById('btn-whatsapp');
        
        if (telefone && telefone.trim() !== '') {
            const numeroLimpo = telefone.replace(/\D/g, '');
            if (btnLigar) {
                btnLigar.href = `tel:+55${numeroLimpo}`;
                btnLigar.style.pointerEvents = 'auto';
                btnLigar.style.opacity = '1';
                btnLigar.title = "Iniciar chamada telefônica";
            }
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
        }""", content, flags=re.DOTALL)

with open("frontend/src/presentation/dashboard/controllers/DashboardController.js", "w", encoding="utf-8") as f:
    f.write(content)
