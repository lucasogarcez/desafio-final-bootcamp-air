-- Total de vendas por mês (utilizando valor_itens)
SELECT
    DATE_TRUNC('month', data_pedido)::date as mes,
    COALESCE(SUM(valor_itens), 0) as total_vendas
FROM pedidos
GROUP BY DATE_TRUNC('month', data_pedido)
ORDER BY mes;

-- Consulta teste: soma geral da tabela
SELECT
    COALESCE(SUM(valor_itens), 0) as total_geral
FROM pedidos;

-- Quantidade de pedidos por estado
SELECT
    c.estado,
    COUNT(p.id) as quantidade_pedidos
FROM clientes c
INNER JOIN pedidos p ON p.cliente_id = c.id
GROUP BY c.estado
ORDER BY quantidade_pedidos DESC, c.estado ASC;

-- Pedidos divergentes
SELECT
    id, valor_total, valor_itens,
    ABS(valor_total - valor_itens) as diferenca
FROM pedidos
WHERE divergente IS TRUE
ORDER BY id;