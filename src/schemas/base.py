from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field, model_serializer
# ---------------------------------------------------------------------------------------------------------------------


class BaseSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    @model_serializer
    def serialize(self):
        value = dict(self)
        value["_id"] = value.pop("id")
        return value

    class Config:
        extra = "ignore"