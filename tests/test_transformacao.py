from datetime import date
import pytest
from etl.transformacao import converter_data, converter_valor, remover_pedidos_repetidos, tratar_email, padronizar_estado, calcular_valor_itens, marcar_divergencia, validar_cliente_id, validar_produto_id, transformar_clientes, transformar_pedidos

# A3
@pytest.mark.parametrize("entrada, esperado", [
    ("2024-02-28", date(2024, 2, 28)),
    ("2023-04-02", date(2023, 4, 2)),
    ("  05/03/2026 ", date(2026, 3, 5)),
    (" 2025-12-01   ", date(2025, 12, 1))
])
def test_converter_data_formatos_validos_retorna_date(entrada, esperado):
    assert converter_data(entrada) == esperado
    
@pytest.mark.parametrize("entrada_invalida", [
    "30/02/2026", "2024-13-01", "2024.08.02", ""
])
def test_converter_data_invalida_retorna_value_error(entrada_invalida):
    with pytest.raises(ValueError):
        converter_data(entrada_invalida)
        
@pytest.mark.parametrize("entrada_nao_string", [
    20260228, None
])
def test_converter_data_tipo_nao_string_retorna_type_error(entrada_nao_string):
    with pytest.raises(TypeError):
        converter_data(entrada_nao_string)
        
#A4
@pytest.mark.parametrize("entrada, esperado", [
    ("125,746", 125.75),
    ("125,84", 125.84),
    (" 1230,4857  ", 1230.49),
    ("83,499", 83.50),
    ("  23245,558 ", 23245.56)
])
def test_converter_valor_com_virgula_arredonda_duas_casas(entrada, esperado):
    assert converter_valor(entrada) == esperado
    
@pytest.mark.parametrize("entrada, esperado", [
    (10, 10.00),
    (10.999, 11.00)
])
def test_converter_valor_inteiro_e_float_retorna_float_arredondado(entrada, esperado):
    assert converter_valor(entrada) == esperado
    
@pytest.mark.parametrize("entrada_invalida", [
    "abc", "10-9", "   ", ""
])
def test_converter_valor_texto_invalido_ou_vazio_retorna_value_error(entrada_invalida):
    with pytest.raises(ValueError):
        converter_valor(entrada_invalida)
        
# A5
def test_remover_pedidos_repetidos_mantem_primeira_ocorrencia_e_ordem():
    pedidos_brutos = [
        {"id": 30, "valor": 125.84},
        {"id": 10, "valor": 40.58},
        {"id": 24, "valor": 999.0},
        {"id": 10, "valor": 125.84},
    ]
    resultado = remover_pedidos_repetidos(pedidos_brutos)
    
    esperado = [
        {"id": 30, "valor": 125.84},
        {"id": 10, "valor": 40.58},
        {"id": 24, "valor": 999.0},
    ]
    
    assert len(resultado) == 3
    assert resultado[1] == {"id": 10, "valor": 40.58}
    assert resultado[2]["id"] == 24
    assert resultado == esperado
    
def test_remover_pedidos_repetidos_sem_duplicatas_retorna_lista_intacta():
    pedidos_brutos = [
        {"id": 10, "valor": 125.84},
        {"id": 24, "valor": 40.58},
        {"id": 16, "valor": 999.0},
        {"id": 30, "valor": 12.39},
        {"id": 2, "valor": 94.34},
    ]
    resultado = remover_pedidos_repetidos(pedidos_brutos)
    
    assert len(resultado) == 5
    assert resultado[2] == {"id": 16, "valor": 999.0}
    assert resultado[0]["valor"] == 125.84
    assert resultado[4]["id"] == 2

def test_remover_pedidos_repetidos_lista_vazia_retorna_vazio():
    pedidos_brutos = []
    
    resultado = remover_pedidos_repetidos(pedidos_brutos)
    
    assert len(resultado) == 0
    assert resultado == []
    
# A1
class TestTratarEmailA1:
    """Suíte completa para o requisito A1 (limpeza e normalização de e-mails)."""

    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            # Caso padrão sem alterações
            ("cliente@dominio.com.br", "cliente@dominio.com.br"),
            # Espaços simples nas extremidades
            ("   cliente@dominio.com   ", "cliente@dominio.com"),
            # Preservação de caixa (A1 não exige .lower(), garante que não altera case)
            ("  User.Name+Tag@Sub.Dominio.COM  ", "User.Name+Tag@Sub.Dominio.COM"),
            # String sem arroba (A1 apenas limpa espaços, não valida formato RFC de e-mail)
            ("  texto_sem_arroba  ", "texto_sem_arroba"),
        ],
    )
    def test_tratar_email_strings_validas_remove_apenas_espacos_extremidades(
        self, entrada, esperado
    ):
        resultado = tratar_email(entrada)
        assert resultado == esperado
        assert isinstance(resultado, str)

    @pytest.mark.parametrize(
        "entrada_ausente",
        [
            None,
            "",
            " ",
            "       ",
        ],
    )
    def test_tratar_email_ausente_ou_vazio_retorna_none(self, entrada_ausente):
        assert tratar_email(entrada_ausente) is None

    @pytest.mark.parametrize(
        "entrada",
        [None, "", "   ", "  teste@etl.com \n", "valido@etl.com"],
    )
    def test_tratar_email_idempotencia(self, entrada):
        """Aplicar tratar_email duas vezes deve produzir exatamente o mesmo resultado."""
        primeira_passada = tratar_email(entrada)
        segunda_passada = tratar_email(primeira_passada)
        assert primeira_passada == segunda_passada

# A2
@pytest.mark.parametrize("entrada, esperado", [
    ("mg ", "MG"),
    ("   sp ", "SP"),
    (" rj    ", "RJ"), 
    ("   go   ", "GO")
])
def test_padronizar_estado_minusculo_com_espacos_retorna_sigla_maiuscula(entrada, esperado):
    assert padronizar_estado(entrada) == esperado

@pytest.mark.parametrize("entrada", [
    "Minas", "M", ""
])
def test_padronizar_estado_tamanho_diferente_de_dois_retorna_value_error(entrada):
    with pytest.raises(ValueError):
        assert padronizar_estado(entrada)

@pytest.mark.parametrize("entrada", [
    None, 31, 94.3, True
])
def test_padronizar_estado_tipo_nao_string_retorna_type_error(entrada):
    with pytest.raises(TypeError):
        assert padronizar_estado(entrada)

# A6
def test_calcular_valor_itens_multiplos_produtos_retorna_soma_arredondada():
    itens_brutos = [
        {"produto_id": 1, "quantidade": 3, "preco_unitario": 4.5},
        {"produto_id": 5, "quantidade": 2, "preco_unitario": 134.57},
        {"produto_id": 2, "quantidade": 3, "preco_unitario": 37.0},
    ]
    
    assert calcular_valor_itens(itens_brutos) == 393.64
    
def test_calcular_valor_itens_lista_vazia_retorna_zero():
    itens_brutos = []
    
    assert calcular_valor_itens(itens_brutos) == 0.0
    
def test_calcular_valor_itens_quantidade_zero_retorna_zero():
    itens_brutos = [
        {"produto_id": 1, "quantidade": 0, "preco_unitario": 50.0},
    ]
    
    assert calcular_valor_itens(itens_brutos) == 0.0
    
def test_marcar_divergencia_valores_iguais_retorna_false():
    
    assert marcar_divergencia(100.00, 100.00) is False
    assert marcar_divergencia(4.9, 4.9) is False
    assert marcar_divergencia(324.98, 324.98) is False
    assert marcar_divergencia(0.1, 0.1) is False

def test_marcar_divergencia_diferenca_exata_de_um_centavo_retorna_false():
    
    assert marcar_divergencia(100.00, 100.01) is False
    assert marcar_divergencia(99.99, 100.00) is False
    assert marcar_divergencia(0.01, 0.02) is False
    
def test_marcar_divergencia_diferenca_maior_que_um_centavo_retorna_true():
    
    assert marcar_divergencia(100.00, 100.02) is True
    assert marcar_divergencia(100.00, 99.98) is True
    assert marcar_divergencia(0.00, 0.02) is True
    
# Testes de chaves estrangeiras
def test_validar_cliente_id_existente_retorna_id():
    assert validar_cliente_id(10, {10, 20, 30}) == 10
    
def test_validar_cliente_id_inexistente_retorna_value_error():
    with pytest.raises(ValueError):
        validar_cliente_id(99, {10, 20, 30})

@pytest.mark.parametrize("entrada_invalida", [
    True, False, "10", 10.0, None
])
def test_validar_cliente_id_tipo_invalido_retorna_value_error(entrada_invalida):
    with pytest.raises(ValueError):
        validar_cliente_id(entrada_invalida, {10, 20, 30})
        
def test_validar_produto_id_existente_retorna_id():
    assert validar_produto_id(5, {1, 5, 9}) == 5
    
def test_validar_produto_id_inexistente_retorna_value_error():
    with pytest.raises(ValueError):
        validar_produto_id(77, {1, 5, 9})
        
@pytest.mark.parametrize("entrada_invalida", [
    True, False, "5", 8.5, None
])
def test_validar_produto_id_tipo_invalido_retorna_value_error(entrada_invalida):
    with pytest.raises(ValueError):
        validar_produto_id(entrada_invalida, {1, 5, 9})

# Testes de fora do escopo
def test_valor_total_negativo_carrega_sem_erro():
    pedidos_brutos = [
        {
            "id": 1,
            "cliente_id": 100,
            "data_pedido": "2026-05-10",
            "status": "entrege",
            "valor_total": "-50,00",
            "itens": [
                {"produto_id": 10, "quantidade": 1, "preco_unitario": 35.0}
            ],
        }
    ]
    
    resultado = transformar_pedidos(pedidos_brutos, ids_clientes=[100], ids_produtos=[10])
    
    assert len(resultado["pedidos"]) == 1
    assert resultado["pedidos"][0]["valor_total"] == -50.00
    assert resultado["pedidos"][0]["divergente"] is True
    
def test_pedido_com_itens_vazio_carrega_com_valor_itens_zero():
    pedidos_brutos = [
        {
            "id": 2,
            "cliente_id": 100,
            "data_pedido": "2026-05-10",
            "status": "cancelado",
            "valor_total": 10.0,
            "itens": [],
        }
    ]
    resultado = transformar_pedidos(pedidos_brutos, ids_clientes=[100], ids_produtos=[10])

    assert len(resultado["pedidos"]) == 1
    assert resultado["pedidos"][0]["valor_itens"] == 0.0
    assert resultado["pedidos"][0]["divergente"] is True
    assert resultado["itens"] == []


def test_pedido_com_chave_itens_ausente_levanta_key_error():
    pedidos_brutos = [
        {
            "id": 3,
            "cliente_id": 100,
            "data_pedido": "2026-05-10",
            "status": "em_transporte",
            "valor_total": 100.0,
            # chave "itens" retirada propositalmente
        }
    ]
    
    with pytest.raises(KeyError):
        transformar_pedidos(pedidos_brutos, ids_clientes=[100], ids_produtos=[10])