from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json

class VectorStore:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=100)
        self.embeddings = UpstageEmbeddings(model='embedding-query', api_key=os.getenv('UPSTAGE_API_KEY'))
        self.vectorstore = None
        self.base_index_path = "data/faiss"  
        os.makedirs(self.base_index_path, exist_ok=True)

    def _get_user_index_path(self, user_id: str) -> str:
        user_path = os.path.join(self.base_index_path, user_id)
        schedule_path = os.path.join(user_path, "schedule")
        os.makedirs(schedule_path, exist_ok=True)
        return schedule_path

    def _format_event_text(self, event: Dict) -> str:
        formatted_text = f"일정: {event.get('summary', '제목 없음')}\n"
        formatted_text += f"시작: {event.get('start', '')}\n"
        formatted_text += f"종료: {event.get('end', '')}\n"
        formatted_text += f"타입: {event.get('calendar_info', {}).get('summary', '기본')}\n"
        formatted_text += f"반복: {event.get('recurrence')[0] if event.get('recurrence') else '반복정보 없음'}\n"  
        formatted_text += f"감정 점수: {event.get('emotion_score', 0)}"
        return formatted_text

    def save_index(self, user_id: str):
        if self.vectorstore:
            index_path = self._get_user_index_path(user_id)
            self.vectorstore.save_local(index_path)
            print(f"인덱스가 {index_path}에 저장되었습니다.")
    
    def load_index(self, user_id: str):
        try:
            if not isinstance(user_id, str) or not user_id:
                print("Invalid user_id")
                return None

            index_path = os.path.join("data", "faiss", user_id, "schedule")
            if not os.path.exists(index_path):
                print(f"No schedule index found for user {user_id}")
                return None

            faiss_index = FAISS.load_local(
                index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True  # pickle 접근 허용
            )
            return faiss_index
            
        except Exception as e:
            print(f"Error loading schedule index: {str(e)}")
            return None

    def add_events(self, user_id: str, events: List[dict]):
        try:
            index_path = self._get_user_index_path(user_id)
            if os.path.exists(index_path):
                import shutil
                shutil.rmtree(index_path)
                print(f"기존 인덱스 삭제: {index_path}")
            
            sorted_events = sorted(events, key=lambda x: x.get('start', ''))
            formatted_events = []
            documents = []
            for event in sorted_events:
                formatted_text = self._format_event_text(event)
                formatted_events.append(formatted_text)
                
                # 메타데이터에 반복 일정 정보 무조건 포함
                metadata = {
                    "original_event": event,
                    "recurrence": event.get('recurrence', []),  # 없으면 빈 리스트
                    "recurrence_id": event.get('recurringEventId', ''),  # 없으면 빈 문자열
                    "is_recurring": bool(event.get('recurrence') or event.get('recurringEventId')),
                }
                
                documents.append(Document(
                    page_content=formatted_text, 
                    metadata=metadata
                ))
            
            json_path = os.path.join(index_path, "events.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            json_data = {
                'events': formatted_events,
                'updated_at': datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"JSON 파일 저장 완료: {json_path}")
            
            split_docs = self.text_splitter.split_documents(documents)
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            self.save_index(user_id)
            print(f"새로운 인덱스 생성 완료: {len(events)}개 이벤트")
                
        except Exception as e:
            print(f"이벤트 처리 중 오류 발생: {str(e)}")
            raise e
        
        
    def update_event_emotion(self, user_id: str, event_date: str, event_time: str, event_summary: str, emotion_score: int) -> bool:
        try:
            index_path = self._get_user_index_path(user_id)
            if not os.path.exists(index_path):
                return False
            
            event_time = event_time.split('.')[0]  
            if event_time.endswith('Z'):
                event_time = event_time[:-1]  
            print(f"찾는 일정: date={event_date}, time={event_time}, summary={event_summary}")
            
            # FAISS 인덱스 로드
            schedule_faiss = FAISS.load_local(
                index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # 모든 문서 가져오기
            all_docs = list(schedule_faiss.docstore._dict.values())
            updated_docs = []
            found = False
            
            for doc in all_docs:
                event = doc.metadata.get("original_event", {})
                event_start = event.get("start", "")
                
                if (event_start.startswith(event_date) and 
                    event.get("summary") == event_summary):
                    event["emotion_score"] = emotion_score
                    doc.metadata["original_event"] = event
                    doc.metadata["emotion_score"] = emotion_score
                    found = True
                    print(f"일정 찾음: {event_summary}")
                
                updated_docs.append(doc)
            
            if not found:
                print("일정을 찾지 못했습니다")
                return False
            
            # 업데이트된 문서로 새 FAISS 인덱스 생성
            texts = [doc.page_content for doc in updated_docs]
            metadatas = [doc.metadata for doc in updated_docs]
            
            new_faiss = FAISS.from_texts(
                texts,
                self.embeddings,
                metadatas=metadatas
            )
            new_faiss.save_local(index_path)
            
            # JSON으로도 저장
            json_path = os.path.join(index_path, "events.json")
            events_data = {
                'events': [doc.metadata.get("original_event", {}) for doc in updated_docs],
                'updated_at': datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=2)
            
            print(f"감정 점수 업데이트 완료: {event_summary}")
            return True
            
        except Exception as e:
            print(f"감정 점수 업데이트 중 오류 발생: {str(e)}")
            return False