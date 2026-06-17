# 🃏 MTG Camera Translator & Card Finder

Fotografe uma carta de **Magic: The Gathering** e receba a tradução instantânea com imagem em alta resolução.

## ✨ Funcionalidades

- 📸 **Captura de imagem** — Tire uma foto com a câmera ou faça upload
- 🤖 **Identificação por IA** — Modelo de visão identifica a carta automaticamente
- 🌐 **Tradução automática** — Nome e texto do oráculo traduzidos para português
- 🖼️ **Imagem HD** — Imagem de alta resolução direto do Scryfall
- 🔒 **Segurança por Design** — Validação rigorosa, rate limiting, credenciais protegidas

## 🏗️ Arquitetura

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Frontend   │────▶│    Backend       │────▶│  OpenRouter   │
│   React/Vite │◀────│    Django DRF    │◀────│  (IA Visão)   │
└─────────────┘     │                  │     └──────────────┘
                    │                  │
                    │                  │────▶┌──────────────┐
                    │                  │◀────│   Scryfall    │
                    └──────────────────┘     │   (Dados)     │
                                             └──────────────┘
```

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Conta no [OpenRouter](https://openrouter.ai/) com créditos

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
copy .env.example .env
# Edite o .env e coloque sua OPENROUTER_API_KEY

# Rodar migrations
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev
```

Acesse `http://localhost:5173` no navegador.

### Executar Testes

```bash
cd backend
python manage.py test cards --verbosity=2
```

## 🔒 Segurança

| Medida | Implementação |
|--------|--------------|
| Validação de Uploads | Magic bytes, extensão, tamanho (max 5MB), path traversal |
| Credenciais | Todas em `.env`, nunca no código/frontend |
| Rate Limiting | 10 req/min + 3 req/sec por IP |
| Tratamento de Erros | Mensagens genéricas ao cliente, detalhes nos logs |

## 📁 Estrutura

```
├── backend/
│   ├── mtg_translator/        # Projeto Django
│   │   ├── settings.py        # Configurações seguras
│   │   └── urls.py            # Rotas raiz
│   ├── cards/                 # App principal
│   │   ├── models.py          # CardScan (auditoria)
│   │   ├── views.py           # CardIdentifyView
│   │   ├── validators.py      # Validação de uploads
│   │   ├── throttles.py       # Rate limiting
│   │   ├── services/          # Integrações externas
│   │   │   ├── vision_service.py    # OpenRouter
│   │   │   └── scryfall_service.py  # Scryfall
│   │   └── tests/             # Testes automatizados
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Componente principal
│   │   ├── components/        # Componentes React
│   │   └── services/api.js    # Comunicação com backend
│   └── package.json
└── README.md
```

## 📄 Licença

Projeto educacional. Dados de cartas fornecidos pela API do [Scryfall](https://scryfall.com/docs/api).
