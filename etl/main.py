from extracao import executar_extracao
from transformacao import executar_transformacao

def main() -> None:
    dados_brutos = executar_extracao()
    if dados_brutos is None:
        return
    
    tratados = executar_transformacao(dados_brutos)
    if tratados is None:
        return
    
    print("Extração e transformação concluídos!")

if __name__ == "__main__":
    main()