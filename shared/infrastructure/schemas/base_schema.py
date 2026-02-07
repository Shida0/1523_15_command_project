"""
Базовые Pydantic схемы.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class BaseSchema(BaseModel):
    """Базовая схема с общими полями."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CreateSchema(BaseModel):
    """Базовая схема для создания."""
    model_config = ConfigDict(from_attributes=True)