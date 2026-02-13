# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2026-02-13

### Corrigido
- 🔗 Conversão de todos os links relativos para URLs absolutas do GitHub no README.md
- ✅ Links agora funcionam corretamente tanto no GitHub quanto no PyPI
- 📚 Links para documentação (WIKI.md, CURSO_BASICO.md, FAQ.md, etc.)
- 📁 Links para arquivos (ESTRUTURA.md, INDICE.md)
- 🔧 Links para scripts (validate_env.py, quick_setup.py, etc.)

### Melhorado
- 🌐 Experiência do usuário ao acessar https://pypi.org/project/mangaba/
- 📖 Acessibilidade da documentação através do PyPI

## [1.0.2] - 2025-11-16

### Adicionado
- Instruções oficiais para instalar o pacote direto do PyPI usando `pip` ou `uv`.

### Corrigido
- Publicação do módulo `mangaba_ai` como pacote raiz (agora `pip install mangaba` expõe `MangabaAgent` corretamente).
- Versão alinhada entre `pyproject.toml`, `setup.py` e `__version__`.

## [1.0.0] - 2024-12-19

### Adicionado
- Agente de IA básico com funcionalidades essenciais
- Sistema de configuração automática via arquivo .env
- Logger colorido e configurável
- Métodos principais:
  - `chat()` - Chat básico
  - `chat_with_context()` - Chat com contexto específico
  - `analyze_text()` - Análise de texto
  - `translate()` - Tradução de textos
  - `summarize()` - Resumo de textos
  - `code_review()` - Revisão de código
  - `explain_code()` - Explicação de código
- Exemplo básico completo
- Documentação detalhada no README
- Configuração de projeto Python com setup.py
- Testes básicos de funcionamento
- Licença MIT
- .gitignore configurado

### Características
- Configuração mínima necessária (apenas API key)
- Interface simples e intuitiva
- Logs informativos e coloridos
- Tratamento de erros robusto
- Documentação em português
- Exemplos práticos de uso

### Dependências
- google-generativeai >= 0.3.0
- python-dotenv >= 0.19.0
- loguru >= 0.6.0

### Estrutura do Projeto
```
mangaba_ai/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── setup.py
├── __init__.py
├── config.py
├── gemini_agent.py
├── test_basic.py
├── examples/
│   └── basic_example.py
└── utils/
    ├── __init__.py
    └── logger.py
```
