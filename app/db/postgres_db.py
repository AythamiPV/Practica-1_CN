import psycopg2
import psycopg2.extras
import psycopg2.pool
from typing import List, Optional
from .db import Database
from models.product import Product
import os

class PostgresDatabase(Database):
    
    def __init__(self):
        # Configuración de conexión sin conectar inmediatamente
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASS'),
            'database': os.getenv('DB_NAME'),
            'connect_timeout': 5,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 5,
            'keepalives_count': 5
        }
        
        # Usar un pool simple de conexiones
        self._connection_pool = None
        self.initialize()

    def _get_connection(self):
        """Obtiene una conexión del pool o crea una nueva"""
        return psycopg2.connect(**self.db_config)

    def initialize(self):
        """Crear tabla si no existe"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
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
                conn.commit()
        finally:
            conn.close()

    def create_product(self, product: Product) -> Product:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO products (product_id, name, price, stock, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    product.product_id, product.name, product.price, product.stock,
                    product.description, product.created_at, product.updated_at
                ))
                conn.commit()
            return product
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_product(self, product_id: str) -> Optional[Product]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = "SELECT * FROM products WHERE product_id = %s"
                cursor.execute(sql, (product_id,))
                row = cursor.fetchone()
                if row:
                    row['created_at'] = row['created_at'].isoformat() if row['created_at'] else None
                    row['updated_at'] = row['updated_at'].isoformat() if row['updated_at'] else None
                    return Product(**row)
            return None
        finally:
            conn.close()

    def get_all_products(self) -> List[Product]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = "SELECT * FROM products ORDER BY name"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [Product(**{
                    **row,
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                }) for row in rows]
        finally:
            conn.close()

    def update_product(self, product_id: str, product: Product) -> Optional[Product]:
        product.update_timestamp()
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE products
                    SET name=%s, price=%s, stock=%s, description=%s, updated_at=%s
                    WHERE product_id=%s
                """
                cursor.execute(sql, (
                    product.name, product.price, product.stock, product.description,
                    product.updated_at, product_id
                ))
                conn.commit()
                if cursor.rowcount > 0:
                    # Necesitamos recuperar el producto actualizado
                    return self.get_product(product_id)
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_product(self, product_id: str) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM products WHERE product_id = %s"
                cursor.execute(sql, (product_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()