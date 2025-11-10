import os
from typing import Dict, Type
from .db import Database
from .postgres_db import PostgresDatabase


class DatabaseFactory:
    """
    Fábrica de bases de datos para la API de tienda de pesca.
    Actualmente solo soporta PostgreSQL, pero está preparada
    para extenderse fácilmente si se desea agregar otros motores.
    """

    _databases: Dict[str, Type[Database]] = {
        'postgres': PostgresDatabase,
    }

    @classmethod
    def create(cls, db_type: str = None) -> Database:
        """
        Crea una instancia de base de datos según el tipo definido
        por la variable de entorno DB_TYPE (por defecto: postgres)
        """
        if db_type is None:
            db_type = os.getenv('DB_TYPE', 'postgres')

        db_type = db_type.lower()
        database_class = cls._databases.get(db_type)

        if database_class is None:
            available = ', '.join(cls._databases.keys())
            raise ValueError(
                f"DB_TYPE '{db_type}' no válido. "
                f"Opciones disponibles: {available}"
            )

        return database_class()

    @classmethod
    def get_available_databases(cls) -> list:
        """Devuelve una lista de los tipos de bases de datos disponibles"""
        return list(cls._databases.keys())
