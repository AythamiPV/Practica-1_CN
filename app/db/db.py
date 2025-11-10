from abc import ABC, abstractmethod
from typing import List, Optional
from models.product import Product

class Database(ABC):
    
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def create_product(self, product: Product) -> Product:
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        pass

    @abstractmethod
    def get_all_products(self) -> List[Product]:
        pass

    @abstractmethod
    def update_product(self, product_id: str, product: Product) -> Optional[Product]:
        pass

    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        pass
