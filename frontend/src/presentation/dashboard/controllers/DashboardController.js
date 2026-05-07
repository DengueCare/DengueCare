import { PatientAPIRepository } from '../../../infrastructure/repositories/PatientAPIRepository.js';
import { GetPatientByIdUseCase, GetPatientsUseCase } from '../../../application/usecases/PatientUseCases.js';

export class DashboardController {
    constructor() {
        const repo = new PatientAPIRepository();
        this.getPatientByIdUseCase = new GetPatientByIdUseCase(repo);
        this.getPatientsUseCase = new GetPatientsUseCase(repo);
        
        // Expose functions to the window object so inline HTML onclicks work without rewriting HTML
        window.fazerLogin = this.fazerLogin.bind(this);
        window.navegar = this.navegar.bind(this);
        window.abrirDetalhes = this.abrirDetalhes.bind(this);

        this.init();
    }

    async init() {
        await this.carregarTabelaPacientes();
    }

    async carregarTabelaPacientes() {
        const tbody = document.getElementById('lista-pacientes-tabela');
        if (!tbody) return; 

        tbody.innerHTML = ''; 

        // Adiciona um loading visual enquanto busca
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #666; padding: 30px;">Carregando pacientes da API...</td></tr>`;

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
        });
    }

    fazerLogin() {
        const nome = document.getElementById('login-nome').value.trim();
        const id = document.getElementById('login-id').value.trim();
        if(nome !== '' && id !== '') {
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('main-app').style.display = 'flex';
        } else {
            document.getElementById('login-error').style.display = 'block';
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
