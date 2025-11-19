# ⚡ Quick Start - Mangaba AI com UV

Bem-vindo! Este arquivo te guia em 5 minutos para começar.

---

## 🚀 Instalação Rápida (Windows PowerShell)

### Passo 1: Instalar UV (2 minutos)

```powershell
# Instala UV via WinGet (mais rápido)
winget install astral-sh.uv

# Ou via Chocolatey
choco install uv

# Ou via Python
pip install uv

# Verificar
uv --version
```

### Passo 2: Setup do Projeto (1 minuto)

```powershell
# Sincronizar dependências
uv sync

# Ou se preferir sem dev dependencies
uv sync --no-dev
```

### Passo 3: Executar Exemplo (1 minuto)

```powershell
# Opção 1: Executar exemplo básico
uv run python examples/basic_example.py

# Opção 2: Usar agente interativamente
uv run python -c "
from mangaba_ai import MangabaAgent
agent = MangabaAgent()
print('✅ Agente criado com sucesso!')
print(agent)
"

# Opção 3: Rodar testes
uv run pytest
```

### Passo 4: Configurar .env (1 minuto)

```powershell
# Copiar template
copy config_template.json .env

# Editar arquivo
# Adicione sua GOOGLE_API_KEY
```

---

## 📚 Documentação Essencial

| Documento | Quando Ler |
|-----------|-----------|
| [docs/UV_SETUP.md](docs/UV_SETUP.md) | Para aprender UV em detalhes |
| [docs/MIGRACAO_PIP_UV.md](docs/MIGRACAO_PIP_UV.md) | Se vem de pip/outro projeto |
| [SUMARIO_EXECUTIVO.md](SUMARIO_EXECUTIVO.md) | Resumo executivo das mudanças |
| [AVALIACAO_PROJETO.md](AVALIACAO_PROJETO.md) | Para entender o projeto |

---

## 🔧 Comandos UV Essenciais

```bash
# Instalação
uv sync                        # Instala tudo
uv sync --no-dev              # Sem dependências dev

# Executar código
uv run python script.py        # Executa script
uv run pytest                  # Roda testes
uv run pytest --cov           # Com cobertura

# Gerenciar pacotes
uv add requests               # Adiciona dependência
uv remove requests            # Remove dependência

# Ambiente
uv venv                       # Cria .venv (se necessário)
source .venv/bin/activate     # Ativa (macOS/Linux)
.\.venv\Scripts\Activate.ps1  # Ativa (Windows)

# Limpeza
uv cache clean                # Limpa cache
uv sync --refresh             # Força atualização
```

---

## ❓ Dúvidas Rápidas

**P: Posso usar pip em vez de UV?**  
R: Sim! Mantemos compatibilidade: `pip install -r requirements.txt`

**P: Preciso fazer algo especial?**  
R: Não. Execute `uv sync` e pronto!

**P: Qual a diferença de UV vs pip?**  
R: UV é 10-100x mais rápido e mais seguro. [Leia mais](docs/MIGRACAO_PIP_UV.md)

**P: Como contribuo?**  
R: Consulte [docs/CONTRIBUICAO.md](docs/CONTRIBUICAO.md)

---

## 📁 Estrutura do Projeto

```
mangaba_ai/
├── 📖 README.md              # Visão geral
├── ⚙️  pyproject.toml         # Configuração (novo!)
├── 🔒 uv.lock                # Lock file (new!)
│
├── 🤖 mangaba_agent.py       # Agente principal
├── 🌐 protocols/             # Protocolos A2A, MCP
├── 📝 examples/              # 11 exemplos práticos
├── 🧪 tests/                 # Testes
│
├── 📁 scripts/
│   ├── uv_setup.py          # Setup automático
│   ├── validate_env.py      # Validar setup
│   └── ...
│
├── 📁 docs/
│   ├── UV_SETUP.md          # Guia UV
│   ├── MIGRACAO_PIP_UV.md  # Migração
│   ├── WIKI.md             # Portal da documentação avançada
│   └── ...
```

---

## 🎯 Próximos Passos

1. ✅ **Instalar UV** (se não tiver)
2. ✅ **Executar** `uv sync`
3. ✅ **Testar** `uv run python examples/basic_example.py`
4. ✅ **Configurar** `.env` com suas chaves
5. ✅ **Explorar** documentação em `docs/`

---

## 🚨 Problemas?

### UV não está instalado?
```powershell
# Windows
winget install astral-sh.uv

# macOS
brew install uv

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Erro ao sincronizar?
```bash
uv sync --refresh   # Força atualização
uv cache clean      # Limpa cache
```

### Precisa de mais ajuda?
- 📖 [docs/UV_SETUP.md](docs/UV_SETUP.md) - Troubleshooting
- ❓ [docs/MIGRACAO_PIP_UV.md](docs/MIGRACAO_PIP_UV.md) - FAQ
- 🐛 [GitHub Issues](https://github.com/mangaba-ai/mangaba-ai/issues)

---

## 💡 Dica Extra

Se estiver usando VS Code, instale a extensão **Python** para melhor suporte:

```
Ctrl+Shift+X → Buscar "Python" → Instalar
```

---

## 📞 Precisa de Ajuda?

**Para começar:** Leia [docs/UV_SETUP.md](docs/UV_SETUP.md)  
**Para migrar:** Leia [docs/MIGRACAO_PIP_UV.md](docs/MIGRACAO_PIP_UV.md)  
**Para entender tudo:** Leia [AVALIACAO_PROJETO.md](AVALIACAO_PROJETO.md)  

---

**Bem-vindo ao Mangaba AI! 🥭✨**

*Pronto? Execute: `uv sync` e `uv run python examples/basic_example.py`*
