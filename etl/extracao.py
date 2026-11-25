# Extração dos dados da API

import csv, decouple, json, os, requests

class ErroExtracao(Exception):
    pass

def extrair_rota_paginada(sessao: requests.Session, url_base: str, rota: str, page_size: int = 200) -> tuple[list[dict], int]:
    url_rota = f"{url_base}/{rota}"
    dados: list[dict] = []
    pagina = 1
    total_paginas = 1

    while pagina <= total_paginas:
        try:
            resposta = sessao.get(
                url=url_rota,
                params={"page": pagina, "page_size": page_size},
                timeout=10,
            )

            resposta.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ErroExtracao(f"Erro de conexão em '/{rota}'. Verifique se 'api_verdejar.py' está em execução")
        except requests.exceptions.Timeout:
            raise ErroExtracao(f"Erro: timeout ao acessar rota '/{rota}' na página {pagina}")
        except requests.exceptions.HTTPError as erro_http:
            codigo_status = erro_http.response.status_code
            
            if codigo_status == 404:
                raise ErroExtracao(f"Erro HTTP ({codigo_status}) ao acessar rota inexistente '/{rota}'")
            
            raise ErroExtracao(f"Erro HTTP ({codigo_status}) ao acessar '/{rota}' na página {pagina}")

        corpo = resposta.json()
        
        if pagina == 1:
            total_paginas = corpo["total_pages"]
            if total_paginas == 0:
                return [], 0
            
        if not corpo["items"]:
            raise ErroExtracao(f"Resposta inesperada em '/{rota}' na página {pagina}: lista 'items' veio vazia")
            
        dados.extend(corpo["items"])
        pagina += 1

    return dados, total_paginas

def extrair_clientes(sessao: requests.Session, url_base: str, page_size: int = 200) -> tuple[list[dict], int]:
    return extrair_rota_paginada(sessao, url_base, "clientes", page_size)

def extrair_pedidos(sessao: requests.Session, url_base: str, page_size: int = 200) -> tuple[list[dict], int]:
    return extrair_rota_paginada(sessao, url_base, "pedidos", page_size)

def ler_produtos_csv(caminho_arquivo: str) -> list[dict]:
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            
            return list(leitor)
    except OSError as erro_leitura:
        raise ErroExtracao(f"Erro ao ler arquivo CSV '{caminho_arquivo}': {erro_leitura}")

def salvar_dados_brutos(dados: list[dict], caminho_arquivo: str) -> None:
    try:
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        
        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)
    except OSError as erro_disco:
        raise ErroExtracao(f"Erro ao salvar arquivo {caminho_arquivo}: {erro_disco}")

def executar_extracao() -> dict[str, list[dict]] | None:
    url_base = decouple.config("API_URL", default="http://127.0.0.1:8000")
    caminho_csv = decouple.config("PRODUTOS_CSV", default="insumos/dados/produtos.csv")
    pasta_destino = "brutos"
    
    try:
        with requests.Session() as sessao:
                
            resp_saude = sessao.get(f"{url_base}/saude", timeout=5)
            resp_saude.raise_for_status()
           
            clientes, pag_clientes = extrair_clientes(sessao, url_base)
            pedidos, pag_pedidos = extrair_pedidos(sessao, url_base)
            produtos = ler_produtos_csv(caminho_csv)
            
            salvar_dados_brutos(clientes, f"{pasta_destino}/clientes.json")
            salvar_dados_brutos(pedidos, f"{pasta_destino}/pedidos.json")
            salvar_dados_brutos(produtos, f"{pasta_destino}/produtos.json")
            
            print(f"extracao: clientes paginas={pag_clientes} registros={len(clientes)}")
            print(f"extracao: pedidos paginas={pag_pedidos} registros_brutos={len(pedidos)}")
            
        return {"clientes": clientes, "produtos": produtos, "pedidos": pedidos}
    except requests.exceptions.ConnectionError:
        print("Erro: não foi possível se conectar à API. Verifique se 'api_verdejar.py' está em execução")
    except requests.exceptions.Timeout:
        print("Erro: A API demorou demais para responder no teste de saúde ('/saude')")
    except requests.exceptions.HTTPError as erro_http:
        codigo_status = erro_http.response.status_code
        print(f"Erro HTTP ({codigo_status}) ao verificar '/saude'")
    except ErroExtracao as erro:
        print(erro)
        
if __name__ == "__main__":
    executar_extracao()