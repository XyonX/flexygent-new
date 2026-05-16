
from typing import Any,Callable,Awaitable
from pydantics import BaseModel


class ToolParameaters(BaseModel):
    type:str
    description:str


class ToolSchema(BaseModel):
