from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class EventTime(BaseModel):
    dateTime: Optional[str]
    date: Optional[str]

class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: str = ""
    start: EventTime
    end: EventTime
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

@app.post("/sync_calendar")
async def sync_calendar(events: List[CalendarEvent]):
    try:
        # 일정들을 문서 형태로 변환
        documents = []
        for event in events:
            content = f"""
            일정: {event.summary}
            시간: {event.start.dateTime or event.start.date} ~ {event.end.dateTime or event.end.date}
            장소: {event.location or '없음'}
            설명: {event.description or '없음'}
            """
            documents.append(content)

        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        texts = text_splitter.create_documents(documents)

        # FAISS 인덱스 생성 및 저장
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)
        vectorstore.save_local("schedule")  # 'schedule'이라는 이름으로 저장

        return {"status": "success", "message": f"{len(events)}개의 일정이 저장되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_schedule(question: str):
    try:
        # FAISS 인덱스 로드
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local("schedule", embeddings)

        # 질문과 관련된 일정 검색
        docs = vectorstore.similarity_search(question, k=3)
        return {
            "relevant_events": [doc.page_content for doc in docs]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 