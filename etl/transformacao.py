from datetime import datetime

class ValorInvalidoError(Exception):
    def __init__(self, tabela, id, campo, valor, linha="", motivo=""):
        self.tabela = tabela
        self.id = id
        self.campo = campo
        self.valor = valor
        self.linha = linha
        self.motivo = motivo
        
        # Passa a mensagem formatada pra classe padrão de exceção (Exception) do Python
        super().__init__(str(self))
        
    def __str__(self):
        base = (
            f"Erro: tabela '{self.tabela} | ID: {self.id} | Campo: '{self.campo}' | Valor inválido: '{self.valor}'" 
        )
        if self.linha:
            base = f"{base} | Linha: {self.linha} "
    
        if self.motivo:
            return f"{base}({self.motivo})"
        return base

def tratar_email(valor: str|None) -> str|None:
    """A1: e-mail ausente (None, vazio ou só espaços) vira None.
    Senão, devolve o texto sem espaços."""
    if valor is not None and not isinstance(valor, str):
        raise TypeError(f"Email não é texto ou 'None': {valor!r}")
    
    if valor is None:
        return None
    texto = valor.strip()
    return texto if texto else None

def padronizar_estado(valor: str) -> str:
    """A2: remove espaços e coloca em maiúsculas a sigla do estado (2 letras).
    Se resultado maior que duas letras, retorna valor inválido."""
    if not isinstance(valor, str):
        raise TypeError(f"Estado não é texto: {valor!r}")
    
    estado_limpo = valor.strip().upper()
    if len(estado_limpo) != 2:
        raise ValueError(f"UF deve ter 2 letras, recebeu '{valor}'")
    return estado_limpo

def converter_data(valor: str) -> datetime.date:
    """A3: aceita 'AAAA-MM-DD' e 'DD/MM/AAAA' e devolve um objeto date.
    Qualquer outro formato, ou uma data que não existe, retorna ValueError."""
    if not isinstance(valor, str):
        raise TypeError(f"Data não é texto: {valor!r}")
    
    texto = valor.strip()
    
    if "/" in texto:
        formato = "%d/%m/%Y"
    elif "-" in texto:
        formato = "%Y-%m-%d"
    else:
        raise ValueError(f"Formato de data não reconhecido: {valor!r}")
    
    try:
        return datetime.strptime(texto, formato).date()
    except ValueError as erro:
        raise ValueError(f"Data inválida ({formato}: {valor!r})") from erro

def converter_valor(valor: int|float|str) -> float:
    """A4: converte texto e inteiro em float, 
    retornando um valor decimal arredondado em 2 casas decimais.
    Se não é possível converter em float (vazio, 'abc') retorna ValueError."""
    if valor is None or isinstance(valor, bool):
        raise ValueError(f"Valor inválido, recebeu '`{valor}'")
    
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            raise ValueError("Valor inválido, recebeu vazio")
        if ',' in texto:
            texto = texto.replace(",", ".")
    else:
        texto = str(valor)
        
    try:
        numero_convertido = float(texto)
    except (ValueError, TypeError) as erro:
        raise ValueError(f"Formato numérico inválido: {type(valor)}:'{valor!r}'") from erro
    
    return round(numero_convertido, 2)

def remover_pedidos_repetidos(pedidos: list[dict]) -> list[dict]:
    """A5: remove os pedidos duplicados mantendo a ordem (primeira ocorrência), 
    retornando uma lista de pedidos únicos."""
    ids_vistos = set()
    pedidos_unicos = []
    
    for pedido in pedidos:
        if pedido["id"] not in ids_vistos:
            ids_vistos.add(pedido["id"])
            pedidos_unicos.append(pedido)
    return pedidos_unicos

def calcular_valor_itens(itens: list[dict]) -> float:
    """A6: recebe os itens e faz a soma do total, olhando quantidade 
    vezes o preço unitário de cada item, retornando o valor em float
    arrendondado em 2 casas decimais."""
    valor_total_itens = 0.00
    for item in itens:
        valor_item = item["quantidade"] * item["preco_unitario"]
        valor_total_itens += valor_item
    return round(valor_total_itens, 2)

def marcar_divergencia(valor_itens: float, valor_total: float) -> bool:
    """A6: retorna se o calculo da diferença absoluta entre valor_itens e valor_total,
    arredondados em 2 casas decimais, é maior que 1 centavo."""
    return abs(round(valor_total, 2) - round(valor_itens, 2)) > 0.01

def converter_produto_id(valor: str) -> int:
    """Converte o texto vindo do CSV em inteiro.
    Texto que não é um int (vazio, '1.5', 'abc') retorna ValueError."""
    if not isinstance(valor, str):
        raise ValueError(f"Valor não é texto: {valor!r}")
    return int(valor.strip())

def validar_cliente_id(cliente_id: int, ids_clientes: set[list]) -> int:
    if isinstance(cliente_id, bool) or not isinstance(cliente_id, int):
        raise ValueError(f"ID de cliente inválido: {cliente_id!r}")
    if cliente_id not in ids_clientes:
        raise ValueError(f"O ID do cliente ({cliente_id}) não existe na base de dados de clientes.")
    return cliente_id

def validar_produto_id(produto_id:int, ids_produtos: set[list]) -> int:
    if isinstance(produto_id, bool) or not isinstance(produto_id, int):
        raise ValueError(f"ID de produto inválido: {produto_id!r}")
    if produto_id not in ids_produtos:
        raise ValueError(f"O ID do produto ({produto_id}) não existe na base de dados de produtos.")
    return produto_id

def transformar_clientes(clientes: list[dict]) -> dict[str, list[dict]] | dict[str, int]:
    """Transforma e-mail e UF dos clientes.
    Retorna dicionário com chaves 'clientes' e 'contadores', ou retorna ValorInvalidoError."""
    clientes_tratados = []
    emails_nulos = 0
    estados_padronizados = 0
    
    for cliente in clientes:
        try:
            email = tratar_email(cliente["email"])
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="clientes", 
                id=cliente["id"],
                campo="email",
                valor=cliente["email"],
                motivo=str(erro_original)
            ) from erro_original
            
        if cliente["email"] is None:
            emails_nulos += 1
            
        estado_original = cliente["estado"].strip()
        try:
            estado_novo = padronizar_estado(cliente["estado"])
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="clientes",
                id=cliente["id"],
                campo="estado",
                valor=estado_original,
                motivo=str(erro_original)
            ) from erro_original
            
        if estado_original != estado_novo:
            estados_padronizados += 1
        
        clientes_tratados.append({
            "id": cliente["id"],
            "nome": cliente["nome"],
            "email": email,
            "cidade": cliente["cidade"],
            "estado": estado_novo,
            "cadastro_em": cliente["cadastro_em"]
        })
    
    contadores = {
        "emails_nulos": emails_nulos,
        "estados_padronizados": estados_padronizados
    }
            
    return {"clientes": clientes_tratados, "contadores": contadores}

def transformar_produtos(produtos: list[dict]) -> list[dict]:
    """Transforma id do produto e preço base dos produtos.
    Retorna uma lista com dicionário contendo os produtos tratados, ou retorna ValorInvalidoError."""
    produtos_tratados = []
    
    for produto in produtos:
        try:
            produto_id = converter_produto_id(produto["produto_id"])
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="produtos",
                id=produto["produto_id"],
                campo="produto_id",
                valor=produto["produto_id"],
                motivo=str(erro_original)
            ) from erro_original
        
        try:
            preco_base = converter_valor(produto["preco_base"])
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="produtos",
                id=produto["produto_id"],
                campo="preco_base",
                valor=preco_base,
                motivo=str(erro_original)
            ) from erro_original
            
        produtos_tratados.append({
            "produto_id": produto_id,
            "nome": produto["nome"],
            "categoria": produto["categoria"],
            "preco_base": preco_base
        })
            
    return produtos_tratados

def transformar_pedidos(pedidos: list[dict], ids_clientes: list, ids_produtos: list) -> dict[str, list[dict]] | dict[str, int]:
    """Deduplica pedidos, extrai itens gerando `linha`, valida FKs, converte tipos
    e verifica divergência entre `valor_total` e `valor_itens`.
    Devolve dict com chaves 'pedidos', 'itens' e 'contadores', ou levanta ValorInvalidoError."""
    # Remover duplicatas
    registros_brutos = len(pedidos)
    lista_unicos = remover_pedidos_repetidos(pedidos)
    repetidos_descartados = registros_brutos - len(lista_unicos)

    clientes_validos = set(ids_clientes)
    produtos_validos = set(ids_produtos)

    pedidos_tratados = []
    itens_tratados = []
    datas_convertidas = 0
    valores_convertidos = 0
    divergentes = 0

    for pedido in lista_unicos:
        pedido_id = pedido["id"]
        
        # Validar "cliente_id" por pedido
        try:
            cliente_id = validar_cliente_id(pedido["cliente_id"], clientes_validos)
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="pedidos",
                id=pedido_id,
                campo="cliente_id",
                valor=pedido["cliente_id"],
                motivo=str(erro_original)
            ) from erro_original
        
        # Extrair os itens, validar "produto_id" e gerar "linha"
        itens_brutos = pedido["itens"]

        for linha, item in enumerate(itens_brutos, start=1):
            try:
                produto_id = validar_produto_id(item["produto_id"], produtos_validos)
            except ValueError as erro_original:
                raise ValorInvalidoError(
                    tabela="itens_pedido",
                    id=pedido_id,
                    campo="produto_id",
                    valor=item["produto_id"],
                    linha=linha,
                    motivo=str(erro_original),
                ) from erro_original
            
            try:
                qtd_convertida = converter_valor(item["quantidade"])
                quantidade = int(qtd_convertida)
            except ValueError as erro_original:
                raise ValorInvalidoError(
                    tabela="itens_pedido",
                    id=pedido_id,
                    campo="quantidade",
                    valor=item["quantidade"],
                    linha=linha,
                    motivo=str(erro_original)
                ) from erro_original
                
            try:
                preco_unitario = converter_valor(item["preco_unitario"])
            except ValueError as erro_original:
                raise ValorInvalidoError(
                    tabela="itens_pedido",
                    id=pedido_id,
                    campo="preco_unitario",
                    valor=item["preco_unitario"],
                    linha=linha,
                    motivo=str(erro_original)
                ) from erro_original

            itens_tratados.append({
                "pedido_id": pedido_id,
                "linha": linha,
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
            })

        # Converter datas e valores
        data_original = pedido["data_pedido"]
        try:
            data_obj = converter_data(data_original)
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="pedidos",
                id=pedido_id,
                campo="data_pedido",
                valor=data_original,
                motivo=str(erro_original),
            ) from erro_original

        if data_original != data_obj.isoformat():
            datas_convertidas += 1

        valor_total_original = pedido["valor_total"]
        try:
            valor_total = converter_valor(pedido["valor_total"])
        except ValueError as erro_original:
            raise ValorInvalidoError(
                tabela="pedidos",
                id=pedido_id,
                campo="valor_total",
                valor=pedido["valor_total"],
                motivo=str(erro_original)
            ) from erro_original

        if isinstance(valor_total_original, str): 
            valores_convertidos += 1

        # Calcular "valor_itens"
        valor_itens = calcular_valor_itens(pedido["itens"])
        
        # Comparar valores para analisar divergência
        tem_divergencia = marcar_divergencia(valor_itens, valor_total)
        if tem_divergencia:
            divergentes += 1

        pedidos_tratados.append({
            "id": pedido_id,
            "cliente_id": cliente_id,
            "data_pedido": data_obj,
            "status": pedido["status"],
            "valor_total": valor_total,
            "valor_itens": valor_itens,
            "divergente": tem_divergencia
        })

    contadores = {
        "pedidos_unicos": len(lista_unicos),
        "repetidos_descartados": repetidos_descartados,
        "datas_convertidas": datas_convertidas,
        "valores_convertidos": valores_convertidos,
        "divergentes": divergentes
    }

    return {"pedidos": pedidos_tratados, "itens": itens_tratados, "contadores": contadores}

def executar_transformacao(dados_brutos: dict[str, list[dict]]) -> dict[str, list[dict]] | None:
    try:
        res_clientes = transformar_clientes(dados_brutos["clientes"])
        clientes_tratados = res_clientes["clientes"]
        contadores_clientes = res_clientes["contadores"]
        
        produtos_tratados = transformar_produtos(dados_brutos["produtos"])
        
        ids_clientes = [cliente["id"] for cliente in clientes_tratados]
        ids_produtos = [produto["produto_id"] for produto in produtos_tratados]
        
        res_pedidos = transformar_pedidos(dados_brutos["pedidos"], ids_clientes, ids_produtos)
        contadores_pedidos = res_pedidos["contadores"]
        
        print(
            f"transformacao: pedidos_unicos={contadores_pedidos["pedidos_unicos"]} repetidos_descartados={contadores_pedidos["repetidos_descartados"]}"
        )
        print(
            f"transformacao: emails_nulos={contadores_clientes["emails_nulos"]} estados_padronizados={contadores_clientes["estados_padronizados"]} datas_convertidas={contadores_pedidos["datas_convertidas"]} "
            f"\n\tvalores_convertidos={contadores_pedidos["valores_convertidos"]}"
        )
        
        return {"clientes": clientes_tratados, "produtos": produtos_tratados, "pedidos": res_pedidos["pedidos"], "itens": res_pedidos["itens"]}
    except ValorInvalidoError as erro:
        print(f"Erro de validação na transformação: {erro}")
        return None