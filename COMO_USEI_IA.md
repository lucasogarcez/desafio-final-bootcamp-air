# Como utilizei IA durante o desafio

## Sugestões aceitas

### Parte 2 (A3): `converter_data`

- Trecho pedido: função `converter_data(valor)` que recebe o texto da data do pedido e retorna um objeto `date`, aceitando `AAAA-MM-DD` e `DD/MM/AAAA`. Passei o que planejei (nome, o que recebe e o que devolve), dois exemplos reais dos dados brutos coletados, restrição de utilizar só a biblioteca padrão e a regra de erro (`ValueError`).
- Justificativa: o formato é decidido pelo separador, sem análise por regex. Usa só `datetime`, da biblioteca padrão. O erro é indicado e a mensagem final com tabela, id, campo e valor é montada pela função `transformar_pedidos`, como definido no contrato.
- Como validei: escrevi os testes antes de executar a função (dois formatos, espaços, data inexistente, sem separador, vazio e None). Também troquei dia por mês (`%d/%m` por `%m/%d` e o teste falhou, como esperado). No fim, todos passaram.

### Parte 4 (A1): testes para `tratar_email`

- Trecho pedido: suíte de testes para a função `tratar_email(valor)`. Passei a implementação da função, a regra de transformação da armadilha A1 (e-mail ausente vira `None`, caso contrário devolve o texto sem espaços nas extremidades) e a regra de erro (`TypeError` quando o valor não é `str` ou `None`).
- Justificativa: a sugestão foi aceita parcialmente, com cortes e ajustes. A IA gerou testes cobrindo espaços simples e caracteres invisíveis (`\t`, `\n`, Unicode), retorno de `None` para vazios, preservação de maiúsculas/minúsculas e idempotência. Mantive os testes de espaços nas extremidades, textos vazios e idempotência, pois estão alinhados diretamente ao contrato de dados e aos tipos possíveis vindos do JSON por observabilidade. Removi casos de bytes, tuplas e dicionários, pois o contrato de origem não gera bytes nem estruturas que sejam aninhadas nesse campo, tornando esses casos redundantes para o escopo de A1.
- Como validei: executei a suíte de testes e realizei "mutações manuais" na função `tratar_email(valor)` para confirmar que os testes detectavam falhas reais dos dados (removi o `.strip()`, troquei por `.lstrip()`, fiz retornar `""` ao invés de `None` e troquei `TypeError` por `ValueError`). Todos os testes falharam nas "mutações" e voltaram a passar após voltar ao código original.

### Parte 4 (reconciliação): testes em `test_reconciliacao.py`

- Trecho pedido: `fixture` de carga no banco e teste `test_reconciliacao_pedidos_origem_e_destino(banco_carregado)` reutilizando a função `reconciliar_pedidos(conexao, pedidos_tratados)` de `etl/reconciliacao.py`. Passei o código de `etl/carga.py`, o fluxo de `transformacao.py` e as regras de comparação (contagem de pedidos únicos com igualdade exata e tolerância de um centavo) para a soma de `valor_itens`.
- Justificativa: a sugestão foi aceita com ajustes, depois de descartar as sugestões iniciais. Nas primeiras vezes, a IA propôs testar com SQLite e, em seguida, com `CREATE TABLE` manual e `DATABASE_URL` via `os.gentv`, o que foi rejeitado por não seguir o caminho escolhido (PostgreSQL) e nem a configuração já existente com `python-decouple`. Nas próximas vezes, passei o contrato de dados e o `schema.sql` para maior contexto da IA. Na versão final, utilizei a `fixture` (`banco_carregado`) reaproveitando `conectar()`, `limpar_tabelas()` e as funções de carga (`carregar_...`) encerrando com rollback no `finally` para não poluir o banco original. Mantive também os casos críticos de teste dos dados (pedido repetido, item decimal e pedido divergente).
- Como validei: executei o `test_reconciliacao.py`, comparando com o banco local, e verifiquei a aprovação dos testes. Para confirmar, simulei falhas (inserindo diferença maior que um centavo e omitindo um pedido na carga dos dados) para ter certeza de que o teste falhava na divergência, e consultei as tabelas depois da execução para comprovar que o rollback manteve intactos os dados carregados pelo `main.py`.

### Parte 5: texto da descrição do Pull Request
- Trecho pedido: estrutura de título e descrição do Pull Request, de acordo com o que o desafio pede (o que foi feito, como foi validado, onde está o registro de IA). A IA propôs um modelo com: resumo, partes do trabalho, decisões, evidências em texto, uso de IA, como rodar e limitações, com espaços para preencher com números.
- Justificativa: o desafio exige que o Pull Request seja revisável sem reexecutar tudo, e o modelo organiza as evidências.
- Como validei: conferi cada número e afirmação, comparando com as saídas do ETL, do pytest e das consultas.

## Sugestões rejeitadas

### Parte 4 (A1): testes para `tratar_email`

- Trecho rejeitado: casos de teste para tipos bytes, tuplas, dicionários e caracteres Unicode em `test_tratar_email_strings_validas_remove_apenas_espacos_extremidades` e `test_tratar_email_ausente_ou_vazio_retorna_none`.
- Justificativa: por observabilidade, o contrato de dados define que a extração dos dados vem de arquivos JSON (API), onde os tipos possíveis para o campo `email` são `str` ou `None`. Os demais tipos, como dos casos de testes rejeitados, não existem nos dados extraídos.

### Parte 4 (reconciliação): testes em `test_reconciliacao.py`

- Trecho rejeitado: uso do banco SQLite (`carregar_em_sqlite_memoria`) e outra sugestão de conexão via `DATABASE_URL` com `CREATE TABLE` embutido no teste.
- Justificativa: o projeto utiliza PostgreSQL como banco de dados (caminho escolhido) com tipos `NUMERIC(12,2)` (que retornam `decimal.Decimal` no `psycopg2`, o que é diferente no SQLite) e lida com variáveis de ambiente com `python-decouple` em `etl/carga.py`. Duplicar a criação de tabelas e a conexão no teste iria quebrar o contrato de origem do desafio.

## Falhas e retrabalho

### Parte 3: contar registros com f-string

- Trecho pedido: função `contar_registros(conexao)` que contabiliza os dados carregados no banco. Passei as funções de conexão ao banco, limpeza de tabelas e carregamento dos dados de `etl/carga.py`.
- Justificativa: a IA sugeriu percorrer uma lista com os nomes das tabelas e montar a consulta de forma dinâmica utilizando `f-string` (`f"SELECT COUNT(*) FROM {tabela};"`). A interpolação de textos em consultas SQL com `f-string` foge das boas práticas de segurança, pois representa risco de `SQL Injection` caso o parâmetro ali passado deixe de ser estático. No `psycopg2`, esses identificadores exigem uma verificação com `psycopg.sql.Identifier`. Além disso, executar uma query dessa forma separada, dentro de um laço, gera quatro requisições e respostas desnecessárias para as tabelas do banco.
- Como foi corrigido: descartei o laço com `f-string` e reescrevi a função `contar_registros(conexao)` com uma única consulta SQL estática, utilizando de subconsultas (`SELECT (SELECT COUNT(*) FROM clientes), (SELECT COUNT(*) FROM produtos), ...`), trazendo todas as contagens de uma única vez, em uma única chamada ao banco, sem interpolação de textos.