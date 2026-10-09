"""Carga dos CSVs da Olist em SQLite e construção das tabelas analíticas (SQL em sql/)."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "olist.sqlite"

TABELAS = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def construir_banco(forcar: bool = False) -> Path:
    if DB.exists() and not forcar:
        return DB
    DB.unlink(missing_ok=True)
    with sqlite3.connect(DB) as con:
        for tabela, arquivo in TABELAS.items():
            pd.read_csv(RAW / arquivo).to_sql(tabela, con, index=False)
        for sql in sorted((ROOT / "sql").glob("*.sql")):
            con.executescript(sql.read_text(encoding="utf-8"))
    return DB


def consulta(sql: str) -> pd.DataFrame:
    construir_banco()
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)
