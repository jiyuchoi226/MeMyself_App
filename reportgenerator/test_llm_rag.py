import os
import sys
# 백엔드 디렉토리를 Python 경로에 추가합니다
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 앱 모듈 임포트
from app.vector_store import VectorStore
from app.llm_rag import ConversationHistory, LLMService

def get_user_input(prompt, default=None):
    """사용자 입력을 받는 함수"""
    if default:
        user_input = input(f"{prompt} [기본값: {default}]: ")
        return user_input if user_input.strip() else default
    else:
        return input(f"{prompt}: ")

def validate_date(date_str):
    """날짜 형식 검증 함수 (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def get_events_for_date(user_id, date_str):
    """특정 날짜의 일정 가져오기"""
    try:
        vector_store = VectorStore()
        schedule_path = os.path.join("data", "faiss", user_id, "schedule")
        
        if not os.path.exists(schedule_path):
            print(f"일정 데이터가 없습니다: {schedule_path}")
            return []
        
        schedule_faiss = vector_store.load_index(user_id)
        if schedule_faiss is None:
            print("일정 데이터를 로드할 수 없습니다.")
            return []
            
        all_events = schedule_faiss.docstore._dict.values()
        
        # 해당 날짜의 일정만 필터링
        date_events = [
            event for event in all_events 
            if event.metadata.get("original_event", {}).get("start", "").startswith(date_str)
        ]
        
        # 시작 시간 기준으로 정렬
        date_events.sort(key=lambda x: x.metadata.get("original_event", {}).get("start", ""))
        
        return date_events
    except Exception as e:
        print(f"일정 가져오기 오류: {str(e)}")
        return []

def display_events(events):
    """일정 목록 표시"""
    if not events:
        print("해당 날짜에 일정이 없습니다.")
        return False
    
    print("\n===== 일정 목록 =====")
    for i, event in enumerate(events, 1):
        event_data = event.metadata.get("original_event", {})
        summary = event_data.get("summary", "제목 없음")
        start = event_data.get("start", "").split("T")[1][:5] if "T" in event_data.get("start", "") else ""
        end = event_data.get("end", "").split("T")[1][:5] if "T" in event_data.get("end", "") else ""
        emotion = event_data.get("emotion_score", 0)
        
        emotion_text = ""
        if emotion > 0:
            # LLMService 없이 간단히 표시
            emotion_dict = {
                1: "매우 불만족",
                2: "불만족",
                3: "보통",
                4: "만족",
                5: "매우 만족"
            }
            emotion_text = f" - 감정: {emotion_dict.get(emotion, '')}"
            
        print(f"{i}. {summary} ({start}-{end}){emotion_text}")
    print("=====================\n")
    return True

def initialize_services(user_id):
    """필요한 서비스 초기화"""
    try:
        # Vector Store 초기화
        vector_store = VectorStore()
        
        # LLM 서비스 초기화
        llm_service = LLMService()
        
        # 대화 기록 초기화
        conversation_history = ConversationHistory(vector_store.embeddings, vector_store.text_splitter)
        conversation_history.load_index(user_id)
        
        print("서비스가 성공적으로 초기화되었습니다.")
        return vector_store, llm_service, conversation_history
    except Exception as e:
        print(f"서비스 초기화 오류: {str(e)}")
        sys.exit(1)

def sequential_conversation(user_id, date_str, events):
    """일정 순서대로 대화 진행"""
    # 서비스 초기화
    vector_store, llm_service, conversation_history = initialize_services(user_id)
    
    print(f"\n===== {date_str} 일정에 대한 대화를 시작합니다 =====\n")
    
    # 각 일정에 대해 순차적으로 대화
    for i, event in enumerate(events, 1):
        event_data = event.metadata.get("original_event", {})
        summary = event_data.get("summary", "제목 없음")
        start = event_data.get("start", "").split("T")[1][:5] if "T" in event_data.get("start", "") else ""
        end = event_data.get("end", "").split("T")[1][:5] if "T" in event_data.get("end", "") else ""
        
        print(f"\n----- 일정 {i}/{len(events)}: {summary} ({start}-{end}) -----")
        
        # 현재 일정 설정
        llm_service.current_event = event_data
        
        # 질문 생성
        if "emotion_score" in event_data and event_data["emotion_score"] > 0:
            emotion_text = llm_service.get_emotion_text(event_data["emotion_score"])
            question = f"어제의 {summary} 일정에 대해 {emotion_text}고 하셨는데, 왜 그렇게 생각하셨나요?"
        else:
            question = f"{summary} 일정은 어떠셨나요?"
        
        llm_service.current_question = question
        print(f"AI: {question}")
        
        # 사용자 응답 입력
        user_input = get_user_input("응답")
        if user_input.lower() in ['q', 'exit', 'quit']:
            print("대화를 종료합니다.")
            break
        
        # 대화 기록 저장
        emotion_info = {
            "score": event_data.get("emotion_score", 0),
            "text": llm_service.get_emotion_text(event_data.get("emotion_score", 0))
        }
        
        conversation_history.add_conversation(
            user_id=user_id,
            bot_question=llm_service.current_question,
            user_answer=user_input,
            event_info=event_data,
            emotion_info=emotion_info
        )
        
        # 중간 저장
        conversation_history.save_index(user_id)
        
    print("\n===== 모든 일정에 대한 대화가 완료되었습니다 =====")
    
    # 최종 저장
    conversation_history.save_index(user_id)
    print(f"대화 내용이 저장되었습니다: data/faiss/{user_id}/history/{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')}")
    
    return True

def main():
    """메인 실행 함수"""
    print("=== 일정 순차 대화 테스트 도구 ===")
    
    # 사용자 이메일 입력
    user_id = get_user_input("사용자 이메일 입력")
    if not user_id:
        print("이메일이 필요합니다.")
        return
    
    # 날짜 입력
    yesterday = (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)).strftime("%Y-%m-%d")
    date_str = get_user_input("날짜 입력 (YYYY-MM-DD 형식)", yesterday)
    
    if not validate_date(date_str):
        print("올바른 날짜 형식이 아닙니다. YYYY-MM-DD 형식으로 입력해주세요.")
        return
    
    # 해당 날짜의 일정 가져오기
    events = get_events_for_date(user_id, date_str)
    
    # 일정 표시
    if not display_events(events):
        print("대화를 진행할 일정이 없습니다.")
        return
    
    # 일정에 대한 감정 점수 입력 (선택사항)
    emotion_input = get_user_input("일정에 감정 점수를 추가하시겠습니까? (y/n)", "n")
    if emotion_input.lower() == 'y':
        for i, event in enumerate(events):
            event_data = event.metadata.get("original_event", {})
            summary = event_data.get("summary", "제목 없음")
            emotion = int(get_user_input(f"{summary} 일정의 감정 점수 (1-5, 0은 건너뛰기)", "0"))
            if 1 <= emotion <= 5:
                event.metadata["original_event"]["emotion_score"] = emotion
    
    # 대화 시작 확인
    confirm = get_user_input("일정 순서대로 대화를 시작하시겠습니까? (y/n)", "y")
    if confirm.lower() != 'y':
        print("프로그램을 종료합니다.")
        return
    
    # 순차 대화 실행
    sequential_conversation(user_id, date_str, events)

if __name__ == "__main__":
    main()