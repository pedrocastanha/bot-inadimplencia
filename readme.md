# Estrutura de arquivos ideal do projeto:

webhook_agent_system/
├── main.py                     # Ponto de entrada da aplicação
├── config.py                   # Configurações da aplicação
├── requirements.txt            # Dependências
├── models/
│   ├── __init__.py
│   ├── webhook_models.py       # Models do webhook (Pydantic)
│   └── message_models.py       # Models de mensagens e dados
├── core/
│   ├── __init__.py
│   ├── memory.py              # Sistema de memória das conversas
│   ├── agent.py               # Classe Agent principal
│   └── agent_manager.py       # Gerenciador de agentes
├── api/
│   ├── __init__.py
│   ├── webhook.py             # Rotas do webhook
│   ├── agents.py              # Rotas de gerenciamento de agentes
│   └── health.py              # Health check e status
├── services/
│   ├── __init__.py
│   ├── message_processor.py   # Processamento de mensagens
│   └── zapi_client.py         # Cliente da Z-API (para envio)
└── utils/
    ├── __init__.py
    ├── logger.py              # Configuração de logging
    └── helpers.py             # Funções auxiliares