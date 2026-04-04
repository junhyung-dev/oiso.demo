from pydantic import BaseModel, HttpUrl
from typing import Optional

class bookmarkBase(BaseModel):
    title : str
    url : HttpUrl
    description : Optional[str] = None
    #description: str | None = None 이랑 동일함    
    
class bookmarkCreate(bookmarkBase):
    pass
    
class bookmarkResponse(bookmarkBase):
    id: int
    
    class Config:
        from_attributes = True