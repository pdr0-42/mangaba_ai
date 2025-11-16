# 🔄 Integração com CI/CD - GitHub Actions

Guia para integrar **UV** nas suas pipelines de CI/CD.

---

## 📋 GitHub Actions com UV

### Arquivo: `.github/workflows/test.yml`

```yaml
name: Tests with UV

on:
  push:
    branches: [ master, develop ]
  pull_request:
    branches: [ master, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install UV
        uses: astral-sh/setup-uv@v1
        with:
          version: "latest"
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Sync dependencies
        run: uv sync --group dev
      
      - name: Run linting
        run: |
          uv run black --check .
          uv run isort --check-only .
          uv run flake8 .
      
      - name: Run tests
        run: uv run pytest --cov=. --cov-report=xml
      
      - name: Run type checking
        run: uv run mypy .
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
```

---

## 🚀 Workflows Adicionais

### 1. Build e Deploy

```yaml
name: Build and Deploy

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Sync dependencies
        run: uv sync
      
      - name: Build package
        run: |
          uv pip install build
          uv run python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

### 2. Verificação de Segurança

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: uv sync --group dev
      
      - name: Security scan with bandit
        run: uv run bandit -r . -ll
      
      - name: Dependency scan
        run: |
          uv pip install safety
          uv run safety check
```

### 3. Benchmark de Performance

```yaml
name: Performance Benchmark

on:
  push:
    branches: [master]
  pull_request:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Run benchmarks
        run: |
          uv sync --group dev
          uv run pytest-benchmark --compare
```

---

## 📊 Exemplo Completo: Multi-Stage Pipeline

```yaml
name: Complete CI/CD Pipeline

on:
  push:
    branches: [ master, develop ]
  pull_request:
    branches: [ master ]

jobs:
  # ✅ Fase 1: Verificações Rápidas
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: uv sync --group dev
      
      - name: Black
        run: uv run black --check .
      
      - name: isort
        run: uv run isort --check-only .
      
      - name: flake8
        run: uv run flake8 .
      
      - name: mypy
        run: uv run mypy . --ignore-missing-imports

  # ✅ Fase 2: Testes Unitários
  test:
    name: Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: lint
    
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: uv sync --group dev
      
      - name: Run tests
        run: uv run pytest --cov=. --cov-report=term-missing
      
      - name: Coverage report
        run: uv run coverage xml

  # ✅ Fase 3: Integração
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: uv sync --group dev
      
      - name: Run integration tests
        run: uv run pytest tests/ -m integration -v
      
      - name: Test examples
        run: |
          uv run python examples/basic_example.py --test
          uv run python examples/api_integration_example.py --test

  # ✅ Fase 4: Build (apenas em master)
  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, test, integration]
    if: github.ref == 'refs/heads/master'
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: astral-sh/setup-uv@v1
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Build distribution
        run: |
          uv pip install build
          uv run python -m build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: python-package-distributions
          path: dist/
```

---

## 🔐 Variáveis de Ambiente

### GitHub Secrets

Adicione no repositório (Settings → Secrets → Actions):

```bash
# Para publicar no PyPI
PYPI_API_TOKEN=pypi-...

# Para notificações
SLACK_WEBHOOK=https://hooks.slack.com/...

# Para testes com APIs reais
TEST_API_KEY=...
```

### No Workflow:

```yaml
env:
  PYTHON_VERSION: "3.11"
  UV_CACHE_DIR: ~/.cache/uv

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --group dev
      - run: |
          uv run pytest \
            --cov \
            -k "not slow" \
            -v
        env:
          API_KEY: ${{ secrets.TEST_API_KEY }}
```

---

## 📈 Monitoramento e Notificações

### Slack Notifications

```yaml
      - name: Notify Slack on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "❌ CI Pipeline failed on ${{ github.ref }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Build Failed* 🔴\nRepo: ${{ github.repository }}\nBranch: ${{ github.ref_name }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Email Notifications

```yaml
      - name: Email on failure
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.GMAIL_USERNAME }}
          password: ${{ secrets.GMAIL_PASSWORD }}
          subject: "CI/CD Pipeline failed"
          to: dev@example.com
          from: ci@example.com
          body: |
            Pipeline failed on ${{ github.ref }}
            Commit: ${{ github.sha }}
```

---

## 🔍 Coverage Report

### Gerar e Publicar

```yaml
      - name: Generate coverage report
        run: |
          uv sync --group dev
          uv run pytest --cov=. --cov-report=html --cov-report=xml
      
      - name: Upload to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: false
      
      - name: Comment PR with coverage
        if: github.event_name == 'pull_request'
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ github.token }}
```

---

## 🎯 Best Practices

### 1. Cache UV

```yaml
      - name: Cache UV
        uses: actions/cache@v3
        with:
          path: ~/.cache/uv
          key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}
          restore-keys: |
            ${{ runner.os }}-uv-
```

### 2. Matrix Testing

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
  fail-fast: false  # Continua mesmo se um falhar
```

### 3. Conditional Execution

```yaml
jobs:
  deploy:
    if: github.event_name == 'release' && github.event.action == 'published'
    runs-on: ubuntu-latest
```

### 4. Secrets Seguros

```yaml
      - name: Never log secrets
        run: |
          # ❌ NUNCA faça isso
          # echo "API_KEY=${{ secrets.API_KEY }}"
          
          # ✅ Sempre use como var de ambiente
          uv run python script.py
        env:
          API_KEY: ${{ secrets.API_KEY }}
```

---

## 📊 Exemplo com Badges

```markdown
[![Tests](https://github.com/mangaba-ai/mangaba-ai/actions/workflows/test.yml/badge.svg)](https://github.com/mangaba-ai/mangaba-ai/actions)
[![Coverage](https://codecov.io/gh/mangaba-ai/mangaba-ai/branch/master/graph/badge.svg)](https://codecov.io/gh/mangaba-ai/mangaba-ai)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![UV](https://img.shields.io/badge/Powered%20by-UV-blue)](https://astral.sh/uv)
```

---

## 🚀 Deploy Automático

### Para PyPI

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Build and publish
        run: |
          uv pip install build twine
          uv run python -m build
          uv run twine upload dist/* -u __token__ -p ${{ secrets.PYPI_TOKEN }}
```

---

## 📚 Referências

- 📖 [GitHub Actions Docs](https://docs.github.com/en/actions)
- 📖 [UV GitHub Action](https://github.com/astral-sh/setup-uv)
- 📖 [Codecov Integration](https://codecov.io/)
- 📖 [Python Testing Best Practices](https://docs.pytest.org/)

---

**Seu CI/CD está pronto! 🚀**
