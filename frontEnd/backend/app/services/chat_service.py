from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.models.chat import ChatMessage
from app.db.database import get_db_connection

# 로깅 설정
logger = logging.getLogger(__name__)

class ChatService:
    """채팅 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self):
        """데이터베이스 연결 초기화"""
        self.db = get_db_connection()
    
    def get_chat_history(self, user_id: str) -> List[ChatMessage]:
        """
        사용자의 채팅 히스토리를 조회합니다.
        
        Args:
            user_id: 사용자 식별자
            
        Returns:
            List[ChatMessage]: 채팅 메시지 목록
        """
        try:
            # 데이터베이스에서 사용자의 채팅 히스토리 조회
            logger.info(f"사용자 {user_id}의 채팅 히스토리 조회 시도")
            messages = self.db.query(
                "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp", 
                (user_id,)
            )
            
            # 결과가 없는 경우 빈 리스트 반환
            if not messages:
                logger.info(f"사용자 {user_id}의 채팅 히스토리가 없습니다.")
                return []
            
            # 결과를 ChatMessage 객체로 변환
            chat_messages = []
            for msg in messages:
                try:
                    # 타임스탬프 문자열을 datetime 객체로 변환
                    if isinstance(msg['timestamp'], str):
                        msg['timestamp'] = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    
                    # is_user를 불리언으로 변환
                    if isinstance(msg['is_user'], int):
                        msg['is_user'] = bool(msg['is_user'])
                    
                    chat_messages.append(ChatMessage(**msg))
                except Exception as e:
                    logger.error(f"메시지 변환 오류: {msg}, {e}")
            
            logger.info(f"사용자 {user_id}의 채팅 히스토리 {len(chat_messages)}개 조회 성공")
            return chat_messages
            
        except Exception as e:
            logger.error(f"채팅 히스토리 조회 오류: {e}")
            return []
    
    def add_message(self, message: ChatMessage) -> ChatMessage:
        """
        새 메시지를 저장합니다.
        
        Args:
            message: 저장할 메시지 객체
            
        Returns:
            ChatMessage: 저장된 메시지
        """
        try:
            # ID가 없는 경우 생성
            if not message.id:
                message.id = str(uuid.uuid4())
            
            # 타임스탬프가 없는 경우 현재 시간 설정
            if not message.timestamp:
                message.timestamp = datetime.now()
            
            # 데이터베이스에 메시지 저장
            success = self.db.execute(
                "INSERT INTO chat_messages (id, user_id, content, is_user, timestamp) VALUES (?, ?, ?, ?, ?)",
                (message.id, message.user_id, message.content, message.is_user, message.timestamp)
            )
            
            if success:
                logger.info(f"메시지 저장 성공: {message.id}")
                return message
            else:
                logger.error(f"메시지 저장 실패: {message.id}")
                raise Exception("메시지 저장 실패")
                
        except Exception as e:
            logger.error(f"메시지 추가 오류: {e}")
            raise 