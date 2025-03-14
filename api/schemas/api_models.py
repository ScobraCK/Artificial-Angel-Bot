from pydantic import BaseModel, Field
from datetime import datetime
from typing import Generic, TypeVar
from fastapi import Request

T = TypeVar("T")
class APIResponse(BaseModel, Generic[T]):
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(examples=['version'])
    data: T

    @classmethod
    def create(cls, request: Request, data: T) -> "APIResponse[T]":
        return cls(
            version=request.app.state.md.version,
            data=data,
        )
