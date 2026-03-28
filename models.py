from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, handler):
        if isinstance(v, ObjectId):
            return str(v)
        return v

class CustomerModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class MessageModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: str
    role: str
    content: str
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ConversationModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: str
    customer_id: Optional[str] = None
    status: str = "active"
    messages: List[MessageModel] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
