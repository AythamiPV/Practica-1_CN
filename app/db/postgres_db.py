import psycopg2
import psycopg2.extras
from typing import List, Optional
from .db import Database
from models.product import Product
import os

class PostgresDatabase(Database):
    
    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        self.connection.autocommit = True
        self.initialize()

    def initialize(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id   VARCHAR(36) PRIMARY KEY,
                    name         VARCHAR(255) NOT NULL,
                    price        NUMERIC(10,2) NOT NULL CHECK (price > 0),
                    stock        INTEGER NOT NULL CHECK (stock >= 0),
                    description  TEXT,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def create_product(self, product: Product) -> Product:
        with self.connection.cursor() as cursor:
            sql = """
                INSERT INTO products (product_id, name, price, stock, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                product.product_id, product.name, product.price, product.stock,
                product.description, product.created_at, product.updated_at
            ))
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            sql = "SELECT * FROM products WHERE product_id = %s"
            cursor.execute(sql, (product_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].isoformat() if row['created_at'] else None
                row['updated_at'] = row['updated_at'].isoformat() if row['updated_at'] else None
                return Product(**row)
        return None

    def get_all_products(self) -> List[Product]:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            sql = "SELECT * FROM products ORDER BY name"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Product(**{
                **row,
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            }) for row in rows]

    def update_product(self, product_id: str, product: Product) -> Optional[Product]:
        product.update_timestamp()
        with self.connection.cursor() as cursor:
            sql = """
                UPDATE products
                SET name=%s, price=%s, stock=%s, description=%s, updated_at=%s
                WHERE product_id=%s
            """
            cursor.execute(sql, (
                product.name, product.price, product.stock, product.description,
                product.updated_at, product_id
            ))
            if cursor.rowcount > 0:
                return self.get_product(product_id)
        return None

    def delete_product(self, product_id: str) -> bool:
        with self.connection.cursor() as cursor:
            sql = "DELETE FROM products WHERE product_id = %s"
            cursor.execute(sql, (product_id,))
            return cursor.rowcount > 0
