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

### Caminho escolhido
- Banco de dados: PostgreSQL
- Biblioteca de conexão: `psycopg2`

## Como funciona
- Extração: vem de arquivo API local [api_verdejar.py](insumos/api_verdejar.py).
- Transformação: limpeza e padronização dos dados de `clientes.json`, `pedidos.json` e `produtos.csv` e cálculo de contadores, vide contrato de dados ([CONTRATO_DE_DADOS.md](CONTRATO_DE_DADOS.md)).
- Carga: tabelas `clientes`, `produtos`, `pedidos`, `itens_pedido` em banco PostgreSQL.

## Estrutura do projeto
```texto
desafio-final/
 README.md
 COMO_USEI_IA.md
 CONTRATO_DE_DADOS.md
 consultas_validacao.sql
 insumos/ (gerar_dados.py, api_verdejar.py, schema.sql, dados/)
 etl/ (extracao.py, transformacao.py, carga.py, reconciliacao.py, main.py)
 tests/ (test_transformacao.py, test_reconciliacao.py)
 .env.example
 requirements.txt
 .gitignore
```
> O arquivo `reconciliacao.py` não constava na estrutura original, porém, foi adicionado com por motivos de responsabilidade, visto que se trata de uma auditoria e iria se misturar com outras responsabilidades se integrado em outro arquivo (como `carga.py`, por exemplo), organização clara na orquestação (`main.py`) como uma outra etapa e diferenças de exceção (exceções separadas levaram a melhores diagnósticos).

## Como executar o projeto localmente
### 1. Pré-Requisitos: 
Certifique-se de que tenha instalado Python 3.12 e PostgreSQL na sua máquina.
### 2. Clonando o Reposiório:
```bash
git clone -b desafio-final-lucas https://github.com/lucasogarcez/desafio-final-bootcamp-air
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
# Em outro terminal, execute a API
python insumos/api_verdejar.py --porta 8000 --dados insumos/dados

# Execute o ETL no terminal inicial
python -m etl.main
```

## Testes

### Como executar
```bash
python -m pytest
```

### Resultado esperado
```bash
===================================================================================== 72 passed in 0.23s ======================================================================================
```

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

## Resultados das Consultas de Validação (`consultas_validacao.sql`)
### 1. Total de vendas por mês (`valor_itens`) e teste de consulta
```text
    mes     | total_vendas                                                                                                                                                                     
------------+--------------
 2026-01-01 |     30355.02
 2026-02-01 |     33855.86
 2026-03-01 |     30617.70
 2026-04-01 |     31170.96
 2026-05-01 |     30777.02
 2026-06-01 |     31557.73
 2026-07-01 |     32685.17
 2026-08-01 |     29260.04
 2026-09-01 |     29909.71
 2026-10-01 |     31039.54
```

- Soma geral dos meses: 311228.75
- Total geral da tabela (`SELECT COALESCE(SUM(valor_itens), 0) FROM pedidos`): 311228.75
- Diferença: 0.00

### 2. Quantidade de pedidos por estado
```text
estado | quantidade_pedidos                                                                                                                                                                   
--------+--------------------
 RS     |               1543
 SC     |               1127
 PR     |                974
 SP     |                880
 MG     |                476
```

### 3. Pedidos divergentes
- Total de registros retornados: 238 pedidos
- Amostra das primeiras linhas retornadas pela consulta:
```text
id  | valor_total | valor_itens | diferenca                                                                                                                                                  
------+-------------+-------------+-----------
    1 |      125.84 |      130.84 |      5.00
   51 |       26.58 |       23.58 |      3.00
   71 |      144.35 |      134.35 |     10.00
   81 |       -1.84 |        3.16 |      5.00
  106 |       47.78 |       44.78 |      3.00
  176 |      137.69 |      134.69 |      3.00
  186 |      143.51 |      133.51 |     10.00
  289 |       79.40 |       76.40 |      3.00
```

## Decisões e trade-offs
Por que tipo `float`, com arredondamento por `round(..., 2)`, para números decimais?
- O banco guarda em `NUMERIC`, por isso, o arredondamento e a tolerância de um centavo controlam o erro das somas.
Por que exceções customizadas?
- Em vez de capturar um `Exception` genérico (o que ocultaria bugs de desenvolvimento, como `TypeError`), o pipeline define exceções específicas (`ValorInvalidoError`, `ErroCarga`). Isso permite carregar dados estruturados do registro inválido (tabela, ID, campo e linha) e centraliza o encerramento controlado (`sys.exit(1)`) em um único ponto, desviando o orquestrador (`main.py`) de exceções de bibliotecas externas (`requests`, `psycopg2`).
Por que recarga completa como estratégia de idempotência?
- Garante idempotência total, produzindo sempre o mesmo resultado no banco e permite também correção de itens removidos ou alterados sem lógica complexa de `UPDATE`/`DELETE`. Em contrapartida, apaga todo o histório do banco a cada execução para reescrevê-lo por completo o que, em produção com alto volume de dados seria um problema, porém, a API local utilizada nesse projeto possui pequeno volume de dados, o que torna o tempo de reescrita do histório irrelevante.
Por que o contador `divergentes` aparece junto aos de transformação e foi adicionado durante o desenvolvimento da reconciliação?
- O contador já era implementado na etapa de transformação (`transformar_pedidos`), porém, sua exibição foi concretizada na etapa de reconciliação para respeitar a ordem do exemplo de saída especificado no desafio e agrupar os dois indicadores de auditoria (`reconciliacao` e `divergentes`), considerando que não é necessário recalcular o valor no banco.
Porque utilizar, em `consultas_validacao.sql`, campo `valor_itens` como valor total de vendas ao invés de `valor_total`?
- O `valor_itens` é calculado durante a transformação utilizando `quantidade` e `preco_unitario` (já tratados), o que garante maior segurança e confiabilidade aos dados retornados pelas consultas. Em contrapartida, utilizar `valor_total` seria depender de um campo talvez ainda não tratado, podendo conter valores negativos ou strings.

### Fora do escopo
| Caso | Por que está fora | O que o ETL faz se aparecer | Como confirmei |
| --- | --- | --- | --- |
| Valores negativos | nenhuma armadilha prevê, e o esquema não tem `CHECK` | carrega como veio | Em `brutos/pedidos.json` (seed 2026, 5100 registros brutos), contei os pedidos com `valor_total` menor que zero, depois de converter com `converter_valor`: 1 ocorrência. Teste `test_valor_total_negativo_carrega_sem_erro` prova que o ETL carrega como veio |
| Pedido sem itens | nenhuma armadilha prevê, evita interrupção por único registro e em ciclo de vida do pedido este poderia ser registrado com status `cancelado` | carrega pedidos com lista de itens vazia (calculando `valor_itens = 0.0`) e interrompe a execução com `KeyError` caso a cahve `itens`esteja ausente | Em `brutos/pedidos.json`, contei pedidos com `itens` vazio ou ausente: 0 ocorrências. Testes `test_pedido_com_itens_vazio_carrega_com_valor_itens_zero` e `test_pedido_com_chave_itens_ausente_levanta_key_error` provam os comportamentos declarados. |

## Autor
### Lucas Oliveira Garcez