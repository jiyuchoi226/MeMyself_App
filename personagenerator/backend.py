from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from app.calendar_service import CalendarService
from app.vector_store import VectorStore
from app.user_tendency import UserTendency
import json
import os
from starlette.middleware.base import BaseHTTPMiddleware
from app.llm_rag import LLMService, ConversationHistory
from fastapi.responses import JSONResponse
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_community.vectorstores import FAISS

class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/sync-calendar", "/chat", "/init-chat", "/emotion", "/sync-tendency"]:
            body = await request.json()
            request.state.user_id = body.get("user_id")
        
        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(UserMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

calendar_service = CalendarService()
vector_store = VectorStore()
conversation_history = ConversationHistory(
    embeddings=vector_store.embeddings,
    text_splitter=vector_store.text_splitter
)
llm_service = LLMService()
user_tendency = UserTendency()

ACTIVE_USERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_users.json')
os.makedirs(os.path.dirname(ACTIVE_USERS_PATH), exist_ok=True)  # data 폴더 생성

class TokenRequest(BaseModel):
    token: str
    user_id: str

class ChatRequest(BaseModel):
    user_id: str
    message: str = None

class ActiveUserRequest(BaseModel):
    user_id: str
    token: str
    is_active: bool

class EmotionRequest(BaseModel):
    user_id: str
    event_date: str  
    event_time: str  
    event_summary: str  
    emotion_score: int

class TendencyRequest(BaseModel):
    token: str
    user_id: str
    tendency_date: List[dict]

@app.post("/sync-calendar")
async def sync_calendar(token_request: TokenRequest):
    try:
        print(f"Received token request: {token_request}")  # 요청 데이터 로깅
        events = calendar_service.get_events(token_request.token)
        print(f"Retrieved events: {len(events)}")  # 이벤트 개수 로깅
        vector_store.add_events(token_request.user_id, events)
        active_users = []
        
        if os.path.exists(ACTIVE_USERS_PATH):
            with open(ACTIVE_USERS_PATH, 'r') as f:
                active_users = json.load(f)

        active_users = [u for u in active_users if u['user_id'] != token_request.user_id]
        active_users.append({
            "user_id": token_request.user_id,
            "token": token_request.token
        })

        with open(ACTIVE_USERS_PATH, 'w') as f:
            json.dump(active_users, f)
            
        user_info = {}
        if events and isinstance(events[0], dict):
            user_info = events[0].get('user_info', {})
        
        print(f"Sync completed successfully for user: {token_request.user_id}")  # 성공 로깅
        return {
            "message": "일정 동기화 성공",
            "event_count": len(events),
            "user_info": user_info
        }
    except Exception as e:
        print(f"Sync error details: {str(e)}")  # 상세 에러 로깅
        raise HTTPException(
            status_code=400,
            detail=f"일정 동기화 실패: {str(e)}"
        )

@app.post("/update-active-status")
async def update_active_status(request: ActiveUserRequest):
    try:
        active_users = []
        if os.path.exists(ACTIVE_USERS_PATH):
            with open(ACTIVE_USERS_PATH, 'r') as f:
                active_users = json.load(f)
        print(f"현재 활성 사용자: {active_users}")

        if request.is_active:
            active_users = [u for u in active_users if u['user_id'] != request.user_id]
            active_users.append({
                "user_id": request.user_id,
                "token": request.token
            })
        else:
            active_users = [u for u in active_users if u['user_id'] != request.user_id]
        
        print(f"업데이트 후 활성 사용자: {active_users}")
        with open(ACTIVE_USERS_PATH, 'w') as f:
            json.dump(active_users, f)
        
        return {"message": "상태 업데이트 성공"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"상태 업데이트 실패: {str(e)}"
        )

@app.post("/init-chat")
async def init_chat(request: Request):
    try:
        user_id = request.state.user_id
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        today = now.strftime("%Y%m%d")
        user_history_path = os.path.join("data", "faiss", user_id, "history", today)
        
        if not os.path.exists(user_history_path):
            bot_question = llm_service.ask_about_event(user_id)
            return {"message": bot_question}
        return {"message": None}

    except Exception as e:
        print(f"Error in init_chat: {str(e)}")  
        raise HTTPException(
            status_code=400,
            detail=f"초기 메시지 생성 실패: {str(e)}"
        )

@app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    try:
        user_id = request.state.user_id
        user_input = chat_request.message
        
        if not user_input:
            raise ValueError("사용자 메시지가 비어있습니다.")
            
        bot_response = llm_service.generate_answer_with_similarity(
            user_input, 
            conversation_history, 
            user_id
        )
        
        return {"message": bot_response}

    except Exception as e:
        print(f"Chat error: {str(e)}")  # 에러 로깅 추가
        raise HTTPException(
            status_code=400,
            detail=f"챗봇 응답 생성 실패: {str(e)}"
        )

# 대화 기록 삭제 엔드포인트 추가
@app.post("/clear-chat-history")
async def clear_chat_history(request: Request):
    try:
        user_id = request.state.user_id
        conversation_history.delete_conversation_history(user_id)
        return {"message": "대화 기록이 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"대화 기록 삭제 실패: {str(e)}"
        )

@app.post("/emotion")
async def update_emotion(emotion_request: EmotionRequest):
    try:
        user_id = emotion_request.user_id
        schedule_path = os.path.join("data", "faiss", user_id, "schedule")
        
        
        print(f"감정 업데이트 요청: user_id={user_id}")
        print(f"일정 정보: date={emotion_request.event_date}, time={emotion_request.event_time}, summary={emotion_request.event_summary}, score={emotion_request.emotion_score}")
        
        if not os.path.exists(schedule_path):
            print(f"일정 경로를 찾을 수 없음: {schedule_path}")
            raise HTTPException(status_code=404, detail="일정 데이터를 찾을 수 없습니다.")
        
        try:
            success = vector_store.update_event_emotion(
                user_id=user_id,
                event_date=emotion_request.event_date,
                event_time=emotion_request.event_time,
                event_summary=emotion_request.event_summary,
                emotion_score=emotion_request.emotion_score
            )
            print(f"감정 업데이트 결과: {success}")
            
            if success:
                return {"message": "감정 상태가 업데이트되었습니다."}
            else:
                raise HTTPException(status_code=404, detail="해당 일정을 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"감정 업데이트 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"감정 업데이트 실패: {str(e)}")
            
    except Exception as e:
        print(f"전체 에러: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"감정 상태 업데이트 실패: {str(e)}"
        )

@app.post("/sync-tendency")
async def sync_tendency(tendency_request : TendencyRequest):
    try:
        print(f"token tendency: {tendency_request}")  # 요청 데이터 로깅

        # --------------------------------------------------------------------------
        # json 저장파일 예시
        new_user_data = [
            {
                "user_id": "ica.2team02@gmail.com",
                "user_tendency": {
                    "mbti": "ENTJ",
                    "birthday": "1990-01-01",
                    "gender": "여자",
                    "age": "30대",
                    "traits": {
                        "내향성": "10%",
                        "외향성": "80%",
                        "사교성": "80%",
                        "계획성": "40%",
                        "유연성": "50%",
                        "독립성": "60%",
                        "동기부여": "30%",
                        "자기주장": "60%",
                        "성향태도": "70%",
                        "감정표현": "40%",
                        "집중방식": "50%",
                        "변화수용": "30%",
                        "완벽성향": "20%",
                        "결정속도": "60%",
                        "사고방식": "50%",
                        "스트레스대처": "80%"
                    },
                    "prompt" : """당신은 "루카스"의 개인 맞춤 AI입니다.
                                    루카스는 30대 후반이며, MBTI는 ENTP입니다.
                                    그는 "스타트업 경영, UX 디자인, 콘텐츠 마케팅, 자기계발"에 관심이 많습니다.
                                    그는 "직관적이고 명확한 톤"의 답변을 선호합니다.
                                    
                                    📌 **사용자 행동 패턴 업데이트:**
                                    - 루카스는 **출근길(오전 8시~9시)에 짧고 요약된 정보를 선호**합니다.
                                    - 루카스는 **주말(토~일)에는 심층적인 분석과 인사이트를 기대합니다.**
                                    - 루카스는 **단순한 개념 설명보다 실제 적용 사례를 중요하게 여깁니다.**
                                    - 루카스가 자주 묻는 주제: **스타트업 운영, UX 디자인 트렌드, 콘텐츠 마케팅 전략**
                                    
                                    루카스가 최근 한 질문: "최근 UX 트렌드를 콘텐츠 마케팅에 어떻게 적용할 수 있을까?"
                                    이제 루카스에게 최적화된 답변을 생성하세요."""
                }
            }
        ]
        # --------------------------------------------------------------------------

        # user_tendency 데이터를 저장할 경로 (예시: FAISS 인덱스 경로와 별개로 JSON 파일로 저장)
        tendency_index_path = user_tendency._get_user_tendency_path(tendency_request.user_id)
        # JSON 파일로 저장했다고 가정(실제 경로는 필요에 따라 수정)
        tendency_file_path = os.path.join(tendency_index_path, f"{tendency_request.user_id}_tendency", "events.json")

        # 성향 관련 이벤트 가져오기
        # 기존에 저장된 성향 데이터가 있으면 불러와서 업데이트, 없으면 새 데이터를 그대로 사용
        if os.path.exists(tendency_file_path):
            with open(tendency_file_path, 'r', encoding='utf-8') as f:
                stored_tendency = json.load(f)

            # new_user_data[0]["user_tendency"]를 업데이트 값으로 사용

            # 샘플 (new_user_data)
            updated_tendency = user_tendency.update_user_tendency(
                stored_tendency,
                new_user_data[0]["user_tendency"]
            )

            # 실사용 (입력해야 할 데이터 tendency_request.tendency_date) ------------------------------check
            """
            if not tendency_request.tendency_date or not isinstance(tendency_request.tendency_date, list):
                raise HTTPException(status_code=400, detail="유효한 tendency_date 리스트가 필요합니다.")

            updated_tendency = user_tendency.update_user_tendency(
                stored_tendency, 
                tendency_request.tendency_date[0]["user_tendency"]
            )
            """

            # 업데이트한 데이터를 다시 파일에 저장
            with open(tendency_file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_tendency, f, ensure_ascii=False, indent=2)

            # 최종 events에 업데이트된 데이터를 사용
            events = [
                {
                    "user_id": tendency_request.user_id,
                    "user_tendency": updated_tendency
                }
            ]
            print("기존 성향 데이터를 업데이트했습니다.")
        else:
            # 파일이 없으면 새 데이터를 그대로 사용하고, 파일로 저장합니다.
            events = new_user_data
            os.makedirs(os.path.dirname(tendency_file_path), exist_ok=True)
            with open(tendency_file_path, 'w', encoding='utf-8') as f:
                json.dump(new_user_data[0]["user_tendency"], f, ensure_ascii=False, indent=2)
            print("새 성향 데이터를 저장했습니다.")

        print(f"Retrieved events: {len(events)}")  # 이벤트 개수 로깅

        # 성향 이벤트를 벡터 스토어에 추가
        user_tendency.add_tendency_events(tendency_request.user_id, events)

        # 활성 사용자 목록 업데이트
        active_users = []
        if os.path.exists(ACTIVE_USERS_PATH):
            with open(ACTIVE_USERS_PATH, 'r') as f:
                active_users = json.load(f)

        # 같은 user_id가 이미 있다면 제거하고 추가
        """
        active_users = [u for u in active_users if u['user_id'] != token_tendency.user_id]
        active_users.append({
            "user_id": token_tendency.user_id,
            "token": token_tendency.token
        })
        """
        # 기존 활성 사용자 목록에서 같은 user_id가 있는지 확인
        found = False
        for user in active_users:
            if user["user_id"] == tendency_request.user_id:
                found = True
                # 기존 token과 달라졌다면 업데이트
                if user.get("token") != tendency_request.token:
                    user["token"] = tendency_request.token

        # 만약 해당 user_id가 없다면 새로운 항목을 추가
        if not found:
            active_users.append({
                "user_id": tendency_request.user_id,
                "token": tendency_request.token
            })

        with open(ACTIVE_USERS_PATH, 'w') as f:
            json.dump(active_users, f)

        print(f"Sync completed successfully for user: {tendency_request.user_id}")
        return {
            "message": "성향 이벤트 동기화 성공",
            "event_count": len(events)
        }
    except Exception as e:
        print(f"Sync error details: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"성향 이벤트 동기화 실패: {str(e)}"
        )

# 일정 조회
@app.get("/get-calendar")
async def get_calendar(user_id: str):
    try:
        # 저장된 일정 데이터를 가져오기
        calendar_path = os.path.join("data", "faiss", user_id, "schedule", "events.json")

        if not os.path.exists(calendar_path):
            raise HTTPException(status_code=404, detail="사용자의 일정 데이터를 찾을 수 없습니다.")

        with open(calendar_path, 'r', encoding='utf-8') as f:
            events = json.load(f)

        return {"message": "일정 조회 성공", "events": events}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"일정 조회 실패: {str(e)}")

# 등록된 사용자 목록 조회
@app.get("/get-active-users")
async def get_active_users():
    try:
        if os.path.exists(ACTIVE_USERS_PATH):
            with open(ACTIVE_USERS_PATH, 'r', encoding='utf-8') as f:
                active_users = json.load(f)
        else:
            active_users = []

        return {"message": "활성 사용자 조회 성공", "active_users": active_users}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"활성 사용자 조회 실패: {str(e)}")

# 사용자 대화 기록 조회
@app.get("/get-chat-history")
async def get_chat_history(user_id: str):
    try:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        today = now.strftime("%Y%m%d")
        user_history_path = os.path.join("data", "faiss", user_id, "history", today)

        if not os.path.exists(user_history_path):
            return {"message": "대화 기록 없음", "chat_history": []}

        with open(user_history_path, 'r', encoding='utf-8') as f:
            chat_history = json.load(f)

        return {"message": "대화 기록 조회 성공", "chat_history": chat_history}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"대화 기록 조회 실패: {str(e)}")


@app.get("/get-tendency-mode") #(formatted 형태 조회)
async def get_tendency(user_id: str, mode: str = "formatted"):
    try:
        tendency_path = os.path.join("data", "faiss", f"{user_id}_tendency", "events.json")

        if not os.path.exists(tendency_path):
            raise HTTPException(status_code=404, detail="사용자의 성향 데이터를 찾을 수 없습니다.")

        with open(tendency_path, "r", encoding="utf-8") as f:
            user_tendency = json.load(f)

        # `mode`에 따라 반환할 데이터 결정
        if mode == "formatted":
            return {"message": "사용자 성향 조회 성공", "user_tendency": user_tendency["events"]}
        elif mode == "original":
            return {"message": "사용자 성향 조회 성공", "user_tendency": user_tendency["original_events"]}
        else:
            raise HTTPException(status_code=400, detail="올바른 mode 값을 입력하세요 (formatted/original)")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"사용자 성향 조회 실패: {str(e)}")


# 사용자 성향 조회 (Key 값 추가 시, 특정 키값에 대한 조회 가능)
@app.get("/get-tendency")
async def get_tendency(user_id: str, key: str = None):
    try:
        tendency_path = os.path.join("data", "faiss", f"{user_id}_tendency", "events.json")

        if not os.path.exists(tendency_path):
            raise HTTPException(status_code=404, detail="사용자의 성향 데이터를 찾을 수 없습니다.")

        with open(tendency_path, 'r', encoding='utf-8') as f:
            user_tendency = json.load(f)

        # 데이터가 'events' 배열 안에 존재하는 경우 첫 번째 항목 반환
        if isinstance(user_tendency, dict) and "original_events" in user_tendency:
            if isinstance(user_tendency["original_events"], list) and len(user_tendency["original_events"]) > 0:
                user_tendency_key = user_tendency["original_events"][0]  # 첫 번째 데이터 반환
            else:
                raise HTTPException(status_code=404, detail="성향 데이터가 존재하지 않습니다.")


            # 특정 키값만 조회하는 경우
            if key:
                if key in user_tendency_key["user_tendency"]:
                    return {"message": "사용자 성향 조회 성공", "value": user_tendency_key["user_tendency"][key]}
                else:
                    raise HTTPException(status_code=404, detail=f"'{key}'에 대한 데이터가 없습니다.")

            return {"message": "사용자 성향 조회 성공", "user_tendency": user_tendency_key["user_tendency"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"사용자 성향 조회 실패: {str(e)}")

# 사용자 성향 조회 API (특정 키값, 중첩된(traits) 세부키 키도 조회 가능)
@app.get("/get-tendency-sub")
async def get_tendency(user_id: str, key: str = "traits", sub_key: str = None):
    try:
        tendency_path = os.path.join("data", "faiss", f"{user_id}_tendency", "events.json")

        if not os.path.exists(tendency_path):
            raise HTTPException(status_code=404, detail="사용자의 성향 데이터를 찾을 수 없습니다.")

        with open(tendency_path, 'r', encoding='utf-8') as f:
            user_tendency = json.load(f)

            # 데이터가 'events' 배열 안에 존재하는 경우 첫 번째 항목 반환
            if isinstance(user_tendency, dict) and "original_events" in user_tendency:
                if isinstance(user_tendency["original_events"], list) and len(user_tendency["original_events"]) > 0:
                    user_tendency_key = user_tendency["original_events"][0]  # 첫 번째 데이터 반환
                else:
                    raise HTTPException(status_code=404, detail="성향 데이터가 존재하지 않습니다.")

        # 특정 키값 조회 (1차 필터링)
        if key:
            result = user_tendency_key["user_tendency"].get(key, None)

            if result is None:
                raise HTTPException(status_code=404, detail=f"'{key}'에 대한 데이터가 없습니다.")

            # 중첩된 키 (sub_key) 조회
            if sub_key:
                if isinstance(result, dict):
                    sub_value = result.get(sub_key, None)
                    if sub_value is None:
                        raise HTTPException(status_code=404, detail=f"'{key}' 안에 '{sub_key}' 데이터가 없습니다.")
                    return {"message": "사용자 성향 조회 성공", "value": sub_value}
                else:
                    raise HTTPException(status_code=400, detail=f"'{key}'는 중첩된 데이터가 아닙니다.")

            return {"message": "사용자 성향 조회 성공", "value": result}

        return {"message": "사용자 성향 조회 성공", "user_tendency": user_tendency["original_events"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"사용자 성향 조회 실패: {str(e)}")
