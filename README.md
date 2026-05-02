[README.md](https://github.com/user-attachments/files/27308809/README.md)
# 🦟 DengueCare AI

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![WhatsApp](https://img.shields.io/badge/WhatsApp_API-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![License](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow?style=for-the-badge)
![Fatec](https://img.shields.io/badge/Fatec-Rio_Claro-003087?style=for-the-badge)

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    🦟  D E N G U E C A R E   A I                        ║
║                                                          ║
║    Telemonitoramento Preditivo via WhatsApp              ║
║    Prevenindo agravamentos. Salvando vidas.              ║
║                                                          ║
║    [ Substituir por banner do projeto ]                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

> **Sistema de telemonitoramento preditivo integrado ao WhatsApp** que acompanha
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
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Roadmap / Sprints](#roadmap--sprints)
- [Equipe](#equipe)
- [Licença](#licença)
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
chatbot estruturado no WhatsApp — canal já amplamente utilizado pela população.
Diariamente, o paciente responde a perguntas mapeadas aos sinais de alarme do
SINAN. Um modelo de Machine Learning processa as respostas e classifica o
paciente nos **Grupos Clínicos A, B, C ou D** do protocolo do SUS, gerando um
score de risco exibido em tempo real no Dashboard da UBS.

> **Proposta de valor:** Evitar o agravamento da dengue por meio do monitoramento
> remoto e contínuo, guiando pacientes de baixo risco ao cuidado domiciliar e
> alertando pacientes de alto risco no momento exato de buscar ajuda.

---

## ✨ Funcionalidades

| # | Código | Funcionalidade |
|---|--------|----------------|
| 1 | `RF-01` | 🩺 **Cadastro médico:** Interface web para registro rápido do paciente com baseline clínica após diagnóstico na UBS |
| 2 | `RF-02` | 💬 **Chatbot WhatsApp:** Respostas numéricas fechadas, diárias, mapeadas ao Dicionário de Dados do SINAN |
| 3 | `RF-03` | 🔧 **Pipeline ETL:** Limpeza, transformação e treinamento do modelo com dados reais das fichas SINAN |
| 4 | `RF-04` | 🤖 **API de Previsão:** Endpoint Python que recebe o array diário de sintomas e retorna o score de risco |
| 5 | `RF-05` | 📊 **Dashboard de Triagem:** Fila ordenada por gravidade com semáforo visual (🟢 Verde / 🟡 Amarelo / 🔴 Vermelho) |

### Comportamento por grupo de risco

- 🟢 **Grupo A (Baixo Risco):** Bot envia orientações de hidratação e repouso.
- 🟡 **Grupo B (Atenção):** Bot alerta sobre sinais a observar; Dashboard destaca o paciente.
- 🔴 **Grupos C/D (Alto Risco):** Bot orienta retorno imediato à UPA; Dashboard emite alerta vermelho e eleva o paciente ao topo da fila.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Finalidade |
|--------|-----------|------------|
| **Backend / ML** | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) Scikit-Learn | Modelos: `DecisionTreeClassifier`, `RandomForest` ou `SVM` |
| **ETL de Dados** | ![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white) Pandas | Limpeza e transformação das fichas SINAN/DataSUS |
| **Dados** | DataSUS / SINAN | Fichas de dengue do município de Rio Claro |
| **Mensageria** | ![WhatsApp](https://img.shields.io/badge/WhatsApp_API-25D366?logo=whatsapp&logoColor=white) Twilio / Meta API | Envio e recebimento de mensagens via Webhooks |
| **Frontend** | Dashboard Web | Fila de pacientes com score de risco em tempo real |
| **Infraestrutura** | ☁️ Cloud | Hospedagem em servidores em nuvem |
| **Gestão** | ![Trello](https://img.shields.io/badge/Trello-0052CC?logo=trello&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white) | Scrum/Agile — Sprints, Trello e controle de versão |

---

## 🏗️ Arquitetura e Fluxo do Sistema

```mermaid
flowchart TD
    A[👨‍⚕️ Médico UBS] -->|Cadastra paciente| B[Interface Web - RF-01]
    B -->|Salva baseline clínica| C[(Banco de Dados)]

    C -->|Agenda contato diário| D[🤖 Bot WhatsApp - RF-02]
    D -->|Perguntas fechadas SINAN| E[📱 Paciente]
    E -->|Respostas numéricas| D

    D -->|Array de sintomas| F[API de Previsão Python - RF-04]
    F -->|ETL + Modelo ML - RF-03| G{Classificação de Risco}

    G -->|Grupo A - Baixo| H[✅ Orientações de repouso e hidratação via bot]
    G -->|Grupos C/D - Alto| I[🚨 Alerta: retornar à UPA via bot]
    G -->|Todos os grupos| J[📊 Dashboard - RF-05]

    I --> J
    J -->|🔴 Vermelho - topo da fila| K[👩‍⚕️ Equipe Médica UBS]
    J -->|🟡 Amarelo / 🟢 Verde| K
```

### Degradação Graciosa

```
Se WhatsApp API falhar → Dashboard lista pacientes como "Contato Pendente"
                       → Equipe realiza contato manual
```

---

## 🗄️ Modelagem de Dados

### Tabela `paciente`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_paciente` | `UUID` | Identificador único |
| `nome_anonimizado` | `VARCHAR` | Nome hasheado (LGPD) |
| `telefone` | `VARCHAR` | Número WhatsApp |
| `data_nascimento` | `DATE` | Data de nascimento |
| `ubs_responsavel` | `VARCHAR` | UBS de referência |
| `data_cadastro` | `TIMESTAMP` | Data/hora do cadastro |

### Tabela `atendimento_inicial`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_atendimento` | `UUID` | Identificador único |
| `id_paciente` | `UUID` | FK → `paciente` |
| `data_inicio_sintomas` | `DATE` | Dia 1 dos sintomas |
| `temperatura` | `FLOAT` | Temperatura na triagem (°C) |
| `pressao_arterial` | `VARCHAR` | Pressão arterial |
| `grupo_clinico_inicial` | `CHAR(1)` | Grupo A/B/C/D (SUS) |
| `medico_responsavel` | `VARCHAR` | CRM do médico |
| `observacoes` | `TEXT` | Notas clínicas livres |

### Tabela `monitoramento_diario`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_monitoramento` | `UUID` | Identificador único |
| `id_paciente` | `UUID` | FK → `paciente` |
| `data_resposta` | `TIMESTAMP` | Data/hora da coleta |
| `dia_doenca` | `INT` | Dia da doença (D1, D2…) |
| `dor_abdominal` | `BOOLEAN` | Sinal de alarme SINAN |
| `vomitos_persistentes` | `BOOLEAN` | Sinal de alarme SINAN |
| `sangramento` | `BOOLEAN` | Sinal de alarme SINAN |
| `letargia` | `BOOLEAN` | Sinal de alarme SINAN |
| `temperatura_dia` | `FLOAT` | Temperatura relatada |
| `score_risco` | `FLOAT` | Score gerado pelo modelo ML (0–1) |
| `grupo_clinico_previsto` | `CHAR(1)` | Grupo A/B/C/D predito |

---

## 🚀 Como Executar Localmente

### Pré-requisitos

- Python `3.11+`
- `pip` ou `pipenv`
- Conta Twilio ou Meta Business API (para WhatsApp)
- PostgreSQL `15+` (ou SQLite para desenvolvimento local)
- Git

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

# WhatsApp API (escolha um)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Meta / WhatsApp Business API (alternativo)
META_WHATSAPP_TOKEN=EAAxxxxxxx
META_PHONE_NUMBER_ID=1234567890
META_VERIFY_TOKEN=seu_token_secreto

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
| Webhook WhatsApp | `http://localhost:8000/webhook/whatsapp` |

> 💡 **Dica:** Para testar o webhook localmente, utilize o [ngrok](https://ngrok.com/):
> ```bash
> ngrok http 8000
> ```
> Configure a URL gerada como endpoint no painel Twilio ou Meta.

---

## 📁 Estrutura de Pastas

```
DengueCare/
│
├── 📂 app/                         # Aplicação principal (FastAPI/Flask)
│   ├── main.py                     # Ponto de entrada da API
│   ├── routes/                     # Endpoints REST
│   │   ├── patients.py             # CRUD de pacientes
│   │   ├── monitoring.py           # Monitoramento diário
│   │   └── webhook.py              # Webhook WhatsApp
│   ├── services/                   # Regras de negócio
│   │   ├── risk_score.py           # Chamada ao modelo ML
│   │   ├── whatsapp_bot.py         # Lógica do chatbot
│   │   └── alert_service.py        # Emissão de alertas
│   └── models/                     # Schemas / ORM
│
├── 📂 ml/                          # Machine Learning
│   ├── train_model.py              # Treinamento e avaliação
│   ├── predict.py                  # Inferência
│   └── evaluate.py                 # Métricas (recall, precision, F1)
│
├── 📂 etl/                         # Pipeline de dados
│   ├── run_etl.py                  # Orquestrador
│   ├── clean_sinan.py              # Limpeza das fichas SINAN
│   └── feature_engineering.py     # Engenharia de features
│
├── 📂 data/
│   ├── raw/                        # Dados brutos (não versionar dados sensíveis)
│   └── processed/                  # Dados anonimizados processados
│
├── 📂 models/                      # Artefatos do modelo treinado (.pkl)
│
├── 📂 dashboard/                   # Frontend do Dashboard Web
│   ├── index.html
│   ├── css/
│   └── js/
│
├── 📂 tests/                       # Testes unitários e de integração
│   ├── test_ml.py
│   ├── test_api.py
│   └── test_bot.py
│
├── 📂 docs/                        # Documentação adicional
│   ├── api_reference.md
│   └── sinan_dictionary.md
│
├── .env.example                    # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── docker-compose.yml              # (opcional) Orquestração local
└── README.md
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

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** — veja o arquivo
[LICENSE](LICENSE) para mais detalhes.

```
MIT License — Copyright (c) 2026 DengueCare AI Team — Fatec Rio Claro
```

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
- **Disclaimer no bot:** toda interação via WhatsApp inclui a seguinte
  mensagem automática:

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
