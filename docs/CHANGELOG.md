# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-04-22

### Adicionado
- 🤗 **Catálogo de modelos HuggingFace open-source** — 28 modelos curados com metadados completos (`id`, `name`, `category`, `context`, `tool_calling`, `streaming`, `notes`)
  - 19 modelos `general`: Mistral, Mixtral, Llama 3/3.1/3.2, Qwen 2.5, Phi-3/3.5, Gemma 2
  - 4 modelos `code`: StarCoder2 15B, Qwen 2.5 Coder 7B/32B, DeepSeek Coder 33B
  - 2 modelos `reasoning`: DeepSeek R1 Distill Qwen 7B e Llama 70B
  - 3 modelos `embedding`: BGE-M3, all-MiniLM-L6-v2, Multilingual E5 Large
- 🔍 **`list_huggingface_models(category=None)`** — função pública para listar/filtrar modelos por categoria
- 📦 **`HF_OPEN_MODELS`** — constante exportada no topo do pacote (`from mangaba import HF_OPEN_MODELS`)
- 🔧 **`HuggingFaceLLMProvider.list_models(category=None)`** — classmethod no provider para acesso direto
- 📚 **Documentação de padrões de projeto** — seção no README mapeando todos os padrões GoF usados no framework
- 🔄 Modelo padrão HuggingFace atualizado para `mistralai/Mistral-7B-Instruct-v0.3`

### Alterado
- `mangaba/core/llm/__init__.py` — exporta `list_huggingface_models` e `HF_OPEN_MODELS`
- `mangaba/__init__.py` — exporta `list_huggingface_models` e `HF_OPEN_MODELS` no topo do pacote
- **`HuggingFaceLLMProvider`** migrado de `text_generation` (API legada) para `chat_completion` (OpenAI-compatible):
  - `generate()` — usa `chat_completion` com suporte a `system_prompt` e `TokenUsage`
  - `stream()` — streaming real token a token via `chat_completion(stream=True)`
  - `generate_with_tools()` — injeção de tools via system message no formato chat

### Corrigido
- Streaming HuggingFace não funcionava com modelos de instrução modernos (Llama 3, Mistral v0.3, Qwen 2.5) porque usava `text_generation` em vez de `chat_completion`

## [3.1.1] - 2026-04-22

### Adicionado
- **Tool calling nativo para 11 modelos HuggingFace** — detecção automática: usa `chat_completion(tools=[...])` para modelos que suportam; cai em prompt injection como fallback para os demais
  - Nativo: Mistral 7B/Mixtral 8x7B/8x22B/Nemo, Llama 3.1 8B/70B/405B, Qwen 2.5 7B/72B, Qwen 2.5 Coder 7B/32B
  - Prompt-based: Llama 3.0, Llama 3.2, Gemma 2, Phi-3, StarCoder2, DeepSeek Coder, DeepSeek R1
- **`hf_model_supports_tools(model_id)`** — função pública para verificar suporte nativo por model ID
- **`_HF_NATIVE_TOOL_MODELS`** — índice interno de modelos com function calling nativo
- Campo `tool_calling` corrigido no catálogo `HF_OPEN_MODELS` (era `False` para todos; agora reflete suporte real)

### Alterado
- `HuggingFaceLLMProvider.generate_with_tools()` — lógica de despacho: nativo quando possível, prompt injection como fallback
- `mangaba/core/llm/__init__.py` e `mangaba/__init__.py` — exportam `hf_model_supports_tools`

## [2.0.4] - 2026-02-13

### Corrigido
- 🔗 URLs do GitHub agora usam branch correto: `/blob/master/` em vez de `/blob/main/`
- ✅ Todos os links da documentação funcionam corretamente no GitHub e PyPI
- 🌐 Branches desnecessários removidos (main e copilot)
- 📚 Mantido apenas branch master como padrão

### Garantido
- ✓ Links para WIKI.md funcionam
- ✓ Links para README.md (índice) funcionam
- ✓ Links para todos os arquivos de documentação funcionam
- ✓ URLs corretas: `github.com/Mangaba-ai/mangaba_ai/blob/master/`

## [2.0.3] - 2026-02-13

### Corrigido
- 🔗 URLs do GitHub corrigidas no README.md
- ✅ Nome correto do repositório: `Mangaba-ai/mangaba_ai` (em vez de `mangaba-ai/mangaba-ai`)
- 🌐 Todos os links da documentação agora funcionam corretamente

## [2.0.2] - 2026-02-13

### Corrigido
- 🔗 Conversão de todos os links relativos para URLs absolutas do GitHub no README.md
- ✅ Links agora funcionam corretamente tanto no GitHub quanto no PyPI
- 📚 Links para documentação (WIKI.md, CURSO_BASICO.md, FAQ.md, etc.)
- 📁 Links para arquivos (ESTRUTURA.md, docs/README.md)
- 🔧 Links para scripts (validate_env.py, quick_setup.py, etc.)
- 📋 Link "ÍNDICE COMPLETO" corrigido para apontar para docs/README.md

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
