-- Fato no grão item do pedido, só pedidos entregues ou em andamento (exclui cancelados/indisponíveis)
CREATE TABLE fact_itens AS
SELECT
    o.order_id,
    oi.order_item_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state                         AS uf_cliente,
    s.seller_state                           AS uf_vendedor,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS categoria,
    o.order_status,
    DATE(o.order_purchase_timestamp)         AS data_compra,
    o.order_purchase_timestamp               AS ts_compra,
    o.order_delivered_customer_date          AS ts_entrega,
    o.order_estimated_delivery_date          AS ts_prometido,
    oi.price                                 AS preco,
    oi.freight_value                         AS frete
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers  c  ON c.customer_id = o.customer_id
JOIN sellers    s  ON s.seller_id   = oi.seller_id
LEFT JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status NOT IN ('canceled', 'unavailable');
