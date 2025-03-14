from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')
vector_dim = 384  # 모델의 출력 차원
index = faiss.IndexFlatL2(vector_dim)

class Event(BaseModel):
    event_id: str
    summary: str
    description: str | None
    emotion_score: int
    timestamp: datetime
    location: str | None
    attendees: list[str] | None

@app.post("/store_vector")
async def store_vector(event: Event):
    # 텍스트 결합
    text = f"{event.summary} {event.description or ''} {event.location or ''}"
    
    # 텍스트를 벡터로 변환
    vector = model.encode([text])[0]
    
    # 감정 점수와 결합
    combined_vector = np.concatenate([vector, np.array([event.emotion_score])])
    
    # Faiss에 저장
    index.add(combined_vector.reshape(1, -1))
    
    return {"status": "success"}

@app.get("/similar_events/{event_id}")
async def find_similar_events(event_id: str):
    # 유사 일정 검색 로직
    pass

@app.get("/emotion_patterns")
async def analyze_emotion_patterns():
    # 감정 패턴 분석 로직
    pass 