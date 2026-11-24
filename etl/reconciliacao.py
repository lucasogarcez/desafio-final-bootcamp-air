import psycopg2
from psycopg2.extensions import connection
from etl.carga import ErroCarga, conectar

class ErroReconciliacao(Exception):
    pass

def reconciliar_pedidos(conexao: connection, pedidos_tratados: list[dict]) -> dict[str, int | float]:
    """Calcula e compara métricas entre os dados tratados e a tabela pedidos."""
    pedidos_unicos = {pedido["id"]: pedido for pedido in pedidos_tratados}.values()

    contagem_origem = len(pedidos_unicos)
    soma_valor_itens_origem = round(sum(
        float(pedido["valor_itens"]) for pedido in pedidos_unicos
    ), 2)

    sql = "SELECT COUNT(*), COALESCE(SUM(valor_itens), 0) FROM pedidos;"
    
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            contagem_destino, soma_destino = cursor.fetchone()
    except psycopg2.Error as erro_pg:
        raise ErroReconciliacao(
            f"Erro ao consultar tabela 'pedidos' para reconciliação: {erro_pg}"
        ) from erro_pg

    soma_valor_itens_destino = round(float(soma_destino), 2)
    diferenca = round(abs(soma_valor_itens_origem - soma_valor_itens_destino), 2)

    return {
        "contagem_origem": int(contagem_origem),
        "contagem_destino": int(contagem_destino),
        "soma_valor_itens_origem": soma_valor_itens_origem,
        "soma_valor_itens_destino": soma_valor_itens_destino,
        "diferenca": diferenca,
    }
    
def executar_reconciliacao(pedidos_tratados: list[dict]) -> dict[str, int | float] | None:
    conexao = None
    
    try:
        conexao = conectar()
        dados_reconciliados = reconciliar_pedidos(conexao, pedidos_tratados)
        
        print(
            f"reconciliacao: soma_valor_itens_origem={dados_reconciliados['soma_valor_itens_origem']} "
            f"soma_valor_itens_destino={dados_reconciliados['soma_valor_itens_destino']} "
            f"diferenca={dados_reconciliados['diferenca']}"
        )
        
        return dados_reconciliados
    except (ErroCarga, ErroReconciliacao) as erro:
        print(f"Erro de reconciliação: {erro}")
        return None
    finally:
        if conexao is not None:
            conexao.close()