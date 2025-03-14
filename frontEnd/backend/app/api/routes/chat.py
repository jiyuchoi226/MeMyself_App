from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.models.chat import ChatMessage, ChatHistory
from app.services.chat_service import ChatService

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/get-chat-history", response_model=ChatHistory)
async def get_chat_history(user_id: str = Query(...)):
    """
    사용자 ID를 기반으로 채팅 히스토리를 조회합니다.
    
    Args:
        user_id: 사용자 이메일 또는 식별자
        
    Returns:
        ChatHistory: 메시지와 채팅 히스토리 목록
    """
    try:
        logger.info(f"사용자 {user_id}의 채팅 히스토리 조회 요청")
        chat_service = ChatService()
        history = chat_service.get_chat_history(user_id)
        
        # 히스토리가 없는 경우
        if not history:
            logger.info(f"사용자 {user_id}의 채팅 히스토리 없음")
            return ChatHistory(message="대화 기록 없음", chat_history=[])
        
        logger.info(f"사용자 {user_id}의 채팅 히스토리 {len(history)}개 조회 성공")
        return ChatHistory(message="대화 기록 조회 성공", chat_history=history)
    
    except Exception as e:
        logger.error(f"채팅 히스토리 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅 히스토리 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/add-chat-message", response_model=ChatMessage, status_code=status.HTTP_201_CREATED)
async def add_chat_message(message: ChatMessage):
    """
    새로운 채팅 메시지를 추가합니다.
    
    Args:
        message: 추가할 채팅 메시지 객체
        
    Returns:
        ChatMessage: 저장된 채팅 메시지
    """
    try:
        logger.info(f"사용자 {message.user_id}의 메시지 추가 요청")
        chat_service = ChatService()
        saved_message = chat_service.add_message(message)
        logger.info(f"메시지 추가 성공: {saved_message.id}")
        return saved_message
    
    except Exception as e:
        logger.error(f"메시지 추가 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메시지 추가 중 오류가 발생했습니다: {str(e)}"
        ) 