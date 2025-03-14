import sys
import os
import uuid
from datetime import datetime, timedelta

# 상위 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_db_connection
from app.models.chat import ChatMessage

def add_test_messages(user_id: str, count: int = 5):
    """
    테스트용 메시지를 추가합니다.
    
    Args:
        user_id: 사용자 ID
        count: 추가할 메시지 수
    """
    db = get_db_connection()
    
    # 현재 시간
    now = datetime.now()
    
    for i in range(count):
        # 사용자 메시지
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=f"사용자 테스트 메시지 {i+1}",
            is_user=True,
            timestamp=now - timedelta(minutes=(count-i)*2)
        )
        
        # AI 응답 메시지
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=f"AI 응답 테스트 메시지 {i+1}",
            is_user=False,
            timestamp=now - timedelta(minutes=(count-i)*2-1)
        )
        
        # 데이터베이스에 저장
        db.execute(
            "INSERT INTO chat_messages (id, user_id, content, is_user, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_message.id, user_message.user_id, user_message.content, user_message.is_user, user_message.timestamp)
        )
        
        db.execute(
            "INSERT INTO chat_messages (id, user_id, content, is_user, timestamp) VALUES (?, ?, ?, ?, ?)",
            (ai_message.id, ai_message.user_id, ai_message.content, ai_message.is_user, ai_message.timestamp)
        )
    
    print(f"{count}개의 테스트 메시지 쌍이 추가되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python add_test_data.py <user_id> [count]")
        sys.exit(1)
    
    user_id = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    add_test_messages(user_id, count) 