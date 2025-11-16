# 🚀 Instalação com UV - Gerenciador de Pacotes Python Moderno

## O que é UV?

`uv` é um gerenciador de pacotes Python **ultra-rápido** e moderno, escrito em Rust, que oferece:
- ⚡ **10-100x mais rápido** que `pip`
- 🔒 **Resolução determinística** de dependências
- 📦 **Lock file seguro** (`uv.lock`)
- 🐍 **Gerenciamento de versões Python**
- 🎯 **Compatibilidade total** com PEP 517/518

> **Documentação oficial**: [astral.sh/uv](https://astral.sh/uv)

---

## 📋 Pré-requisitos

### Windows (PowerShell)

```powershell
# Instalação via winget (Recomendado)
winget install astral-sh.uv

# Ou via Python
pip install uv

# Verificar instalação
uv --version
```

### macOS

```bash
# Instalação via Homebrew
brew install uv

# Ou via curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verificar instalação
uv --version
```

### Linux

```bash
# Instalação via curl (Recomendado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via package manager (apt, yum, etc)
# Verificar: https://docs.astral.sh/uv/guides/installation/

# Verificar instalação
uv --version
```

---

## 🚀 Instalação Rápida do Mangaba AI com UV

### Opção 1: Setup Automático (Recomendado)

```powershell
# Windows PowerShell
uv sync
```

```bash
# macOS / Linux
uv sync
```

**O que acontece:**
- ✅ Cria ambiente virtual automático (`.venv`)
- ✅ Instala todas as dependências (do `pyproject.toml`)
- ✅ Gera `uv.lock` com versions pinadas
- ✅ Configura ambiente para desenvolvimento

### Opção 2: Setup Manual com Virtualenv

```powershell
# Windows PowerShell
uv venv                      # Cria .venv
.\.venv\Scripts\Activate.ps1  # Ativa ambiente

uv pip install -e .          # Instala em modo desenvolvimento
```

```bash
# macOS / Linux
uv venv                      # Cria .venv
source .venv/bin/activate    # Ativa ambiente

uv pip install -e .          # Instala em modo desenvolvimento
```

---

## 📦 Instalação de Dependências

### Instalar todas as dependências
```bash
uv sync
```

### Instalar apenas dependências principais
```bash
uv sync --no-dev
```

### Instalar com grupo de desenvolvimento
```bash
uv sync --group dev
```

### Instalar com grupo de testes
```bash
uv sync --group test
```

### Adicionar nova dependência
```bash
# Adiciona ao pyproject.toml e uv.lock
uv pip install requests>=2.25.0

# Ou com sintaxe uv (recomendado)
uv add requests>=2.25.0
```

### Remover dependência
```bash
uv remove requests
```

---

## 🔧 Executar Código com UV

### Executar Python com ambiente UV
```bash
# Executa script com ambiente UV
uv run python script.py

# Executa com argumentos
uv run python -c "import sys; print(sys.executable)"

# Executa pytest com UV
uv run pytest

# Executa exemplo
uv run python examples/basic_example.py
```

### Executar comandos no ambiente UV
```bash
# Ativa shell com ambiente UV
uv run python

# Executa validação
uv run python scripts/validate_env.py

# Executa setup rápido
uv run python scripts/quick_setup.py
```

---

## 🧪 Testando a Instalação

### 1. Validar ambiente
```bash
uv run python scripts/validate_env.py
```

### 2. Executar testes
```bash
# Todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov

# Testes específicos
uv run pytest tests/test_mangaba_agent.py -v

# Testes de integração
uv run pytest -m integration
```

### 3. Executar exemplo básico
```bash
uv run python examples/basic_example.py
```

### 4. Usar agente interativamente
```bash
uv run python -c "
from mangaba_ai import MangabaAgent
agent = MangabaAgent()
print(agent.chat('Olá!'))
"
```

---

## 📁 Estrutura de Arquivos com UV

```
mangaba_ai/
├── pyproject.toml        # 📋 Configuração moderna (replaces setup.py)
├── uv.lock              # 🔒 Lock file com versions pinadas
├── .venv/               # 🐍 Ambiente virtual (criado por uv sync)
├── requirements.txt     # 📦 OPCIONAL (mantém compatibilidade)
├── setup.py            # OPCIONAL (deprecated, mas mantém compatibilidade)
└── ...
```

> **Nota**: O `pyproject.toml` é o novo padrão. O `setup.py` é mantido apenas para compatibilidade.

---

## ⚡ Comandos UV Essenciais

| Comando | Descrição |
|---------|-----------|
| `uv --version` | Verifica versão do UV |
| `uv sync` | Instala dependências (cria ambiente) |
| `uv sync --no-dev` | Instala sem dependências de dev |
| `uv add <pacote>` | Adiciona dependência |
| `uv remove <pacote>` | Remove dependência |
| `uv pip install <pacote>` | Instala com pip (compatibilidade) |
| `uv run <comando>` | Executa comando no ambiente |
| `uv python list` | Lista versões Python disponíveis |
| `uv python install 3.11` | Instala versão Python específica |
| `uv venv` | Cria virtualenv manual |
| `uv cache clean` | Limpa cache |

---

## 🔄 Migrando de Pip para UV

### Antes (pip + requirements.txt)
```bash
python -m venv .venv
source .venv/bin/activate  # .\.venv\Scripts\Activate.ps1 no Windows
pip install -r requirements.txt
python script.py
```

### Depois (UV moderno)
```bash
uv sync
uv run python script.py
```

**Benefícios:**
- ✅ 10x mais rápido
- ✅ Deps garantidas com lock file
- ✅ Suporte a Python nativo
- ✅ Menos comandos necessários

---

## 🌍 Configuração de Ambiente

### 1. Copiar arquivo de exemplo
```bash
# Windows PowerShell
copy config_template.json .env

# macOS / Linux
cp config_template.json .env
```

### 2. Configurar variáveis
```bash
# Editar .env com suas credenciais
# GOOGLE_API_KEY=sua_chave_aqui
# MODEL_NAME=gemini-2.5-flash
```

### 3. Validar
```bash
uv run python scripts/validate_env.py
```

---

## 🐛 Troubleshooting

### Erro: "uv: command not found"
```bash
# Ubuntu/Debian
sudo apt install uv

# macOS
brew install uv

# Ou reinstale via curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Erro: "Python version not found"
```bash
# UV pode instalar automaticamente
uv python install 3.11

# Ou especifique a versão no pyproject.toml
requires-python = ">=3.8"
```

### Limpar cache e reinstalar
```bash
uv cache clean
uv sync --refresh
```

### Usar versão Python específica
```bash
# Cria ambiente com Python 3.11
uv venv --python 3.11

# Ou especifique ao instalar
uv sync --python 3.11
```

---

## 📚 Recursos Adicionais

### Documentação
- 📖 [UV Official Docs](https://docs.astral.sh/uv/)
- 📖 [PEP 517 - Build System Interface](https://peps.python.org/pep-0517/)
- 📖 [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- 📖 [Mangaba AI Docs](./README.md)

### Comparação com alternativas
- **pip**: Gerenciador padrão (lento, sem lock file)
- **poetry**: Alternativa moderna (mais lento que UV)
- **PDM**: Outro gerenciador moderno
- **UV**: **Ultra-rápido** (Recomendado!)

### Próximos Passos
1. ✅ Instalar UV
2. ✅ Executar `uv sync`
3. ✅ Validar ambiente
4. ✅ Usar exemplos
5. ✅ Ler documentação completa

---

## 🎯 Quick Reference

```bash
# Instalação
winget install astral-sh.uv        # Windows (ou brew install uv no macOS)

# Setup
uv sync                              # Instala tudo

# Desenvolvimento
uv run python examples/basic_example.py  # Executa exemplo
uv run pytest                        # Roda testes
uv run pytest --cov                 # Com cobertura

# Adicionar packages
uv add requests                      # Adiciona dependência
uv remove requests                   # Remove dependência

# Limpeza
uv cache clean                       # Limpa cache
```

---

**Bem-vindo ao futuro do gerenciamento de pacotes Python! 🚀**
