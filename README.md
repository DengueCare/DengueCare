[README.md](https://github.com/user-attachments/files/27477016/README.md)
# 🦟 DengueCare AI

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow?style=for-the-badge)
![Fatec](https://img.shields.io/badge/Fatec-Rio_Claro-003087?style=for-the-badge)

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    🦟  D E N G U E C A R E   A I                        ║
║                                                          ║
║    Telemonitoramento Preditivo com Chatbot Próprio       ║
║    Prevenindo agravamentos. Salvando vidas.              ║
║                                                          ║
║    [ Substituir por banner do projeto ]                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

> **Sistema de telemonitoramento preditivo com chatbot próprio** que acompanha
> diariamente pacientes com suspeita ou diagnóstico de dengue, utilizando Machine
> Learning treinado com dados reais do SINAN para identificar silenciosamente sinais
> de agravamento e emitir alertas em tempo real para equipes médicas da UBS —
> prevenindo complicações e desafogando o sistema de triagem.

---

## 📑 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Arquitetura e Fluxo do Sistema](#arquitetura-e-fluxo-do-sistema)
- [Modelagem de Dados](#modelagem-de-dados)
- [Como Executar Localmente](#como-executar-localmente)
- [Roadmap / Sprints](#roadmap--sprints)
- [Equipe](#equipe)
- [Conformidade LGPD](#conformidade-lgpd)

---

## 📌 Sobre o Projeto

### Contexto

A dengue é uma doença endêmica no Brasil e representa um desafio crítico para o
sistema público de saúde, especialmente durante períodos epidêmicos. As Unidades
Básicas de Saúde (UBS) enfrentam sobrecarga nas triagens presenciais, enquanto
pacientes em monitoramento domiciliar frequentemente não conseguem identificar,
por conta própria, os sinais de alarme que indicam agravamento da doença.

### Problema

- **Subnotificação de sinais de alarme:** pacientes em casa não relatam sintomas
  críticos até que o quadro já esteja grave.
- **Sobrecarga de triagem:** UBSs e UPAs são procuradas tanto por casos leves
  quanto por emergências, dificultando a priorização.
- **Acompanhamento descontínuo:** após a consulta inicial, não há canal estruturado
  de comunicação entre paciente e equipe médica.

### Solução

O **DengueCare AI** automatiza o acompanhamento pós-consulta por meio de um
chatbot próprio desenvolvido em HTML, CSS e JavaScript. Diariamente, o paciente
responde a perguntas mapeadas aos sinais de alarme do SINAN. Um modelo de
Machine Learning processa as respostas e classifica o paciente nos **Grupos
Clínicos A, B, C ou D** do protocolo do SUS, gerando um score de risco exibido
em tempo real no Dashboard da UBS.

> **Proposta de valor:** Evitar o agravamento da dengue por meio do monitoramento
> remoto e contínuo, guiando pacientes de baixo risco ao cuidado domiciliar e
> alertando pacientes de alto risco no momento exato de buscar ajuda.

---

## ✨ Funcionalidades

| # | Código | Funcionalidade |
|---|--------|----------------|
| 1 | `RF-01` | 🩺 **Cadastro médico:** Interface web para registro rápido do paciente com baseline clínica após diagnóstico na UBS |
| 2 | `RF-02` | 💬 **Chatbot próprio:** Respostas numéricas fechadas, diárias, mapeadas ao Dicionário de Dados do SINAN, acessado via aplicação web (HTML, CSS e JavaScript) |
| 3 | `RF-03` | 🔧 **Pipeline ETL:** Limpeza, transformação e treinamento do modelo com dados reais das fichas SINAN |
| 4 | `RF-04` | 🤖 **API de Previsão:** Endpoint Python que recebe o array diário de sintomas e retorna o score de risco |
| 5 | `RF-05` | 📊 **Dashboard de Triagem:** Fila ordenada por gravidade com semáforo visual (🟢 Verde / 🟡 Amarelo / 🔴 Vermelho) |

### Comportamento por grupo de risco

- 🟢 **Grupo A (Baixo Risco):** Chatbot envia orientações de hidratação e repouso.
- 🟡 **Grupo B (Atenção):** Chatbot alerta sobre sinais a observar; Dashboard destaca o paciente.
- 🔴 **Grupos C/D (Alto Risco):** Chatbot orienta retorno imediato à UPA; Dashboard emite alerta vermelho e eleva o paciente ao topo da fila.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Finalidade |
|--------|-----------|------------|
| **Backend / ML** | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) Scikit-Learn | Modelos: `DecisionTreeClassifier`, `RandomForest` ou `SVM` |
| **ETL de Dados** | ![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white) Pandas | Limpeza e transformação das fichas SINAN/DataSUS |
| **Dados** | DataSUS / SINAN | Fichas de dengue do município de Rio Claro |
| **Frontend** | ![HTML](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white) ![CSS](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black) | Chatbot de monitoramento e Dashboard Web (fila de risco) |
| **Infraestrutura** | ☁️ Cloud | Hospedagem em servidores em nuvem |
| **Gestão** | ![Trello](https://img.shields.io/badge/Trello-0052CC?logo=trello&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white) | Scrum/Agile — Sprints, Trello e controle de versão |

---

## 🏗️ Arquitetura e Fluxo do Sistema

```mermaid
flowchart TD
    A[👨‍⚕️ Médico UBS] -->|Cadastra paciente| B[Interface Web - RF-01]
    B -->|Salva baseline clínica| C[(Banco de Dados)]

    C -->|Agenda contato diário| D[🤖 Chatbot Web - RF-02]
    D -->|Perguntas fechadas SINAN| E[🖥️ Paciente]
    E -->|Respostas numéricas| D

    D -->|Array de sintomas| F[API de Previsão Python - RF-04]
    F -->|ETL + Modelo ML - RF-03| G{Classificação de Risco}

    G -->|Grupo A - Baixo| H[✅ Orientações de repouso e hidratação via chatbot]
    G -->|Grupos C/D - Alto| I[🚨 Alerta: retornar à UPA via chatbot]
    G -->|Todos os grupos| J[📊 Dashboard - RF-05]

    I --> J
    J -->|🔴 Vermelho - topo da fila| K[👩‍⚕️ Equipe Médica UBS]
    J -->|🟡 Amarelo / 🟢 Verde| K
```


---

## 🗄️ Modelagem de Dados

> ⚠️ **Atenção:** Esta seção será atualizada em breve.

### Tabela `paciente`
⚠️ATUAL (Mudara no futuro)⚠️
| Coluna |
| `id_paciente` |
|  `nr_usuario` |
| `nr_carteira` |


### Tabela `atendimento_paciente`
⚠️ATUAL (Mudara no futuro)⚠️
| Coluna |
| `id_atendimento` |
| `id_chave estrangeira` |
| `nr_atendimento` |


---

## 🚀 Como Executar Localmente

### Pré-requisitos

- Python `3.11+`
- `pip` ou `pipenv`
- PostgreSQL `15+` (ou SQLite para desenvolvimento local)
- Git
- Navegador moderno (para o chatbot e dashboard em HTML/CSS/JS)

### 1. Clone o repositório

```bash
git clone https://github.com/<seu-usuario>/DengueCare.git
cd DengueCare
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/denguecare

# Configurações do Modelo ML
MODEL_PATH=./models/dengue_classifier.pkl
RECALL_THRESHOLD=0.95

# Segurança
SECRET_KEY=sua_chave_secreta_aqui
```

### 5. Execute o pipeline ETL e treine o modelo

```bash
# 1. Processar os dados brutos do SINAN
python etl/run_etl.py --input data/raw/sinan_rio_claro.csv --output data/processed/

# 2. Treinar e avaliar o modelo
python ml/train_model.py --data data/processed/sinan_clean.csv --output models/
```

### 6. Inicie o servidor backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Acesse a aplicação

| Serviço | URL |
|---------|-----|
| API (Swagger) | `http://localhost:8000/docs` |
| Dashboard Web | `http://localhost:8000/dashboard` |
| Chatbot | `http://localhost:8000/chatbot` |

---

## 🗓️ Roadmap / Sprints

```
Sprint 1 ──────────────────────────────────────────────── [Em andamento]
│
├── 🔬 ETL & Dados
│   ├── [ ] Download e inspeção das fichas SINAN de Rio Claro
│   ├── [ ] Limpeza e anonimização (LGPD)
│   ├── [ ] Engenharia de features (sinais de alarme)
│   └── [ ] Treinamento inicial do modelo (baseline)
│
├── 🗄️ Banco de Dados
│   ├── [ ] Definição do schema (paciente, atendimento, monitoramento)
│   └── [ ] Migrations e seed de dados de teste
│
Sprint 2 ──────────────────────────────────────────────── [Planejado]
│
├── ⚙️ Backend & Integração
│   ├── [ ] API de previsão (endpoint /predict)
│   ├── [ ] Lógica do fluxo de perguntas do chatbot
│   └── [ ] Serviço de alertas e fila de risco
│
Sprint 3 ──────────────────────────────────────────────── [Planejado]
│
└── 🖥️ Frontend & Refinamento
    ├── [ ] Dashboard Web (fila por gravidade)
    ├── [ ] Testes ponta a ponta (cadastro → Chatbot → Dashboard)
    ├── [ ] Auditoria de viés do modelo
    └── [ ] Documentação final e deploy em nuvem
```

---

## 👥 Equipe

**Fatec Rio Claro — Projeto Integrador 3 | 3º Semestre / 2026 — Grupo 1**

| Papel | Nome |
|-------|------|
| 🎯 **Product Owner** | Heitor Vitti Partezani |
| 🔄 **Scrum Master** | Guilherme Peres Romanzotti |
| 👨‍💻 **Dev Team** | César Augusto Oliveira Bovo |
| 👩‍💻 **Dev Team** | Elisa Almeida Alcântara |
| 👨‍💻 **Dev Team** | Luis Otavio Routh da Silva |
| 👨‍💻 **Dev Team** | Marvin Cristhian Gomes Pinto |
| 👨‍💻 **Dev Team** | Paulo Guilherme Moreira |
| 👨‍💻 **Dev Team** | Raphael Culim Neves |

---

## 🛡️ Conformidade LGPD

> ⚠️ **Aviso Legal e de Privacidade**

Este sistema foi desenvolvido em conformidade com a **Lei Geral de Proteção de
Dados Pessoais (LGPD — Lei nº 13.709/2018)**. As seguintes medidas estão
implementadas:

- **Anonimização obrigatória:** todos os dados do SINAN utilizados no treinamento
  do modelo passam por processo de anonimização irreversível antes de qualquer
  processamento computacional.
- **Minimização de dados:** apenas as informações estritamente necessárias ao
  monitoramento clínico são coletadas.
- **Finalidade específica:** os dados são utilizados exclusivamente para
  monitoramento de saúde dos pacientes cadastrados e melhoria dos modelos
  preditivos.
- **Disclaimer no chatbot:** toda interação inclui a seguinte mensagem automática:

  > *"Este serviço é um suporte ao acompanhamento médico e **não substitui
  > diagnóstico, prescrição ou orientação médica profissional**. Em caso de
  > emergência, ligue 192 (SAMU) ou dirija-se à UPA mais próxima."*

- **Tratamento de texto livre:** mensagens fora do fluxo estruturado recebem
  resposta orientativa e, em casos de emergência declarada, instruções imediatas
  para acionar o SAMU ou a UPA.
- **Direito do titular:** pacientes podem solicitar a exclusão de seus dados
  a qualquer momento pelo contato da UBS responsável.

---

<div align="center">

Feito com ❤️ por estudantes da **Fatec Rio Claro** — Projeto Integrador 3 · 2026

</div>
