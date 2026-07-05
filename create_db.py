"""
create_db.py
Genera una base de datos SQLite de ejemplo (tienda online) para probar
el generador de consultas SQL con IA.
"""

import sqlite3
import os

DB_PATH = os.path.join("data", "store.db")


def create_database():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            signup_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
    """)

    customers = [
        (1, "Ana Torres", "Peru", "2024-01-15"),
        (2, "Luis Mamani", "Peru", "2024-02-20"),
        (3, "Maria Gomez", "Chile", "2024-01-30"),
        (4, "John Smith", "USA", "2024-03-05"),
        (5, "Carla Vidal", "Peru", "2024-04-11"),
    ]
    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?)", customers
    )

    products = [
        (1, "Laptop Pro 15", "Electronics", 3500.00),
        (2, "Wireless Mouse", "Electronics", 80.00),
        (3, "Office Chair", "Furniture", 450.00),
        (4, "Standing Desk", "Furniture", 900.00),
        (5, "USB-C Hub", "Electronics", 120.00),
    ]
    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)", products
    )

    orders = [
        (1, 1, 1, 1, "2024-05-01"),
        (2, 1, 2, 2, "2024-05-01"),
        (3, 2, 3, 1, "2024-05-03"),
        (4, 3, 1, 1, "2024-05-04"),
        (5, 4, 5, 3, "2024-05-06"),
        (6, 5, 4, 1, "2024-05-07"),
        (7, 2, 1, 1, "2024-05-10"),
        (8, 3, 5, 2, "2024-05-12"),
    ]
    cursor.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders
    )

    conn.commit()
    conn.close()
    print(f"Base de datos creada en: {DB_PATH}")


if __name__ == "__main__":
    create_database()
