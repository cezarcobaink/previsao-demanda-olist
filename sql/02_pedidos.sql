-- Um registro por pedido, com prazos, valores e avaliação
CREATE TABLE pedidos AS
WITH itens AS (
    SELECT order_id, SUM(price) AS valor_itens, SUM(freight_value) AS valor_frete, COUNT(*) AS n_itens
    FROM order_items GROUP BY order_id
), notas AS (
    SELECT order_id, MAX(review_score) AS nota FROM order_reviews GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_state AS uf_cliente,
    DATE(o.order_purchase_timestamp) AS data_compra,
    o.order_status,
    julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS dias_entrega,
    julianday(o.order_estimated_delivery_date) - julianday(o.order_purchase_timestamp) AS dias_prometidos,
    julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS dias_atraso,
    n.nota, i.valor_itens, i.valor_frete, i.n_itens
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN itens i ON i.order_id = o.order_id
LEFT JOIN notas n ON n.order_id = o.order_id;
