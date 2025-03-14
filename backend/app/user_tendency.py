from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json

class UserTendency:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=100)
        self.embeddings = UpstageEmbeddings(model='embedding-query', api_key=os.getenv('UPSTAGE_API_KEY'))
        self.vectorstore = None
        self.base_index_path = "data/faiss"  
        os.makedirs(self.base_index_path, exist_ok=True)

    # user 성향
    def _get_user_tendency_path(self, user_id: str) -> str:
        return os.path.join(self.base_index_path, f"{user_id}_tendency")

    def _format_event_user(self, event: Dict) -> str:
        # 유저 기본 정보 출력
        user_tendency = event.get('user_tendency', {})
        formatted_text = f"{user_tendency.get('prompt', '')}"
        """formatted_text = f"user_id: {event.get('user_id', '')}\n"

        # user_tendency 내부 정보 추출
        user_tendency = event.get('user_tendency', {})
        formatted_text += f"MBTI: {user_tendency.get('mbti', '')}\n"
        formatted_text += f"생일: {user_tendency.get('birthday', '')}\n"
        formatted_text += f"성별: {user_tendency.get('gender', '')}\n"
        formatted_text += f"연령대: {user_tendency.get('age', '')}\n"

        # 성향(traits) 정보 출력
        traits = user_tendency.get('traits', {})
        if traits:
            formatted_text += "성향:\n"
            for trait, value in traits.items():
                formatted_text += f"  {trait}: {value}\n"
        """

        return formatted_text

    def save_index(self, user_id: str):
        if self.vectorstore:
            index_path = self._get_user_tendency_path(user_id)
            self.vectorstore.save_local(index_path)
            print(f"인덱스가 {index_path}에 저장되었습니다.")

    # 성향 데이터 로드
    def load_user_tendency(self, user_id: str):
        try:
            index_path = self._get_user_tendency_path(user_id)
            if os.path.exists(index_path):
                return FAISS.load_local(
                    index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            return None
        except Exception as e:
            print(f"인덱스 로드 중 에러: {str(e)}")
            return None

    #고정된 항목의 키는 그대로 두고, 그 값만 새 값으로 업데이트
    def update_user_tendency(existing_tendency: dict, updates: dict) -> dict:
        # updates 딕셔너리 안의 각 항목을 확인
        for key, value in updates.items():
            # 만약 key가 'traits'이면, 안쪽의 값들을 업데이트
            if key == "traits" and isinstance(value, dict):
                for trait_key, trait_val in value.items():
                    # 기존 traits에 같은 trait_key가 있다면 업데이트
                    if trait_key in existing_tendency.get("traits", {}):
                        existing_tendency["traits"][trait_key] = trait_val
                    else:
                        # 원하는 경우 새로운 키를 추가할 수도 있어요.
                        existing_tendency["traits"][trait_key] = trait_val
            else:
                # 'gender'와 같은 항목은 바로 값을 업데이트
                existing_tendency[key] = value
        return existing_tendency


    # 유저 성향 데이터 저장
    def add_tendency_events(self, user_id: str, events: List[dict]):
        try:
            # 1. 기존 인덱스 삭제
            index_path = self._get_user_tendency_path(user_id)
            if os.path.exists(index_path):
                import shutil
                shutil.rmtree(index_path)
                print(f"기존 인덱스 삭제: {index_path}")

            # 2. 포맷팅된 이벤트 리스트 생성
            formatted_events = []
            documents = []
            json_events = []  # 원본 데이터도 함께 저장

            for event in events:
                formatted_text = self._format_event_user(event)
                formatted_events.append({"formatted_text": formatted_text})  # JSON에 저장할 형태
                json_events.append(event)  # 원본 데이터 추가

                documents.append(Document(
                    page_content=formatted_text,
                    metadata={"original_event": event}
                ))
            
            # 3. JSON 파일 저장
            json_path = os.path.join(index_path, "events.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            json_data = {
                "events": formatted_events,  # formatted_text 리스트 저장
                "original_events": json_events,  # 원본 JSON 데이터 추가
                "updated_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"JSON 파일 저장 완료: {json_path}")
            
            # 4. FAISS 인덱스 생성 및 저장
            split_docs = self.text_splitter.split_documents(documents)
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            self.save_index(user_id)
            print(f"새로운 인덱스 생성 완료: {len(events)}개 이벤트")
                
        except Exception as e:
            print(f"이벤트 처리 중 오류 발생: {str(e)}")
            raise e


    # 전체 성향 조회 / 특정 키 조회 / 중첩된 키 조회
    def get_user_tendency_key(self, user_id: str, key: str = None, sub_key: str = None) -> dict:
        try:
            # 성향 JSON 로드
            user_data = self._get_user_tendency_path(user_id)
            if user_data is None:
                return {"error": "사용자 성향 데이터를 찾을 수 없습니다."}

            # 전체 데이터 반환
            if key is None:
                return {"message": "성향 조회 성공", "user_tendency": user_data}

            # 특정 키 조회
            if key in user_data:
                result = user_data[key]

                if result is None:
                    return {"error": f"'{key}' 데이터가 없습니다."}

                # 중첩된 키 조회
                if sub_key:
                    if isinstance(result, dict) and sub_key in result:
                        return {"message": "성향 조회 성공", "value": result[sub_key]}
                    else:
                        return {"error": f"'{key}' 안에 '{sub_key}' 데이터가 없습니다."}

                return {"message": "성향 조회 성공", "value": result}

            return {"error": f"'{key}'에 대한 데이터가 없습니다."}

        except Exception as e:
            print(f"[ERROR] 성향 조회 실패: {str(e)}")
            return {"error": f"성향 조회 실패: {str(e)}"}