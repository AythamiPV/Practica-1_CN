from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid

class Product(BaseModel):
    product_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def update_timestamp(self):
        self.updated_at = datetime.utcnow().isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Caña de pescar Shimano FX2500",
                "price": 89.99,
                "stock": 10,
                "description": "Caña ligera para pesca deportiva de agua dulce"
            }
        }
