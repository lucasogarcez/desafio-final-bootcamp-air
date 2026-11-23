import sys
from etl.carga import executar_carga
from etl.extracao import executar_extracao
from etl.transformacao import executar_transformacao

def main() -> None:
    try:
        
        dados_brutos = executar_extracao()
        if dados_brutos is None:
            sys.exit(1)
        
        dados_tratados = executar_transformacao(dados_brutos)
        if dados_tratados is None:
            sys.exit(1)
        
        carga = executar_carga(dados_tratados)
        if carga is None:
            sys.exit(1)
    
        print("Extração e transformação concluídos!")
    except Exception as erro:
        print(f"Erro no pipeline: {erro}")
        sys.exit(1)

if __name__ == "__main__":
    main()