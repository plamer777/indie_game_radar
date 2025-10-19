from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
# ---------------------------------------------------------------------------------------------------------------------


class BaseDBModel(BaseModel):
    id: str = Field(..., validation_alias="_id")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None