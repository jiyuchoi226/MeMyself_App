from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import chat

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Chat History API",
    description="채팅 히스토리 관리 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 환경에서는 구체적인 도메인 지정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, tags=["chat"])

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {"message": "채팅 히스토리 API에 오신 것을 환영합니다!"}

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작")

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료") 