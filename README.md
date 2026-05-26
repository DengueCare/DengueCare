[README.md](https://github.com/user-attachments/files/27477016/README.md)
# 🦟 DengueCare AI

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![Status](https://img.shields.io/badge/Status-MVP_Funcional-brightgreen?style=for-the-badge)
![Fatec](https://img.shields.io/badge/Fatec-Rio_Claro-003087?style=for-the-badge)

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    🦟  D E N G U E C A R E   A I                        ║
║                                                          ║
║    Telemonitoramento Preditivo via Bot Telegram          ║
║    Prevenindo agravamentos. Salvando vidas.              ║
║                                                          ║
║    [ Substituir por banner do projeto ]                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

> **Sistema de telemonitoramento preditivo via Bot Telegram** que acompanha
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

> 🤝 **Empresa Parceira:** Vigilância Epidemiológica de Rio Claro — representada por
> João Guilherme Benetti Ramos (Doutorando, USP).

### Problema

- **Subnotificação de sinais de alarme:** pacientes em casa não relatam sintomas
  críticos até que o quadro já esteja grave.
- **Sobrecarga de triagem:** UBSs e UPAs são procuradas tanto por casos leves
  quanto por emergências, dificultando a priorização.
- **Acompanhamento descontínuo:** após a consulta inicial, não há canal estruturado
  de comunicação entre paciente e equipe médica.

### Solução

O **DengueCare AI** automatiza o acompanhamento pós-consulta por meio de um
**Bot Telegram** (`python-telegram-bot`), em produção no Render. O paciente
interage via Telegram respondendo a perguntas mapeadas aos sinais de alarme do
SINAN. Um modelo de Machine Learning (`modelo_dengue_v1.pkl`) processa as
respostas e classifica o paciente nos **Grupos Clínicos A, B, C ou D** do
protocolo do SUS, gerando um score de risco exibido em tempo real no Dashboard
da UBS.

> **Proposta de valor:** Evitar o agravamento da dengue por meio do monitoramento
> remoto e contínuo, guiando pacientes de baixo risco ao cuidado domiciliar e
> alertando pacientes de alto risco no momento exato de buscar ajuda.

---

## ✨ Funcionalidades

| # | Código | Funcionalidade |
|---|--------|----------------|
| 1 | `RF-01` | 🩺 **Cadastro médico:** Interface web para registro rápido do paciente com baseline clínica após diagnóstico na UBS |
| 2 | `RF-02` | 💬 **Bot Telegram:** Fluxo de identificação, cadastro e acompanhamento de sintomas via Telegram (`python-telegram-bot`), com respostas numéricas fechadas mapeadas ao Dicionário de Dados do SINAN |
| 3 | `RF-03` | 🔧 **Pipeline ETL:** Limpeza, transformação e treinamento do modelo com dados reais das fichas SINAN |
| 4 | `RF-04` | 🤖 **API de Previsão:** Endpoint Python que recebe o array diário de sintomas e retorna o score de risco |
| 5 | `RF-05` | 📊 **Dashboard de Triagem:** Fila ordenada por gravidade com semáforo visual (🟢 Verde / 🟡 Amarelo / 🔴 Vermelho) |

### Comportamento por grupo de risco

- 🟢 **Grupo A (Baixo Risco):** Bot Telegram envia orientações de hidratação e repouso.
- 🟡 **Grupo B (Atenção):** Bot Telegram alerta sobre sinais a observar; Dashboard destaca o paciente.
- 🔴 **Grupos C/D (Alto Risco):** Bot Telegram orienta retorno imediato à UPA; Dashboard emite alerta vermelho e eleva o paciente ao topo da fila.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Finalidade |
|--------|-----------|------------|
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) Python 3.11+ | Rotas `POST /api/v1/chat/send` · `GET /patients/` — deploy no Render |
| **ML / IA** | ![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?logo=scikit-learn&logoColor=white) | `modelo_dengue_v1.pkl` — classifica Grupos A/B/C/D (protocolo SUS) |
| **ETL de Dados** | ![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white) Pandas | Limpeza e transformação das fichas SINAN 2026 / DataSUS |
| **Dados** | DataSUS / SINAN 2026 | Base pública usada no treinamento (dados de Rio Claro aguardando parceiro) |
| **Bot / Mensageria** | ![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?logo=telegram&logoColor=white) python-telegram-bot | Identificação, cadastro e fluxo de sintomas via Webhook — deploy no Render |
| **Banco de Dados** | ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white) PostgreSQL + SQLAlchemy | Tabelas `paciente` + colunas de atendimento — acesso assíncrono |
| **Frontend** | ![HTML](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white) ![CSS](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black) | Dashboard Web com fila de risco em tempo real |
| **Infraestrutura** | ![Render](https://img.shields.io/badge/Render-46E3B7?logo=render&logoColor=white) | Hospedagem do backend FastAPI + webhook Telegram em produção |
| **Gestão** | ![Trello](https://img.shields.io/badge/Trello-0052CC?logo=trello&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white) | Scrum/Agile — Sprints, Trello e controle de versão |

---

## 🏗️ Arquitetura e Fluxo do Sistema

```mermaid
flowchart TD
    A[👨‍⚕️ Médico UBS] -->|Cadastra paciente| B[Interface Web - RF-01]
    B -->|Salva baseline clínica| C[(Supabase — PostgreSQL)]

    C -->|Agenda contato diário| D[🤖 Bot Telegram - RF-02]
    D -->|Perguntas fechadas SINAN| E[📱 Paciente]
    E -->|Respostas numéricas| D

    D -->|POST /api/v1/chat/send| F[⚙️ FastAPI Backend - RF-04]
    F -->|ml_service.py — modelo_dengue_v1.pkl - RF-03| G{Classificação de Risco}

    G -->|Grupo A/B - Baixo| H[✅ Orientações de repouso e hidratação via Telegram]
    G -->|Grupos C/D - Alto| I[🚨 Alerta: retornar à UPA via Telegram]
    G -->|Todos os grupos| J[📊 Dashboard Web - RF-05]

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
git clone https://github.com/DengueCare/DengueCare.git
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
# Banco de Dados (Supabase)
DATABASE_URL=postgresql+asyncpg://usuario:senha@db.<projeto>.supabase.co:5432/postgres

# Bot Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Configurações do Modelo ML
MODEL_PATH=./models/modelo_dengue_v1.pkl
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
| Webhook Telegram | `http://localhost:8000/webhook/telegram` |


---

## 👥 Equipe

**Fatec Rio Claro — Projeto Integrador 3 | 3º Semestre / 2026 — Grupo 1**

| Papel | Nome | Destaque |
|-------|------|----------|
| 🎯 **Product Owner** | Heitor Vitti Partezani | Banco de Dados (Supabase) |
| 🔄 **Scrum Master** | Guilherme Peres Romanzotti | Gestão, comunicação com parceiro |
| 👨‍💻 **Dev Team** | César Augusto Oliveira Bovo | Documentação técnica |
| 👩‍💻 **Dev Team** | Elisa Almeida Alcântara | **Accountable — IA / ETL / ML** |
| 👨‍💻 **Dev Team** | Luis Otavio Routh da Silva | Frontend & Fluxo de cadastro |
| 👨‍💻 **Dev Team** | Marvin Cristhian Gomes Pinto | **Accountable — Backend & Integração IA** |
| 👨‍💻 **Dev Team** | Paulo Guilherme Moreira | Design / Verificação de identidade |
| 👨‍💻 **Dev Team** | Raphael Culim Neves | Fluxo conversacional do chatbot |

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
- **Disclaimer no bot:** toda interação via Bot Telegram inclui a seguinte mensagem automática:

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
