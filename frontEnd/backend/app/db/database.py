from typing import Dict, List, Any, Optional
import logging
import sqlite3
from contextlib import contextmanager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """데이터베이스 연결 및 쿼리 실행을 담당하는 클래스"""
    
    def __init__(self, db_path: str = "chat_history.db"):
        """
        데이터베이스 연결 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 채팅 메시지 테이블 생성
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_user BOOLEAN NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
                ''')
                conn.commit()
                logger.info("데이터베이스 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # 결과를 딕셔너리 형태로 반환하도록 설정
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            logger.error(f"데이터베이스 연결 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        SQL 쿼리 실행 및 결과 반환
        
        Args:
            sql: SQL 쿼리문
            params: 쿼리 파라미터
            
        Returns:
            List[Dict]: 쿼리 결과 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                results = cursor.fetchall()
                # Row 객체를 딕셔너리로 변환
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"쿼리 실행 오류: {sql}, {params}, {e}")
            return []
    
    def execute(self, sql: str, params: tuple = ()) -> bool:
        """
        SQL 실행 (INSERT, UPDATE, DELETE)
        
        Args:
            sql: SQL 쿼리문
            params: 쿼리 파라미터
            
        Returns:
            bool: 성공 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                logger.info(f"SQL 실행 성공: {sql}")
                return True
        except Exception as e:
            logger.error(f"SQL 실행 오류: {sql}, {params}, {e}")
            return False

# 데이터베이스 인스턴스 생성
_db_instance = None

def get_db_connection() -> Database:
    """
    데이터베이스 연결 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        Database: 데이터베이스 연결 객체
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance 