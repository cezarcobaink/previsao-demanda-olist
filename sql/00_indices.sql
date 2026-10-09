CREATE INDEX IF NOT EXISTS ix_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_orders_cust ON orders(customer_id);
CREATE INDEX IF NOT EXISTS ix_cust_id ON customers(customer_id);
CREATE INDEX IF NOT EXISTS ix_sellers_id ON sellers(seller_id);
CREATE INDEX IF NOT EXISTS ix_products_id ON products(product_id);
CREATE INDEX IF NOT EXISTS ix_reviews_order ON order_reviews(order_id);
