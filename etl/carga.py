import decouple
import psycopg2
from psycopg2.extensions import connection

class ErroCarga(Exception):
    pass

def conectar() -> connection:
    try:
        return psycopg2.connect(
            host=decouple.config("DB_HOST", default="localhost"),
            port=decouple.config("DB_PORT", default="5432", cast=int),
            dbname=decouple.config("DB_NAME"),
            user=decouple.config("DB_USER"),
            password=decouple.config("DB_PASSWORD")
        )
    except psycopg2.OperationalError as erro:
        raise ErroCarga("Não foi possível conectar ao PostgreSQL. Verifique suas credenciais.") from erro
    
def limpar_tabelas(conexao: connection) -> None:
    sql = "TRUNCATE TABLE itens_pedido, pedidos, clientes, produtos;"
    with conexao.cursor() as cursor:
        cursor.execute(sql)
        
def carregar_produtos(conexao: connection, produtos: list[dict]) -> None:
    sql = """
        INSERT INTO produtos (produto_id, nome, categoria, preco_base)
        VALUES (%s, %s, %s, %s);
    """
    
    valores = [
        (
            produto["produto_id"],
            produto["nome"],
            produto["categoria"],
            produto["preco_base"]
        )
        for produto in produtos
    ]
    
    with conexao.cursor() as cursor:
        cursor.executemany(sql, valores)
        
def carregar_clientes(conexao: connection, clientes: list[dict]) -> None:
    sql = """
        INSERT INTO clientes (id, nome, email, cidade, estado, cadastro_em)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    
    valores = [
        (
            cliente["id"],
            cliente["nome"],
            cliente["email"],
            cliente["cidade"],
            cliente["estado"],
            cliente["cadastro_em"]
        )
        for cliente in clientes
    ]
    
    with conexao.cursor() as cursor:
        cursor.executemany(sql, valores)
        
def carregar_pedidos(conexao: connection, pedidos: list[dict]) -> None:
    sql = """
        INSERT INTO pedidos (id, cliente_id, data_pedido, status, valor_total, valor_itens, divergente)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    
    valores = [
        (
            pedido["id"],
            pedido["cliente_id"],
            pedido["data_pedido"],
            pedido["status"],
            pedido["valor_total"],
            pedido["valor_itens"],
            pedido["divergente"]
        )
        for pedido in pedidos
    ]
    
    with conexao.cursor() as cursor:
        cursor.executemany(sql, valores)
        
def carregar_itens_pedido(conexao: connection, itens: list[dict]) -> None:
    sql = """
        INSERT INTO itens_pedido (pedido_id, linha, produto_id, quantidade, preco_unitario)
        VALUES (%s, %s, %s, %s, %s);
    """
    
    valores = [
        (
            item["pedido_id"],
            item["linha"],
            item["produto_id"],
            item["quantidade"],
            item["preco_unitario"]
        )
        for item in itens
    ]
    
    with conexao.cursor() as cursor:
        cursor.executemany(sql, valores)
        
def contar_registros(conexao: connection) -> dict[str, int]:
    sql = """
        SELECT
            (SELECT COUNT(*) FROM clientes),
            (SELECT COUNT(*) FROM produtos),
            (SELECT COUNT(*) FROM pedidos),
            (SELECT COUNT(*) FROM itens_pedido);
        """
    
    with conexao.cursor() as cursor:
        cursor.execute(sql)
        clientes, produtos, pedidos, itens = cursor.fetchone()

    return {"clientes": clientes, "produtos": produtos, "pedidos": pedidos, "itens_pedido": itens}

def executar_carga(dados_tratados: dict[str, list[dict]]) -> dict[str, int] | None:
    conexao = None
    try:
        conexao = conectar()
        
        limpar_tabelas(conexao)
        carregar_produtos(conexao, dados_tratados["produtos"])
        carregar_clientes(conexao, dados_tratados["clientes"])
        carregar_pedidos(conexao, dados_tratados["pedidos"])
        carregar_itens_pedido(conexao, dados_tratados["itens"])
        
        conexao.commit()
        
        contagens = contar_registros(conexao)
        print(f"carga: clientes={contagens['clientes']} produtos={contagens['produtos']} pedidos={contagens['pedidos']} itens={contagens['itens_pedido']}")
        
        return contagens
    except ErroCarga as erro:
        print(f"Erro na carga: {erro}")
        return None
    except psycopg2.Error as erro_pg:
        if conexao is not None:
            conexao.rollback()
        print(f"Erro: banco de dados falhou durante carga (transação revertida): {erro_pg}")
        return None
    finally:
        if conexao is not None:
            conexao.close()