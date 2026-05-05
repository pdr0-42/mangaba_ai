import pytest
import os
import shutil
from mangaba.vectorstores import VectorStoreFactory

# Configurações de caminhos temporários para os testes
SQLITE_PATH = "test_mangaba_local.db"
CHROMA_PATH = "./test_chroma_db"


@pytest.fixture(params=["sqlite", "chroma"])
def vector_store(request, tmp_path):
    if request.param == "sqlite":
        # tmp_path é uma fixture do pytest que cria pastas temporárias seguras
        db_path = tmp_path / "test.db"
        store = VectorStoreFactory.get_store(str(db_path))
    else:
        chroma_dir = tmp_path / "chroma_test"
        store = VectorStoreFactory.get_store(f"chroma://{chroma_dir}")

    yield store
    store.clear()


# --- CASOS DE TESTE ---


def test_add_and_count(vector_store):
    """Verifica se a inserção e a contagem de itens funcionam."""
    texts = ["Sistema de Detecção", "Logs de Firewall"]
    embeddings = [[0.1, 0.2, 0.3], [0.8, 0.9, 0.1]]

    ids = vector_store.add(texts, embeddings)

    assert len(ids) == 2
    assert vector_store.count == 2


def test_search_similarity(vector_store):
    """Valida se a busca retorna o item semanticamente mais próximo."""
    # Adicionamos dois conceitos opostos
    texts = ["Acesso negado", "Acesso permitido"]
    # Vetores simplificados (IA usaria dimensões maiores)
    embeddings = [[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]]
    vector_store.add(texts, embeddings)

    # Uma query muito similar a "Acesso permitido"
    query_vector = [0.9, 0.9, 0.9]
    results = vector_store.search(query_vector, top_k=1)

    assert len(results) == 1
    assert results[0]["content"] == "Acesso permitido"
    # O score de similaridade deve ser alto
    assert results[0]["score"] > 0.9


def test_delete_item(vector_store):
    """Garante que a remoção por ID limpa o registro corretamente."""
    ids = vector_store.add(["Dado temporário"], [[0.5, 0.5, 0.5]])
    assert vector_store.count == 1

    vector_store.delete(ids)
    assert vector_store.count == 0


def test_metadata_persistence(vector_store):
    """Verifica se os metadados JSON são recuperados corretamente."""
    meta = {"severidade": "alta", "origem": "zeek"}
    vector_store.add(["Ataque detectado"], [[0.1, 0.1, 0.1]], metadatas=[meta])

    results = vector_store.search([0.1, 0.1, 0.1], top_k=1)
    assert results[0]["metadata"]["severidade"] == "alta"
