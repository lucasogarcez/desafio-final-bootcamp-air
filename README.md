# Desafio Final AI/R (ETL)

O repositório se trata da resolução de um desafio de ETL, implementando todo o pipeline e suas respectivas validações, desenvolvido pela empresa AI/R (AI Revolution Group / AI Revolution Company), proposto durante o Bootcamp AI/R AI-Driven Data Engineering 2026.
> Todos os dados são sintéticos (gerados por programa, com seed fixa) e a empresa não existe. Nenhuma
> informação real de pessoas está envolvida.

## Contexto
A Verdejar é uma loja virtual fictícia de hortifrúti. Ela guarda clientes e pedidos em um sistema antigo,
acessível por uma API, e o catálogo de produtos em uma planilha CSV. A empresa quer esses dados em
um banco PostgreSQL, limpos e conferidos, para começar a analisar vendas por mês, por estado e por
categoria de produto.
Seu papel é o de engenheiro ou engenheira de dados em início de carreira: construir o ETL que leva os
dados da API e do CSV para o banco, provar que a carga está correta e explicar as decisões, inclusive as
que tomou com a ajuda da IA.

### Insumos fornecidos
- **gerar_dados.py**: gera os dados com a seed 2026 (os dados já vêm gerados na pasta dados/).
- **api_verdejar.py**: sobe a API local em http://127.0.0.1:8000 com as rotas /clientes e /pedidos,
paginadas por page e page_size, e /saude.
- **dados/produtos.csv**: catálogo com produto_id, nome, categoria e preco_base.
- **schema.sql**: esquema de destino no PostgreSQL com as tabelas clientes, produtos, pedidos e
itens_pedido.
- **README_insumos.md**: instruções de uso dos insumos.

### Armadilhas declaradas nos dados
Os dados contêm, de propósito, seis problemas de qualidade. Eles estão declarados aqui para tratamento de forma 
consiente. O ETL aqui presentelida com todos.
| Código | Problema | O que se espera do ETL |
|:--- | --- | --- |
| A1 | Parte dos clientes tem e-mail ausente (valor nulo) | Manter o cliente, gravar o e-mail como nulo e contar quantos são.|
| A2 | A sigla do estado aparece ora em maiúsculas (RS), ora em minúsculas (rs). | Padronizar para maiúsculas antes da carga. |
| A3 | A data do pedido vem em dois formatos: AAAAMM-DD e DD/MM/AAAA. | Converter os dois formatos para o tipo de data do banco (`DATE` no PostgreSQL) |
| A4 | O valor total do pedido vem ora como número, ora como texto com vírgula decimal (por exemplo, 125,84). | Carregar cada pedido uma única vez; rodar o ETL de novo não pode duplicar. |
| A5 | Alguns pedidos aparecem repetidos (mesmo id e mesmo conteúdo) em páginas diferentes da API. | Carregar cada pedido uma única vez; rodar o ETL de novo não pode duplicar. |
| A6 | Em parte dos pedidos, o valor total informado não bate com a soma dos itens. | Gravar os dois valores (valor_total e valor_itens), marcar a divergência na coluna divergente e relatar a quantidade. |

## Como funciona
- Extração: vem de arquivo API local [api_verdejar.py](insumos/api_verdejar.py).
- Transformação: limpeza e padronização dos dados de `clientes.json`, `pedidos.json` e `produtos.csv` e cálculo de contadores, vide contrato de dados ([CONTRATO_DE_DADOS.md](CONTRATO_DE_DADOS.md)).
- Carga: tabelas `clientes`, `produtos`, `pedidos`, `itens_pedido` em banco PostgreSQL.
(Um diagrama simples em texto ou imagem ajuda.)

## Como executar o projeto localmente
### 1. Pré-Requisitos: 
Certifique-se de que tenha instalado Python 3.12 e PostgreSQL na sua máquina.
### 2. Clonando o Reposiório:
```bash
git clone https://github.com/lucasogarcez/desafio-final-bootcamp-air
cd desafio-final-bootcamp-air
```
### 3. Configurando o Ambiente Virtual
```bash
python -m venv venv
source venv/bin/activate # No Windows: venv\Scripts\activate

pip install -r requirements.txt
```
### 4. Variáveis de Ambiente
Crie um arquivo de nome `.env` na raiz do seu projeto e configure as credenciais do seu banco de dados local:
```bash
# Banco de dados
DB_NAME=nome_do_banco
DB_USER=usuario_postgres
DB_PASSWORD=senha_postgres
DB_HOST=localhost
DB_PORT=5432

# API
API_URL="http://127.0.0.1:8000"

# Dados CSV
PRODUTOS_CSV="insumos/dados/produtos.csv"
```
Caso queria um exemplo, acesse o arquivo [.env.example](.env.example).
### 5. Preparando o Banco de Dados
No terminal da sua IDE, execute:
> Se não quiser o nome do seu banco de dados como `verdejar`, substitua no comando abaixo.
```bash
# Cria o banco de dados local
psql -U postgres -c "CREATE DATABASE verdejar;"

# Cria as tabelas no seu banco de dados local
psql -U postgres -d verdejar -f schema.sql
```
### 6. Executando ETL completo
```bash
python -m etl.main
```

## Testes

### Teste de idempotência (estratégia: recarga completa)
Texto de saída do terminal ao realizar duas execuções seguidas, com as mesmas contagens:
```text
(venv) PS C:\Users\lucas\...\desafio-final-bootcamp-air> Get-Date; python -m etl.main; Get-Date; python -m etl.main; Get-Date

Monday, November 23, 2026 6:35:18 PM
extracao: clientes paginas=5 registros=1000
extracao: pedidos paginas=26 registros_brutos=5100
transformacao: pedidos_unicos=5000 repetidos_descartados=100
transformacao: emails_nulos=81 estados_padronizados=151 datas_convertidas=1037 
        valores_convertidos=1255
carga: clientes=1000 produtos=12 pedidos=5000 itens=12455
Extração e transformação concluídos!
Monday, November 23, 2026 6:35:22 PM
extracao: clientes paginas=5 registros=1000
extracao: pedidos paginas=26 registros_brutos=5100
transformacao: pedidos_unicos=5000 repetidos_descartados=100
transformacao: emails_nulos=81 estados_padronizados=151 datas_convertidas=1037 
        valores_convertidos=1255
carga: clientes=1000 produtos=12 pedidos=5000 itens=12455
Extração e transformação concluídos!
Monday, November 23, 2026 6:35:26 PM
```
> Parte do caminho absoluto do diretório foi anonimizado para fins de segurança e privacidade.

## Decisões e trade-offs
Por que exceções customizadas?
- Em vez de capturar um `Exception` genérico (o que ocultaria bugs de desenvolvimento, como `TypeError`), o pipeline define exceções específicas (`ValorInvalidoError`, `ErroCarga`). Isso permite carregar dados estruturados do registro inválido (tabela, ID, campo e linha) e centraliza o encerramento controlado (`sys.exit(1)`) em um único ponto, desviando o orquestrador (`main.py`) de exceções de bibliotecas externas (`requests`, `psycopg2`).
Por que recarga completa como estratégia de idempotência?
- Garante idempotência total, produzindo sempre o mesmo resultado no banco e permite também correção de itens removidos ou alterados sem lógica complexa de `UPDATE`/`DELETE`. Em contrapartida, apaga todo o histório do banco a cada execução para reescrevê-lo por completo o que, em produção com alto volume de dados seria um problema, porém, a API local utilizada nesse projeto possui pequeno volume de dados, o que torna o tempo de reescrita do histório irrelevante.

## Autor
### Lucas Oliveira Garcez