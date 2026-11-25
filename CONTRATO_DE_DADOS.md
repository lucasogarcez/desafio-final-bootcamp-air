# Contrato de dados

## Tabela: `clientes`
| Campo | Tipo no banco | Aceita nulo? | Chave ou restrição | Origem | Regra de transformação | Armadilha e contador |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | não | primária | API, clientes | - | - |
| `nome` | `TEXT` | não | - | API, clientes | - | - |
| `email` | `TEXT` | sim | - | API, clientes | manter cliente e gravar o e-mail, mesmo se nulo | A1, `emails_nulos` |
| `cidade` | `TEXT` | não | - | API, clientes | - | - |
| `estado` | `CHAR(2)` | não |  - | API, clientes | remover espaços e se letras em minúsculo, converter para maiúsculas. Se depois disso tiver menos ou mais que 2 letras, é valor inválido | A2, `estados_padronizados` |
| `cadastro_em` | `DATE` | não | - | API, clientes | - | - |

## Tabela: `produtos`
| Campo | Tipo no banco | Aceita nulo? | Chave ou restrição | Origem | Regra de transformação | Armadilha e contador |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `produto_id` | `INTEGER` | não | primária | CSV, produtos | converter valor vindo do .csv para `int`, armazenando no banco como `INTEGER` | - |
| `nome` | `TEXT` | não | - | CSV, produtos | - | - |
| `categoria` | `TEXT` | não | - | CSV, produtos | - | - |
| `preco_base` | `NUMERIC(10,2)` | não | - | CSV, produtos | converter valor vindo do .csv para `float` e utilizar `round(...,2)`, armazenando no banco como `NUMERIC`. Utiliza a mesma função que `valor_total`, sem contabilizar no contador de `valores_convertidos` | - |

## Tabela: `pedidos`
| Campo | Tipo no banco | Aceita nulo? | Chave ou restrição | Origem | Regra de transformação | Armadilha e contador |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | não | primária | API, pedidos | verificar se já existe (`id` e demais campos), caso sim manter a primeira correspondência do `id` e descartar duplicata | A5, `repetidos_descartados` |
| `cliente_id` | `INTEGER` | não | estrangeira (clientes.id) | API, pedidos | se não tiver cliente correspondente, é valor inválido | - |
| `data_pedido` | `DATE` | não | - | API, pedidos | identificar formato e, se em formato `DD/MM/AAAA`, converter para `AAAA-MM-DD`. Se em nenhum desses formatos ou se não for possível conversão, o valor é inválido | A3, `datas_convertidas` |
| `status` | `TEXT` | não | - | API, pedidos | valores definidos (entregue, cancelado, em_transporte) | - |
| `valor_total` | `NUMERIC(12,2)` | não |  - | API, pedidos | converter para tipo `float` e arredondar com `round(..., 2)` | A4, `valores_convertidos` |
| `valor_itens` | `NUMERIC(12,2)` | não | - | calculado | soma de quantidade vezes `preco_unitario` dos itens do pedido, arredondada a 2 casas | A6 |
| `divergente` | `BOOLEAN` | não | valor padrão: `FALSE` | calculado | soma da quantidade (tabela `itens_pedido`, campo `quantidade`) vezes o preço dos itens (tabela `itens_pedido`, campo `preco_unitario`) e marca como divergente (tabela `pedidos`, campo `divergente`) se, arredondada em 2 casas, a diferença absoluta (`|valor_total - valor_itens|`) for estritamente maior que um centavo. | A6, `divergentes` |

## Tabela: `itens_pedido`
| Campo | Tipo no banco | Aceita nulo? | Chave ou restrição | Origem | Regra de transformação | Armadilha e contador |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pedido_id` | `INTEGER` | não | composta, estrangeira (pedidos.id) | pedidos.id (pedido pai) | remoção de pedidos duplicados acontece antes de extrair itens do pedido | A5 |
| `linha` | `INTEGER` | não | composta | calculado | gerar de 1 a n dentro de cada pedido | - |
| `produto_id` | `INTEGER` | não | estrangeira (produtos.produto_id) | API, pedidos["itens"] | se não tiver produto correspondente, é valor inválido | - |
| `quantidade` | `INTEGER` | não | - | API, pedidos["itens"] | - | - |
| `preco_unitario` | `NUMERIC(10,2)` | não |  - | API, pedidos["itens"] | - | - |

## Armadilhas
### A1
- Campos em que aparece (tabela, campo): clientes, `email`;
- Regra de transformação: salvar campo, independentemente se nulo.

### A2
- Campos em que aparece (tabela, campo): clientes, `estado`;
- Regra de transformação: remover espaços e, se em letras minúsculas, converter para maiúsculas. Se depois disso tiver menos ou mais que 2 letras, é valor inválido.

### A3
- Campos em que aparece (tabela, campo): pedidos, `data_pedido`;
- Regra de transformação: identificar formato e, se em formato `DD/MM/AAAA`, converter para `AAAA-MM-DD`. Se em nenhum desses formatos ou se não for possível conversão, o valor é inválido.

### A4
- Campos em que aparece (tabela, campo): pedidos, `valor_total`;
- Regra de transformação: converter para tipo `float` e arredondar com `round(..., 2)`.

### A5
- Campos em que aparece (tabela, campo): pedidos, `id`; itens_pedido, `pedido_id`.
- Regra de transformação: verificar se já existe (`id`), caso sim manter a primeira correspondência do `id` e descartar duplicata.

### A6
- Campos em que aparece (tabela, campo): pedidos, `valor_itens`; pedidos, `divergente`;
- Regra de transformação: soma da quantidade (tabela `itens_pedido`, campo `quantidade`) vezes o preço dos itens (tabela `itens_pedido`, campo `preco_unitario`) e marca como divergente (tabela `pedidos`, campo `divergente`) se a diferença absoluta (`valor_total - valor_itens`) for estritamente maior que um centavo.

## Decisões
### Converter texto em número:
Utilização do tipo `float` com `round(...,2)` pois o banco guarda em `NUMERIC`. O arredondamento e a tolerância de um centavo controlam o erro das somas.

### Valores inválidos:
São determinados valores inválidos casos de: campo `estado` fora de 2 letras, data fora dos dois formatos (`DD/MM/AAAA` ou `AAAA-MM-DD`), `cliente_id` ou `produto_id` inexistente, valor não convertível e formatações das funções auxiliares (`tratar_email`, `padronizar_estado`, `converter_data`, `converter_valor`, `remove_pedidos_repetidos`, `calcular_itens_pedido`, `converter_produto_id`, `validar_cliente_id`, `validar_produto_id`). Sendo assim, é obrigatória a interrupção da execução no primeiro erro com lançamento de mensagem de erro, com formato: tabela, id, campo, valor. Para a tabela `itens_pedido`, que não tem campo `id`, substitui-se na mensagem por: `pedido_id` e `linha`.

### Ordem de transformação:
1. Na tabela `pedidos`, remover duplicatas.
2. Validar `cliente_id` de pedidos.
3. Extrair itens dos pedidos únicos, validar `produto_id` e gerar `linha`, na ordem que vem no JSON.
4. Converter data e valor nos campos necessários.
5. Calcular `valor_itens` da tabela `pedidos`.
6. Comparar (`valor_total - valor_itens`) para marcar divergência.

## Dicionário de contadores
| Nome | O que conta? | Quando é contado? |
| --- | --- | --- |
| `clientes paginas` | páginas lidas da rota "/clientes" da API | a cada página lida |
| `registros` | linhas lidas da rota "/clientes" da API | a cada linha lida |
| `pedidos paginas` | páginas lidas da rota "/pedidos" da API | a cada página lida |
| `registros_brutos` | linhas lidas da rota "/pedidos" da API | a cada linha lida |
| `pedidos_unicos` | quantidade de pedidos não duplicados | durante verificação para remoção de ids duplicados |
| `repetidos_descartados` | quantidade de pedidos duplicados | durante verificação para remoção de ids duplicados |
| `emails_nulos` | quantidade de emails com valor nulo | durante verificação de valores lidos do campo |
| `estados_padronizados` | quantidade de estados convertidos para maiúsculas | durante a verificação de valores lidos do campo  |
| `datas_convertidas` | quantidade de datas convertidas para formato `AAAA-MM-DD` | durante a verificação de valores lidos do campo |
| `valores_convertidos` | quantidade de valores convertidos de texto para numérico, em `valor_total` | durante a verificação de valores lidos do campo |
| `itens` | quantidade de itens encontrados em todos os pedidos lidos | durante a carga de dados no banco |
| `soma_valor_itens_origem` | total da soma do valor dos itens de pedidos, com dados brutos | verificação de reconciliação dos dados |
| `soma_valor_itens_destino` | total da soma do valor dos itens de pedidos, com dados enviados ao banco | verificação de reconciliação dos dados |
| `diferenca` | diferença absoluta entre `soma_valor_itens_origem` e `soma_valor_itens_destino`, ambos arredondados em 2 casas decimais, com o resultado final também arredondado em 2 casas decimais  | verificação de reconciliação dos dados |
| `divergentes` | diferença absoluta entre `valor_total` e `valor_itens`, ambos arredondados em 2 casas decimais, com o resultado final também arredondado em 2 casas decimais. Considera-se divergente quanto o resultado é maior que 0,01 | marcação de divergência |

## Fora do escopo
| Caso | Por que está fora | O que o ETL faz se aparecer | Como confirmei |
| --- | --- | --- | --- |
| Valores negativos | nenhuma armadilha prevê, e o esquema não tem `CHECK` | carrega como veio | Em `brutos/pedidos.json` (seed 2026, 5100 registros brutos), contei os pedidos com `valor_total` menor que zero, depois de converter com `converter_valor`: 1 ocorrência. Teste `test_valor_total_negativo_carrega_sem_erro` prova que o ETL carrega como veio |
| Pedido sem itens | nenhuma armadilha prevê, evita interrupção por único registro e em ciclo de vida do pedido este poderia ser registrado com status `cancelado` | carrega pedidos com lista de itens vazia (calculando `valor_itens = 0.0`) e interrompe a execução com `KeyError` caso a cahve `itens`esteja ausente | Em `brutos/pedidos.json`, contei pedidos com `itens` vazio ou ausente: 0 ocorrências. Testes `test_pedido_com_itens_vazio_carrega_com_valor_itens_zero` e `test_pedido_com_chave_itens_ausente_levanta_key_error` provam os comportamentos declarados. |