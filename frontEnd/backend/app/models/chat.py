from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    id: str
    user_id: str
    content: str
    is_user: bool  # True: 사용자 메시지, False: AI 응답
    timestamp: datetime
    
    class Config:
        orm_mode = True

class ChatHistory(BaseModel):
    """채팅 히스토리 응답 모델"""
    message: str
    chat_history: List[ChatMessage] 