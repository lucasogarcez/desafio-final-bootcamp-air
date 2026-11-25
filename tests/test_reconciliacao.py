import pytest
from etl.carga import carregar_clientes, carregar_itens_pedido, carregar_pedidos, carregar_produtos, conectar, limpar_tabelas
from etl.reconciliacao import reconciliar_pedidos
from etl.transformacao import executar_transformacao

@pytest.fixture
def banco_carregado():
    """Executa transformação e carga real no PostgreSQL dentro de uma transação isolada."""
    dados_brutos = {
        "clientes": [
            {
                "id": 1,
                "nome": "Ana",
                "email": "  ana@email.com  ",
                "cidade": "Uberaba",
                "estado": "mg",
                "cadastro_em": "2026-01-10",
            }
        ],
        "produtos": [
            {
                "produto_id": "10",
                "nome": "Teclado",
                "categoria": "Periféricos",
                "preco_base": "100,00",
            },
            {
                "produto_id": "20",
                "nome": "Cabo",
                "categoria": "Acessórios",
                "preco_base": "10,33",
            },
        ],
        "pedidos": [
            {
                "id": 101,
                "cliente_id": 1,
                "data_pedido": "2026-11-20",
                "status": "pago",
                "valor_total": "131,00",
                "itens": [
                    {"produto_id": 10, "quantidade": 1, "preco_unitario": 100.0},
                    {"produto_id": 20, "quantidade": 3, "preco_unitario": 10.333},
                ],
            },
            {
                # Pedido divergente proposital (valor_total=999.00 vs valor_itens=50.00)
                # Garante que a reconciliação soma valor_itens, e não valor_total
                "id": 102,
                "cliente_id": 1,
                "data_pedido": "21/11/2026",
                "status": "pago",
                "valor_total": "999,00",
                "itens": [
                    {"produto_id": 10, "quantidade": 1, "preco_unitario": 50.0},
                ],
            },
            {
                # Pedido duplicado na origem (mesmo ID 101) — descartado pelo A5
                "id": 101,
                "cliente_id": 1,
                "data_pedido": "2026-11-20",
                "status": "pago",
                "valor_total": "131,00",
                "itens": [
                    {"produto_id": 10, "quantidade": 1, "preco_unitario": 100.0},
                    {"produto_id": 20, "quantidade": 3, "preco_unitario": 10.333},
                ],
            },
        ],
    }

    dados_tratados = executar_transformacao(dados_brutos)
    assert dados_tratados is not None

    conexao = conectar()
    try:
        limpar_tabelas(conexao)
        carregar_produtos(conexao, dados_tratados["produtos"])
        carregar_clientes(conexao, dados_tratados["clientes"])
        carregar_pedidos(conexao, dados_tratados["pedidos"])
        carregar_itens_pedido(conexao, dados_tratados["itens"])

        yield conexao, dados_tratados
    finally:
        conexao.rollback()
        conexao.close()


def test_reconciliacao_pedidos_origem_e_destino(banco_carregado):
    conexao, dados_tratados = banco_carregado

    rec = reconciliar_pedidos(conexao, dados_tratados["pedidos"])

    # Contagem exata (2 pedidos únicos: IDs 101 e 102)
    assert rec["contagem_destino"] == rec["contagem_origem"]
    assert rec["contagem_destino"] == 2

    # Soma de valor_itens (131.00 + 50.00 = 181.00) comparada com tolerância de R$ 0,01
    assert rec["soma_valor_itens_destino"] == pytest.approx(
        rec["soma_valor_itens_origem"], abs=0.01
    )
    assert rec["soma_valor_itens_destino"] == pytest.approx(181.00, abs=0.01)