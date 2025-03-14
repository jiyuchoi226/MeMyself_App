import os
import json
import networkx as nx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Any, Tuple
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings
from openai import OpenAI
import traceback

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableConfig
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

# 1. 기본 데이터 로더 인터페이스
class DataLoader:
    """데이터 로드 및 기본 분석 기능을 제공하는 기본 클래스"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_path = "data/faiss"
    
    def load_calendar_events(self):
        """일정 데이터 로드"""
        try:
            # 일정 JSON 파일 경로
            calendar_path = os.path.join(
                self.base_path, self.user_id, "schedule", "events.json"
            )
            
            if not os.path.exists(calendar_path):
                print(f"캘린더 파일을 찾을 수 없음: {calendar_path}")
                return []
            
            # 일정 JSON 파일 읽기
            with open(calendar_path, "r", encoding="utf-8") as f:
                events_data = json.load(f)
            
            # events 키의 데이터 추출
            if "events" in events_data:
                events = events_data["events"]
            else:
                events = events_data
            
            # 각 이벤트 파싱
            parsed_events = []
            for event in events:
                # 이미 객체인 경우
                if isinstance(event, dict):
                    parsed_events.append(event)
                # 문자열인 경우 파싱
                elif isinstance(event, str):
                    event_dict = {}
                    event_lines = event.split("\n")
                    for line in event_lines:
                        if ": " in line:
                            key, value = line.split(": ", 1)
                            event_dict[key.strip()] = value.strip()
                    parsed_events.append(event_dict)
            
            # 이전 주 날짜 계산
            week_dates = self._get_previous_week_dates()
            start_date = week_dates["start_date"]
            end_date = week_dates["end_date"]
            
            # 지난 주에 해당하는 일정만 필터링
            filtered_events = []
            for event in parsed_events:
                # 시작 시간 확인
                start_time = event.get("시작", "")
                if not start_time or not isinstance(start_time, str):
                    continue
                    
                # 날짜 추출 (YYYY-MM-DD 형식이 있을 경우)
                event_date = ""
                if "T" in start_time:
                    event_date = start_time.split("T")[0].replace("-", "")
                
                # 시작 날짜가 지난 주 범위에 속하면 필터링
                if event_date and start_date <= event_date <= end_date:
                    filtered_events.append(event)
            
            return filtered_events
            
        except Exception as e:
            print(f"일정 데이터 로드 중 오류: {str(e)}")
            traceback.print_exc()
            return []
        
    def load_chat_history(self):
        """대화 기록 로드"""
        try:
            # 이전 주 날짜 계산
            week_dates = self._get_previous_week_dates()
            start_date = week_dates["start_date"]
            end_date = week_dates["end_date"]
            
            # 대화 기록 폴더 경로
            history_path = os.path.join(self.base_path, self.user_id, "history")
            
            if not os.path.exists(history_path):
                print(f"대화 기록 폴더를 찾을 수 없음: {history_path}")
                return []
            
            # 모든 대화 기록 파일 찾기
            chat_histories = []
            for filename in os.listdir(history_path):
                file_path = os.path.join(history_path, filename, "conversations.json")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        conversation_data = json.load(f)
                        conversations = conversation_data.get("conversations", [])
                        
                        # 이전 주 일정에 관한 대화만 필터링
                        filtered_conversations = []
                        for conv in conversations:
                            event_info = conv.get("event_info", {})
                            event_start = event_info.get("start", "")
                            
                            # 이벤트 날짜 추출 (YYYY-MM-DD 형식)
                            event_date = ""
                            if event_start and isinstance(event_start, str) and "T" in event_start:
                                event_date = event_start.split("T")[0].replace("-", "")
                            
                            # 이전 주 날짜에 해당하는 일정에 관한 대화만 포함
                            if event_date and start_date <= event_date <= end_date:
                                filtered_conversations.append(conv)
                        
                        chat_histories.extend(filtered_conversations)
            
            return chat_histories
            
        except Exception as e:
            print(f"대화 기록 로드 중 오류: {str(e)}")
            traceback.print_exc()
            return []
        
    def load_user_tendency(self):
        """사용자 성향 데이터 로드"""
        try:
            # 사용자 성향 데이터 파일 경로
            tendency_path = os.path.join(self.base_path, self.user_id, "tendency", "events.json")
            
            if not os.path.exists(tendency_path):
                print(f"사용자 성향 파일을 찾을 수 없음: {tendency_path}")
                return {}
            
            # 사용자 성향 데이터 파일 읽기
            with open(tendency_path, "r", encoding="utf-8") as f:
                tendency_data = json.load(f)
            
            return tendency_data
            
        except Exception as e:
            print(f"사용자 성향 데이터 로드 중 오류: {str(e)}")
            return {}
        
    def analyze_emotion_data(self, events):
        """감정 데이터 분석"""
        try:
            # 감정 점수가 있는 이벤트 필터링
            events_with_emotion = []
            for event in events:
                emotion_score = event.get("감정 점수", None)
                if emotion_score is not None and emotion_score != "":
                    try:
                        score = int(emotion_score)
                        if 1 <= score <= 5:  # 1-5 사이의 값만 유효한 감정 점수로 간주
                            events_with_emotion.append({"event": event, "score": score})
                    except (ValueError, TypeError):
                        pass
            
            if not events_with_emotion:
                return {"avg_emotion": 0, "emotion_counts": {}, "highest": None, "lowest": None}
            
            # 감정 점수 통계 계산
            total_score = sum(item["score"] for item in events_with_emotion)
            avg_emotion = total_score / len(events_with_emotion)
            
            # 감정 점수별 개수
            emotion_counts = {}
            for item in events_with_emotion:
                score = item["score"]
                emotion_counts[score] = emotion_counts.get(score, 0) + 1
            
            # 가장 높은/낮은 감정 점수 이벤트 찾기
            highest = max(events_with_emotion, key=lambda x: x["score"])
            lowest = min(events_with_emotion, key=lambda x: x["score"])
            
            return {
                "avg_emotion": avg_emotion,
                "emotion_counts": emotion_counts,
                "highest": highest,
                "lowest": lowest
            }
        except Exception as e:
            print(f"감정 데이터 분석 중 오류: {str(e)}")
            traceback.print_exc()
            return {"avg_emotion": 0, "emotion_counts": {}, "highest": None, "lowest": None}
        
    def analyze_activity_patterns(self, events):
        """활동 패턴 분석"""
        try:
            # 활동 유형별 분류
            activity_types = {}
            for event in events:
                event_type = event.get("타입", "기타")
                if event_type not in activity_types:
                    activity_types[event_type] = []
                activity_types[event_type].append(event)
            
            # 시간대별 활동 분류
            time_slots = {
                "아침(06-09)": [], "오전(09-12)": [], 
                "오후(12-18)": [], "저녁(18-22)": [], "밤(22-06)": []
            }
            
            for event in events:
                start_time = event.get("시작", "")
                if "T" in start_time:
                    try:
                        hour = int(start_time.split("T")[1][:2])
                        
                        if 6 <= hour < 9:
                            time_slots["아침(06-09)"].append(event)
                        elif 9 <= hour < 12:
                            time_slots["오전(09-12)"].append(event)
                        elif 12 <= hour < 18:
                            time_slots["오후(12-18)"].append(event)
                        elif 18 <= hour < 22:
                            time_slots["저녁(18-22)"].append(event)
                        else:
                            time_slots["밤(22-06)"].append(event)
                    except:
                        pass
            
            # 요일별 활동 분류
            weekday_activities = {"월": [], "화": [], "수": [], "목": [], "금": [], "토": [], "일": []}
            weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
            
            for event in events:
                start_time = event.get("시작", "")
                if "T" in start_time:
                    date_part = start_time.split("T")[0]
                    try:
                        date_obj = datetime.fromisoformat(date_part)
                        weekday = weekday_names[date_obj.weekday()]
                        weekday_activities[weekday].append(event)
                    except:
                        continue
            
            # 반복 일정 분석
            recurring_events = [event for event in events if event.get("반복", "반복정보 없음") != "반복정보 없음"]
            
            # 일정 제목 기반 키워드 분석
            keywords = {}
            for event in events:
                title = event.get("일정", "")
                for word in title.split():
                    if len(word) > 1:
                        keywords[word] = keywords.get(word, 0) + 1
            
            # 상위 키워드 추출
            top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "activity_types": activity_types,
                "time_slots": time_slots,
                "weekday_activities": weekday_activities,
                "recurring_events": recurring_events,
                "top_keywords": top_keywords
            }
            
        except Exception as e:
            print(f"활동 패턴 분석 중 오류: {str(e)}")
            traceback.print_exc()
            return {}
        
    def analyze_chat_content(self, chat_history):
        """대화 내용 분석"""
        try:
            if not chat_history:
                return {"keywords": {}, "topics": []}
            
            # 사용자 메시지 추출
            user_messages = []
            for chat in chat_history:
                user_answer = chat.get("user_answer", "")
                if user_answer:
                    user_messages.append(user_answer)
            
            # 키워드 빈도 분석
            keywords = {}
            for message in user_messages:
                for word in message.split():
                    if len(word) > 1:
                        keywords[word] = keywords.get(word, 0) + 1
            
            # 상위 키워드 추출
            top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 주제 및 감정 키워드 분석 
            topics = []
            topic_indicators = {
                "업무": ["일", "업무", "회사", "프로젝트", "미팅", "클래스", "이메일"],
                "건강": ["운동", "건강", "걷기", "산책", "식단"],
                "여가": ["여행", "영화", "휴식", "허니문", "인테리어"],
                "창작": ["유튜브", "썸네일", "편집", "스크립트", "콘텐츠"],
                "인간관계": ["만남", "친구", "가족", "대화"]
            }
            
            for topic, indicators in topic_indicators.items():
                for message in user_messages:
                    message_lower = message.lower()
                    if any(indicator in message_lower for indicator in indicators):
                        topics.append(topic)
                        break
            
            # 중복 제거
            topics = list(set(topics))
            
            return {
                "keywords": dict(top_keywords),
                "topics": topics,
                "message_count": len(user_messages)
            }
            
        except Exception as e:
            print(f"대화 내용 분석 중 오류: {str(e)}")
            traceback.print_exc()
            return {"keywords": {}, "topics": []}
        
    def get_data_for_report(self):
        """보고서 생성을 위한 기본 데이터 준비"""
        events = self.load_calendar_events()
        chat_history = self.load_chat_history()
        user_tendency = self.load_user_tendency()
        
        # 데이터 분석
        emotion_analysis = self.analyze_emotion_data(events)
        activity_analysis = self.analyze_activity_patterns(events)
        chat_analysis = self.analyze_chat_content(chat_history)
        
        return {
            "events": events,
            "chat_history": chat_history,
            "user_tendency": user_tendency,
            "emotion_analysis": emotion_analysis,
            "activity_analysis": activity_analysis,
            "chat_analysis": chat_analysis
        }
    
    def _get_previous_week_dates(self) -> Dict[str, str]:
        """지난 주의 시작일과 종료일 계산"""
        today = datetime.now(ZoneInfo("Asia/Seoul"))
        end_of_previous_week = today - timedelta(days=today.weekday() + 1)
        start_of_previous_week = end_of_previous_week - timedelta(days=6)

        return {
            "start_date": start_of_previous_week.strftime("%Y%m%d"),
            "end_date": end_of_previous_week.strftime("%Y%m%d"),
        }
        
# 2. Vector RAG 시스템
class VectorRAGDataLoader(DataLoader):
    """벡터 검색 기반 RAG 시스템 구현"""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        try:
            # 벡터 검색 모델 초기화 (UpstageEmbeddings 등)
            self.embeddings = UpstageEmbeddings(
                model="embedding-query", api_key=os.getenv("UPSTAGE_API_KEY")
            )
        except Exception as e:
            print(f"임베딩 모델 초기화 오류: {str(e)}")
            # 폴백 임베딩 모델 사용 시도
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                print("HuggingFace 임베딩 모델로 폴백")
            except Exception as fallback_error:
                print(f"폴백 임베딩 모델 초기화 실패: {str(fallback_error)}")
                # 로그용 임베딩 모델 (실제 사용은 안됨)
                self.embeddings = None
    
    def create_vector_index(self, documents):
        """문서를 벡터화하여 인덱스 생성"""
        try:
            texts = [doc.get("text", "") for doc in documents if "text" in doc]
            metadatas = [{"source": doc.get("source", ""), "id": doc.get("id", "")} for doc in documents if "text" in doc]
            
            if not texts:
                print("인덱스 생성을 위한 텍스트 문서가 없습니다.")
                return
            
            # FAISS 벡터 저장소 생성
            vectorstore = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
            
            # 인덱스 저장
            index_path = os.path.join(self.base_path, self.user_id, "faiss_index")
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            vectorstore.save_local(index_path)
            
            print(f"FAISS 인덱스 생성 완료: {len(texts)}개 문서")
        except Exception as e:
            print(f"벡터 인덱스 생성 중 오류: {str(e)}")
            traceback.print_exc()
    
    def query_vector_store(self, query_text, top_k=5):
        """벡터 검색 수행"""
        try:
            # FAISS 인덱스 로드
            index_path = os.path.join(self.base_path, self.user_id, "faiss_index")
            if not os.path.exists(index_path):
                print(f"FAISS 인덱스를 찾을 수 없음: {index_path}")
                return []
            
            try:
                # 안전한 역직렬화 옵션 명시적 사용
                vectorstore = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as load_error:
                print(f"FAISS 인덱스 로드 오류 (안전 모드): {str(load_error)}")
                return []
            
            # 벡터 유사도 검색 수행
            results = vectorstore.similarity_search(query_text, k=top_k)
            
            # 결과 포맷팅
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("score", 0)
                })
            
            return formatted_results
        except Exception as e:
            print(f"벡터 검색 중 오류: {str(e)}")
            traceback.print_exc()
            return []
        
    def get_vector_data_for_report(self):
        """벡터 RAG 데이터 준비"""
        # 기본 데이터 수집 (기존 메서드 활용)
        return super().get_data_for_report()
    
    def _expand_query(self, query_text):
        """쿼리 확장 - 더 나은 검색 결과를 위한 쿼리 개선"""
   
        # 향후 개선점점: 유의어 추가, 주요 키워드 강조 등
        expanded_query = query_text
        
        # 일정 관련 키워드 
        calendar_keywords = ["일정", "미팅", "약속", "회의", "일", "이벤트", "활동"]
        for keyword in calendar_keywords:
            if keyword in query_text.lower() and keyword not in expanded_query:
                expanded_query += f" {keyword}"
        
        # 감정 관련 키워드 
        emotion_keywords = ["기분", "감정", "느낌", "좋았던", "나빴던", "행복", "슬픔", "화남", "불안"]
        for keyword in emotion_keywords:
            if keyword in query_text.lower() and keyword not in expanded_query:
                expanded_query += f" {keyword}"
        
        return expanded_query
    
    def prepare_data(self):
        """벡터 검색을 위한 데이터 준비"""
        # 일정 및 대화 데이터 로드
        events = self.load_calendar_events()
        chat_history = self.load_chat_history()
        
        # 벡터 인덱싱을 위한 문서 변환 - 개선된 버전
        documents = []
        
        # 일정 데이터를 문서로 변환 (개선된 인덱싱)
        for event in events:
            event_id = event.get("id", f"event_{hash(str(event))}")
            
            # 일정 정보를 더 잘 표현하는 텍스트 구성
            event_text = f"일정 제목: {event.get('일정', '')}\n"
            event_text += f"시작 시간: {event.get('시작', '')}\n"
            event_text += f"종료 시간: {event.get('종료', '')}\n"
            event_text += f"일정 유형: {event.get('타입', '')}\n"
            
            # 감정 점수 정보 추가
            emotion_score = event.get("감정 점수", "")
            if emotion_score:
                event_text += f"감정 점수: {emotion_score}\n"
                
                # 감정 설명 추가
                if isinstance(emotion_score, (int, float)) or (isinstance(emotion_score, str) and emotion_score.isdigit()):
                    score = int(float(emotion_score))
                    if score == 1:
                        event_text += "감정 상태: 매우 부정적\n"
                    elif score == 2:
                        event_text += "감정 상태: 부정적\n"
                    elif score == 3:
                        event_text += "감정 상태: 보통\n"
                    elif score == 4:
                        event_text += "감정 상태: 긍정적\n"
                    elif score == 5:
                        event_text += "감정 상태: 매우 긍정적\n"
            
            # 키워드 추출 및 추가
            event_title = event.get('일정', '')
            if event_title:
                keywords = [word for word in event_title.split() if len(word) > 1]
                if keywords:
                    event_text += f"키워드: {', '.join(keywords)}\n"
            
            documents.append({
                "id": event_id,
                "source": "event",
                "text": event_text
            })
        
        # 대화 데이터를 문서로 변환 
        for chat in chat_history:
            chat_id = chat.get("id", f"chat_{hash(str(chat))}")
            
            # 대화 컨텍스트를 더 풍부하게 구성
            chat_text = f"사용자 메시지: {chat.get('user_answer', '')}\n"
            
            # 관련 이벤트 정보 추가
            event_info = chat.get('event_info', {})
            if event_info:
                chat_text += f"관련 일정: {event_info.get('summary', '')}\n"
                chat_text += f"일정 시간: {event_info.get('start', '')}\n"
                
            # 감정 관련 키워드 추출 및 추가
            user_answer = chat.get('user_answer', '')
            emotion_keywords = ["기쁨", "행복", "슬픔", "화남", "불안", "만족", "실망", "흥분", "지루함", "기대"]
            found_emotions = []
            for keyword in emotion_keywords:
                if keyword in user_answer:
                    found_emotions.append(keyword)
            
            if found_emotions:
                chat_text += f"감정 키워드: {', '.join(found_emotions)}\n"
            
            documents.append({
                "id": chat_id,
                "source": "chat",
                "text": chat_text
            })
        
        # 벡터 인덱스 생성
        self.create_vector_index(documents)
    
    def get_rag_results(self, query_text, top_k=5):
        """벡터 검색 기반 RAG 결과 반환 - 강화된 컨텍스트 구성"""
        # 벡터 검색 수행
        search_results = self.query_vector_store(query_text, top_k)
        
        # 결과가 없는 경우 기본 데이터 반환
        if not search_results:
            return []
        
        # RAG 컨텍스트 구성 - 검색 결과를 의미 있게 구조화
        rag_context = []
        
        for item in search_results:
            content = item["content"]
            score = item["score"]
            metadata = item["metadata"]
            source_type = metadata.get("source", "unknown")
            
            # 출처에 따라 컨텍스트 구조화
            if source_type == "event":
                # 일정 정보 구조화
                event_info = self._parse_event_content(content)
                event_info["relevance_score"] = score
                event_info["source_type"] = "event"
                rag_context.append(event_info)
            elif source_type == "chat":
                # 대화 정보 구조화
                chat_info = self._parse_chat_content(content)
                chat_info["relevance_score"] = score
                chat_info["source_type"] = "chat"
                rag_context.append(chat_info)
        
        return rag_context
    
    def _parse_event_content(self, content):
        """이벤트 컨텐츠 파싱"""
        event_info = {}
        for line in content.split('\n'):
            if ': ' in line:
                key, value = line.split(': ', 1)
                clean_key = key.strip().lower().replace(' ', '_')
                event_info[clean_key] = value.strip()
        return event_info
    
    def _parse_chat_content(self, content):
        """대화 컨텐츠 파싱"""
        chat_info = {}
        for line in content.split('\n'):
            if ': ' in line:
                key, value = line.split(': ', 1)
                clean_key = key.strip().lower().replace(' ', '_')
                chat_info[clean_key] = value.strip()
        return chat_info


# 3. Graph RAG 시스템 
class GraphRAGDataLoader(DataLoader):
    """그래프 검색 기반 RAG 시스템 구현 """
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        # 그래프 데이터베이스 초기화
        self.graph = nx.DiGraph()
        self.graph_built = False

    def get_graph_data_for_report(self):
        """그래프 RAG 데이터 준비"""
        # 기본 데이터 수집
        base_data = super().get_data_for_report()
        
        # 그래프 특화 분석 데이터 추가
        graph_stats = {
            "node_count": len(self.graph.nodes) if self.graph else 0,
            "edge_count": len(self.graph.edges) if self.graph else 0,
            "keyword_count": len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'keyword']),
            "event_count": len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'event']),
            "chat_count": len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'chat']),
        }
        
        event_patterns = self.extract_event_patterns()
        behavioral_insights = self.extract_user_behavioral_insights()
        correlations = self.identify_correlations()
        
        # 데이터 병합
        return {
            **base_data,
            "graph_stats": graph_stats,
            "event_patterns": event_patterns,
            "behavioral_insights": behavioral_insights,
            "correlations": correlations
        }
    
    def build_knowledge_graph(self):
        """지식 그래프 구축 - 개선된 버전"""
        try:
            if self.graph_built:
                print("그래프가 이미 구축되어 있습니다.")
                return
                
            # 1. 일정 데이터 로드
            events = self.load_calendar_events()
            
            # 2. 대화 기록 로드
            chat_history = self.load_chat_history()
            
            # 3. 그래프 노드 및 관계 생성
            # 사용자 노드 생성
            self.graph.add_node(self.user_id, type="user")
            
            # 일정 노드 생성 및 관계 설정
            for event in events:
                event_id = event.get("id", f"event_{hash(str(event))}")
                event_date = ""
                start_time = event.get("시작", "")
                if "T" in start_time:
                    event_date = start_time.split("T")[0]
                
                # 더 많은 메타데이터 포함
                self.graph.add_node(
                    event_id, 
                    type="event", 
                    data=event,
                    title=event.get("일정", ""),
                    event_type=event.get("타입", ""),
                    date=event_date,
                    search_text=self._prepare_search_text(event)  # 검색용 텍스트 추가
                )
                
                # 사용자와 일정의 관계
                self.graph.add_edge(self.user_id, event_id, relation="HAS_EVENT")
                
                # 일정 키워드 추출 및 연결 (개선된 키워드 추출)
                event_title = event.get("일정", "")
                if event_title:
                    # 간단한 키워드 추출
                    keywords = [word for word in event_title.split() if len(word) > 1]
                    
                    # 타입 정보에서 추가 키워드 추출
                    event_type = event.get("타입", "")
                    if event_type and event_type not in keywords:
                        keywords.append(event_type)
                    
                    # 키워드 노드 생성 및 연결
                    for keyword in keywords:
                        keyword_id = f"keyword_{keyword}"
                        if not self.graph.has_node(keyword_id):
                            self.graph.add_node(keyword_id, type="keyword", value=keyword)
                        self.graph.add_edge(event_id, keyword_id, relation="HAS_KEYWORD")
                        
                        # 동의어 추가 (간단한 예시)
                        synonyms = self._get_synonyms(keyword)
                        for synonym in synonyms:
                            syn_id = f"keyword_{synonym}"
                            if not self.graph.has_node(syn_id):
                                self.graph.add_node(syn_id, type="keyword", value=synonym)
                            # 동의어 관계 추가
                            self.graph.add_edge(keyword_id, syn_id, relation="IS_SYNONYM")
                
                # 일정과 감정 연결 (개선된 감정 모델링)
                emotion_score = event.get("감정 점수", None)
                if emotion_score is not None and emotion_score != "":
                    try:
                        score = int(emotion_score)
                        emotion_id = f"emotion_{score}"
                        
                        # 감정 노드가 없다면 생성
                        if not self.graph.has_node(emotion_id):
                            # 감정 레이블 추가
                            emotion_label = "중립"
                            if score == 1:
                                emotion_label = "매우 부정적"
                            elif score == 2:
                                emotion_label = "부정적"
                            elif score == 3:
                                emotion_label = "중립"
                            elif score == 4:
                                emotion_label = "긍정적"
                            elif score == 5:
                                emotion_label = "매우 긍정적"
                            
                            self.graph.add_node(
                                emotion_id, 
                                type="emotion", 
                                value=score,
                                label=emotion_label
                            )
                        
                        # 감정 관계 추가
                        self.graph.add_edge(event_id, emotion_id, relation="HAS_EMOTION", weight=1.0)
                        
                        # 이벤트의 감정 수준에 따른 관계 강화
                        if score >= 4:  # 긍정적 감정
                            self.graph.add_edge(
                                self.user_id, event_id, 
                                relation="ENJOYS", 
                                weight=score/5.0
                            )
                        elif score <= 2:  # 부정적 감정
                            self.graph.add_edge(
                                self.user_id, event_id, 
                                relation="DISLIKES", 
                                weight=(6-score)/5.0
                            )
                    except (ValueError, TypeError):
                        pass
                        
                # 일정 날짜 노드 추가
                if event_date:
                    date_id = f"date_{event_date}"
                    if not self.graph.has_node(date_id):
                        self.graph.add_node(date_id, type="date", value=event_date)
                    self.graph.add_edge(event_id, date_id, relation="ON_DATE")
            
            # 대화 노드 생성 및 관계 설정 (개선된 대화 모델링)
            for chat in chat_history:
                chat_id = chat.get("id", f"chat_{hash(str(chat))}")
                
                # 대화 메타데이터 추가
                user_answer = chat.get("user_answer", "")
                self.graph.add_node(
                    chat_id, 
                    type="chat", 
                    data=chat,
                    text=user_answer,
                    search_text=user_answer  # 검색용 텍스트
                )
                
                # 사용자와 대화의 관계
                self.graph.add_edge(self.user_id, chat_id, relation="HAS_CHAT")
                
                # 대화와 관련 일정 연결
                event_info = chat.get("event_info", {})
                event_id = event_info.get("id", "")
                if event_id and event_id in self.graph:
                    self.graph.add_edge(chat_id, event_id, relation="ABOUT_EVENT", weight=1.5)  # 강한 연결
                
                # 대화 키워드 추출 및 연결 (개선된 키워드 추출)
                if user_answer:
                    # 간단한 키워드 추출
                    keywords = [word for word in user_answer.split() if len(word) > 1]
                    
                    # 감정 키워드 추출
                    emotion_keywords = ["행복", "슬픔", "기쁨", "화남", "불안", "만족", "실망", "지루함", "기대", "좋았", "나빴"]
                    for emotion in emotion_keywords:
                        if emotion in user_answer and emotion not in keywords:
                            keywords.append(emotion)
                    
                    # 키워드 노드 생성 및 연결
                    for keyword in keywords:
                        keyword_id = f"keyword_{keyword}"
                        if not self.graph.has_node(keyword_id):
                            self.graph.add_node(keyword_id, type="keyword", value=keyword)
                        
                        # 대화-키워드 관계 추가
                        self.graph.add_edge(chat_id, keyword_id, relation="MENTIONS_KEYWORD", weight=1.0)
                        
                        # 키워드 간 관계 추가 (co-occurrence)
                        for other_keyword in keywords:
                            if keyword != other_keyword:
                                other_id = f"keyword_{other_keyword}"
                                if self.graph.has_node(other_id):
                                    # 이미 관계가 있으면 가중치 증가
                                    if self.graph.has_edge(keyword_id, other_id):
                                        self.graph[keyword_id][other_id]["weight"] += 0.5
                                    else:
                                        self.graph.add_edge(keyword_id, other_id, relation="CO_OCCURS_WITH", weight=1.0)
            
            # 그래프 구축 완료 플래그 설정
            self.graph_built = True
            print(f"지식 그래프 구축 완료: 노드 {len(self.graph.nodes)} 개, 엣지 {len(self.graph.edges)} 개")
            return
            
        except Exception as e:
            print(f"지식 그래프 구축 중 오류: {str(e)}")
            traceback.print_exc()
            return
    
    def _prepare_search_text(self, event):
        """검색을 위한 텍스트 준비"""
        search_text = ""
        
        # 일정 제목
        title = event.get("일정", "")
        if title:
            search_text += f"{title} "
        
        # 일정 타입
        event_type = event.get("타입", "")
        if event_type:
            search_text += f"{event_type} "
        
        # 기타 메타데이터
        for key, value in event.items():
            if key not in ["일정", "타입"] and isinstance(value, str):
                search_text += f"{value} "
        
        return search_text.strip()
    
    def _get_synonyms(self, keyword):
        """단어의 동의어 목록 반환 """

        synonyms_dict = {
            "일": ["업무", "작업", "태스크", "할일"],
            "미팅": ["회의", "미팅", "만남", "약속"],
            "여행": ["여행", "여정", "트립"],
            "운동": ["운동", "헬스", "피트니스", "트레이닝"],
            "식사": ["식사", "밥", "점심", "저녁", "아침", "브런치", "식단"],
        }
        
        # 키워드에 대한 동의어 찾기
        for key, values in synonyms_dict.items():
            if keyword in values:
                return [syn for syn in values if syn != keyword]
        
        # 동의어가 없으면 빈 리스트 반환
        return []
    
    def query_graph(self, query_text, top_k=5):
        """그래프 검색 수행 - 개선된 버전"""
        try:
            if not self.graph_built:
                self.build_knowledge_graph()
                
            # 쿼리 확장 및 전처리
            expanded_query = self._expand_query(query_text)
            keywords = self._extract_keywords(expanded_query)
            
            # 관련 노드 찾기 위한 다단계 검색 전략
            relevant_nodes = self._find_relevant_nodes(keywords)
            
            # 관련 이벤트 찾기 
            event_nodes = self._find_relevant_events(relevant_nodes, keywords)
            
            # 검색 결과가 적으면 그래프 탐색 확장
            if len(event_nodes) < top_k:
                event_nodes.update(self._expand_graph_search(keywords, top_k - len(event_nodes)))
            
            # 결과 가공
            results = self._format_search_results(event_nodes)
            
            # 관련성 점수에 따라 정렬
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return results[:top_k]
                
        except Exception as e:
            print(f"그래프 쿼리 중 오류: {str(e)}")
            traceback.print_exc()
            return []
    
    def _expand_query(self, query_text):
        """쿼리 확장 - 더 나은 검색 결과를 위한 쿼리 개선"""
        # 기본적인 키워드 확장
        expanded_query = query_text
        
        # 일정 관련 키워드 추가
        calendar_keywords = ["일정", "미팅", "약속", "회의", "일", "이벤트", "활동"]
        for keyword in calendar_keywords:
            if keyword in query_text.lower() and keyword not in expanded_query:
                expanded_query += f" {keyword}"
        
        # 감정 관련 키워드 추가
        emotion_keywords = ["기분", "감정", "느낌", "좋았던", "나빴던", "행복", "슬픔", "화남", "불안"]
        for keyword in emotion_keywords:
            if keyword in query_text.lower() and keyword not in expanded_query:
                expanded_query += f" {keyword}"
        
        return expanded_query
    
    def _extract_keywords(self, query_text):
        """쿼리에서 의미 있는 키워드 추출"""
        # 간단한 키워드 추출 - 실제 구현에서는 NLP 기법 사용 가능
        words = query_text.split()
        
        # 길이 2 이상의 의미 있는 단어만 키워드로 추출
        keywords = [word.lower() for word in words if len(word) > 1]
        
        return keywords
    
    def _find_relevant_nodes(self, keywords):
        """관련 노드 찾기"""
        relevant_nodes = set()
        
        # 1. 직접 일치 검색
        for keyword in keywords:
            keyword_id = f"keyword_{keyword}"
            
            if keyword_id in self.graph:
                relevant_nodes.add(keyword_id)
                
                # 동의어 노드도 포함
                for successor in self.graph.successors(keyword_id):
                    if self.graph.nodes[successor].get('type') == 'keyword' and \
                       self.graph.get_edge_data(keyword_id, successor).get('relation') == 'IS_SYNONYM':
                        relevant_nodes.add(successor)
        
        # 2. 부분 문자열 검색
        if len(relevant_nodes) < 2:  # 직접 일치 결과가 부족한 경우
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'keyword':
                    node_value = attrs.get('value', '').lower()
                    
                    for keyword in keywords:
                        if keyword in node_value or node_value in keyword:
                            relevant_nodes.add(node)
                            break
        
        return relevant_nodes
    
    def _find_relevant_events(self, keyword_nodes, query_keywords):
        """관련 이벤트 노드 찾기"""
        event_nodes = set()
        event_relevance = {}  # 이벤트 관련성 점수 추적
        
        # 1. 키워드 노드와 직접 연결된 이벤트 찾기
        for keyword_node in keyword_nodes:
            for predecessor in self.graph.predecessors(keyword_node):
                if self.graph.nodes[predecessor].get('type') == 'event':
                    event_nodes.add(predecessor)
                    
                    # 관련성 점수 업데이트 (키워드 일치 가중치)
                    current_score = event_relevance.get(predecessor, 0)
                    edge_weight = self.graph.get_edge_data(predecessor, keyword_node).get('weight', 1.0)
                    event_relevance[predecessor] = current_score + 1.0 * edge_weight
        
        # 2. 키워드가 이벤트 텍스트에 포함된 경우 찾기
        if len(event_nodes) < 5:  # 직접 연결 결과가 부족한 경우
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    search_text = attrs.get('search_text', '').lower()
                    if not search_text:
                        title = attrs.get('title', '').lower()
                        event_type = attrs.get('event_type', '').lower()
                        search_text = f"{title} {event_type}"
                    
                    match_count = 0
                    for keyword in query_keywords:
                        if keyword in search_text:
                            match_count += 1
                    
                    if match_count > 0:
                        event_nodes.add(node)
                        # 직접 텍스트 일치 가중치 (약간 낮게 설정)
                        event_relevance[node] = event_relevance.get(node, 0) + match_count * 0.8
        
        # 3. 감정 기반 검색
        emotion_keywords = ["기분", "감정", "느낌", "행복", "슬픔", "좋은", "나쁜"]
        emotion_query = any(keyword in query_keywords for keyword in emotion_keywords)
        
        if emotion_query:
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    # 감정 노드와 연결된 이벤트 찾기
                    for successor in self.graph.successors(node):
                        if self.graph.nodes[successor].get('type') == 'emotion':
                            event_nodes.add(node)
                            
                            # 감정 점수 기반으로 관련성 가중치 부여
                            emotion_value = self.graph.nodes[successor].get('value', 3)
                            emotion_weight = abs(emotion_value - 3) * 0.3  # 중립에서 멀수록 가중치 증가
                            event_relevance[node] = event_relevance.get(node, 0) + 0.5 + emotion_weight
        
        # 이벤트 노드와 관련성 점수 함께 반환
        return {node: event_relevance.get(node, 0.5) for node in event_nodes}
    
    def _expand_graph_search(self, keywords, limit=3):
        """그래프 확장 검색 - 결과가 부족할 때 사용"""
        additional_events = {}
        
        # 1. 그래프 중심성 기반 중요 이벤트 찾기
        if self.graph.number_of_nodes() > 0:
            try:
                # 페이지랭크 알고리즘으로 중요 노드 계산
                pagerank = nx.pagerank(self.graph, weight='weight')
                
                # 이벤트 노드만 필터링하고 중요도 순 정렬
                event_pageranks = {node: rank for node, rank in pagerank.items() 
                                 if self.graph.nodes[node].get('type') == 'event'}
                
                top_events = sorted(event_pageranks.items(), key=lambda x: x[1], reverse=True)[:limit]
                
                for node, rank in top_events:
                    additional_events[node] = 0.3 * rank  # 그래프 중심성 기반 낮은 관련성 점수
            except:
                pass
        
        # 2. 최근 이벤트 추가 (날짜 기반)
        recent_events = []
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get('type') == 'event':
                date = attrs.get('date', '')
                if date:
                    recent_events.append((node, date))
        
        # 최근 날짜순 정렬
        recent_events.sort(key=lambda x: x[1], reverse=True)
        
        # 최근 이벤트 추가 (낮은 관련성 점수)
        for node, _ in recent_events[:limit]:
            if node not in additional_events:
                additional_events[node] = 0.2  # 최신성 기반 매우 낮은 관련성 점수
        
        return additional_events
    
    def _format_search_results(self, event_nodes_with_scores):
        """검색 결과 포맷팅"""
        results = []
        
        for node, relevance_score in event_nodes_with_scores.items():
            # 이벤트 데이터 추출
            event_data = self.graph.nodes[node].get('data', {})
            
            # 감정 점수 찾기
            emotion_score = None
            emotion_label = None
            for successor in self.graph.successors(node):
                if self.graph.nodes[successor].get('type') == 'emotion':
                    emotion_score = self.graph.nodes[successor].get('value')
                    emotion_label = self.graph.nodes[successor].get('label')
                    break
            
            # 관련 키워드 추출
            related_keywords = []
            for successor in self.graph.successors(node):
                if self.graph.nodes[successor].get('type') == 'keyword':
                    keyword_value = self.graph.nodes[successor].get('value')
                    if keyword_value:
                        related_keywords.append(keyword_value)
            
            # 풍부한 메타데이터가 포함된 결과 생성
            result = {
                'type': 'event',
                'data': event_data,
                'emotion_score': emotion_score,
                'emotion_label': emotion_label,
                'keywords': related_keywords,
                'relevance_score': relevance_score  # 검색 관련성 점수
            }
            
            results.append(result)
        
        return results
    
    def prepare_data(self):
        """그래프 검색을 위한 데이터 준비"""
        # 그래프 구축
        self.build_knowledge_graph()
    
    def get_rag_results(self, query_text, top_k=5):
        """그래프 검색 기반 RAG 결과 반환 - RAG 컨텍스트 생성 강화"""
        # 그래프 검색 수행
        graph_results = self.query_graph(query_text, top_k)
        
        if not graph_results:
            return []
        
        # RAG 컨텍스트 구성 - 그래프 결과를 LLM에 적합한 포맷으로 변환
        rag_context = []
        
        for item in graph_results:
            event_data = item.get('data', {})
            emotion_score = item.get('emotion_score')
            emotion_label = item.get('emotion_label')
            keywords = item.get('keywords', [])
            relevance_score = item.get('relevance_score', 0)
            
            # 일정 정보 추출
            event_title = event_data.get('일정', '')
            event_start = event_data.get('시작', '')
            event_end = event_data.get('종료', '')
            event_type = event_data.get('타입', '')
            
            # 구조화된 일정 정보
            structured_event = {
                'title': event_title,
                'start_time': event_start,
                'end_time': event_end,
                'type': event_type,
                'emotion_score': emotion_score,
                'emotion_label': emotion_label,
                'keywords': keywords,
                'relevance_score': relevance_score,
                'source_type': 'graph'
            }
            
            rag_context.append(structured_event)
        
        return rag_context
        
# 4. Hybrid RAG 시스템
class HybridRAGSystem:
    """벡터 RAG와 그래프 RAG를 결합한 하이브리드 RAG 시스템"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.vector_loader = VectorRAGDataLoader(user_id)
        self.graph_loader = GraphRAGDataLoader(user_id)
    
    def prepare_data(self):
        """벡터 및 그래프 RAG 시스템 데이터 준비"""
        print("\n=== 벡터 RAG 데이터 준비 중... ===\n")
        self.vector_loader.prepare_data()
        print("\n=== 그래프 RAG 데이터 준비 중... ===\n")
        self.graph_loader.prepare_data()
        
    def hybrid_search(self, query_text, top_k=5):
        """벡터 검색과 그래프 검색 결과를 결합한 하이브리드 검색 수행"""
        # 벡터 검색 수행
        vector_results = self.vector_loader.get_rag_results(query_text, top_k)
        print(f"벡터 검색 결과: {len(vector_results)}개")
        
        # 그래프 검색 수행
        graph_results = self.graph_loader.get_rag_results(query_text)
        print(f"그래프 검색 결과: {len(graph_results)}개")
        
        # 결과 병합 및 중복 제거
        combined_results = []
        
        # 벡터 결과와 그래프 결과의 ID 추적
        vector_ids = set()
        graph_ids = set()
        
        # 벡터 결과 ID 수집 및 결과 추가
        for item in vector_results:
            item_id = item.get('metadata', {}).get('id', '')
            if item_id:
                vector_ids.add(item_id)
            
            combined_results.append({
                'source': 'vector',
                'content': item.get('content', ''),
                'metadata': item.get('metadata', {})
            })
        
        # 그래프 결과 중 벡터 결과에 없는 것만 추가
        for item in graph_results:
            if item.get('type') == 'event':
                event_data = item.get('data', {})
                event_id = event_data.get('id', '')
                
                # 벡터 결과에 없고 이미 추가되지 않은 그래프 결과만 추가
                if (not event_id or event_id not in vector_ids) and event_id not in graph_ids:
                    if event_id:
                        graph_ids.add(event_id)
                    
                    combined_results.append({
                        'source': 'graph',
                        'type': 'event',
                        'data': event_data,
                        'emotion_score': item.get('emotion_score')
                    })
        
        # 결과 순위 조정 - 그래프와 벡터 결과를 균형 있게 제공
        graph_items = [item for item in combined_results if item.get('source') == 'graph']
        vector_items = [item for item in combined_results if item.get('source') == 'vector']
        
        # 결과 재구성
        result_count = min(top_k, len(graph_items) + len(vector_items))
        
        final_results = []
        
        # 그래프 결과와 벡터 결과를 적절히 섞음
        for i in range(result_count):
            if i % 2 == 0 and graph_items:  # 짝수 인덱스는 그래프 결과
                final_results.append(graph_items.pop(0))
            elif vector_items:  # 홀수 인덱스는 벡터 결과
                final_results.append(vector_items.pop(0))
            elif graph_items:  # 벡터 결과가 없으면 나머지 그래프 결과 추가
                final_results.append(graph_items.pop(0))
            elif vector_items:  # 그래프 결과가 없으면 나머지 벡터 결과 추가
                final_results.append(vector_items.pop(0))
        
        print(f"최종 하이브리드 검색 결과: {len(final_results)}개")
        return final_results[:top_k]
        
    def get_data_for_report(self):
        """하이브리드 RAG 기반 보고서 데이터 준비"""
        try:
            # 벡터 데이터 가져오기
            print("\n=== 벡터 RAG 데이터 가져오는 중... ===\n")
            vector_data = self.vector_loader.get_vector_data_for_report()
            
            # 그래프 데이터 가져오기 (그래프 특화 분석 포함)
            print("\n=== 그래프 RAG 데이터 가져오는 중... ===\n")
            graph_data = self.graph_loader.get_graph_data_for_report()
            
            # 두 데이터 병합
            hybrid_data = {**vector_data, **graph_data}
            
            # 추가 하이브리드 통계 정보
            hybrid_data["hybrid_stats"] = {
                "vector_data_points": len(vector_data.get("events", [])),
                "graph_data_points": len(graph_data.get("events", [])),
                "combined_data_points": len(hybrid_data.get("events", [])),
                "vector_keywords": len(vector_data.get("activity_analysis", {}).get("top_keywords", [])),
                "graph_keywords": len(graph_data.get("behavioral_insights", {}).get("top_keywords", [])),
            }
            
            return hybrid_data
            
        except Exception as e:
            print(f"하이브리드 데이터 준비 중 오류: {str(e)}")
            traceback.print_exc()
            
            # 벡터 데이터 준비에 실패해도 그래프 데이터라도 반환
            try:
                graph_data = self.graph_loader.get_graph_data_for_report()
                return graph_data
            except:
                # 기본 데이터라도 반환
                basic_loader = DataLoader(self.user_id)
                return basic_loader.get_data_for_report()
    
    def _analyze_query_intent(self, query_text):
        """쿼리 의도 분석"""
        query_lower = query_text.lower()
        
        # 감정 관련 쿼리 확인
        emotion_keywords = ["감정", "기분", "느낌", "행복", "슬픔", "기쁨", "화남", "불안", "좋았던", "나빴던"]
        is_emotion_query = any(keyword in query_lower for keyword in emotion_keywords)
        
        # 시간/날짜 관련 쿼리 확인
        time_keywords = ["언제", "날짜", "시간", "오전", "오후", "저녁", "아침"]
        is_time_query = any(keyword in query_lower for keyword in time_keywords)
        
        # 관계 관련 쿼리 확인
        relationship_keywords = ["관련", "연결", "사이", "패턴", "같이", "함께"]
        is_relationship_query = any(keyword in query_lower for keyword in relationship_keywords)
        
        # 일정 유형 관련 쿼리 확인
        type_keywords = ["유형", "종류", "타입", "분류"]
        is_type_query = any(keyword in query_lower for keyword in type_keywords)
        
        # 의도 판단
        intent = {
            "is_emotion_query": is_emotion_query,
            "is_time_query": is_time_query,
            "is_relationship_query": is_relationship_query,
            "is_type_query": is_type_query
        }
        
        return intent
    
    def _get_weights_by_intent(self, query_intent):
        """쿼리 의도에 따른 검색 가중치 결정"""
        # 기본 가중치
        vector_weight = 0.5
        graph_weight = 0.5
        
        # 의도에 따른 가중치 조정
        if query_intent.get("is_emotion_query", False):
            # 감정 쿼리는 그래프 검색이 더 효과적
            graph_weight = 0.7
            vector_weight = 0.3
        
        elif query_intent.get("is_relationship_query", False):
            # 관계 쿼리는 그래프 검색이 훨씬 효과적
            graph_weight = 0.8
            vector_weight = 0.2
            
        elif query_intent.get("is_time_query", False):
            # 시간 쿼리는 벡터 검색이 더 효과적일 수 있음
            vector_weight = 0.6
            graph_weight = 0.4
            
        elif query_intent.get("is_type_query", False):
            # 유형 쿼리는 균형적 활용
            vector_weight = 0.5
            graph_weight = 0.5
        
        return vector_weight, graph_weight
    
    def _combine_results(self, vector_results, graph_results, vector_weight, graph_weight, top_k):
        """벡터 및 그래프 검색 결과 결합 - 개선된 알고리즘"""
        # 결과 ID 기반 중복 제거 및 통합
        combined_results = {}
        
        # 벡터 결과 처리
        for item in vector_results:
            item_id = None
            if isinstance(item, dict):
                if "일정_제목" in item:
                    item_id = f"event_{item['일정_제목']}"
                elif "title" in item:
                    item_id = f"event_{item['title']}"
            
            # ID 생성 실패 시 해시 사용
            if not item_id:
                item_id = f"vector_{hash(str(item))}"
            
            # 관련성 점수 가중치 적용
            relevance_score = item.get("relevance_score", 0.5) * vector_weight
            
            combined_results[item_id] = {
                "item": item,
                "source": "vector",
                "relevance_score": relevance_score
            }
        
        # 그래프 결과 처리
        for item in graph_results:
            item_id = None
            if isinstance(item, dict):
                if "title" in item:
                    item_id = f"event_{item['title']}"
            
            # ID 생성 실패 시 해시 사용
            if not item_id:
                item_id = f"graph_{hash(str(item))}"
            
            # 관련성 점수 가중치 적용
            relevance_score = item.get("relevance_score", 0.5) * graph_weight
            
            # 이미 있는 항목이면 점수 비교하여 더 높은 것 사용
            if item_id in combined_results:
                existing_score = combined_results[item_id]["relevance_score"]
                if relevance_score > existing_score:
                    combined_results[item_id] = {
                        "item": item,
                        "source": "graph",
                        "relevance_score": relevance_score
                    }
                
                # 양쪽 소스에서 모두 발견된 항목은 점수 보너스
                combined_results[item_id]["relevance_score"] += 0.1
            else:
                combined_results[item_id] = {
                    "item": item,
                    "source": "graph",
                    "relevance_score": relevance_score
                }
        
        # 관련성 점수로 정렬
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x["relevance_score"], 
            reverse=True
        )
        
        # 상위 결과 반환
        return sorted_results[:top_k]
    
    def _prepare_rag_context(self, combined_results, query_text, query_intent):
        """최종 RAG 컨텍스트 준비"""
        rag_context = []
        
        # 의도에 맞게 컨텍스트 구성
        for result in combined_results:
            item = result["item"]
            source = result["source"]
            relevance_score = result["relevance_score"]
            
            # 이벤트 정보 표준화
            standardized_item = self._standardize_item(item, source)
            standardized_item["relevance_score"] = relevance_score
            standardized_item["source"] = source
            
            rag_context.append(standardized_item)
        
        # 쿼리 정보 추가
        context_metadata = {
            "query": query_text,
            "intent": query_intent,
            "result_count": len(rag_context),
            "vector_count": sum(1 for item in rag_context if item.get("source") == "vector"),
            "graph_count": sum(1 for item in rag_context if item.get("source") == "graph")
        }
        
        # LLM에 전달할 최종 컨텍스트
        final_context = {
            "metadata": context_metadata,
            "results": rag_context
        }
        
        return final_context
    
    def _standardize_item(self, item, source):
        """검색 결과 항목을 표준 형식으로 변환"""
        standardized = {}
        
        if source == "vector":
            # 벡터 결과 표준화
            if "일정_제목" in item:
                standardized["title"] = item.get("일정_제목", "")
            elif "title" in item:
                standardized["title"] = item.get("title", "")
            
            if "시작_시간" in item:
                standardized["start_time"] = item.get("시작_시간", "")
            elif "start_time" in item:
                standardized["start_time"] = item.get("start_time", "")
            
            standardized["type"] = item.get("type", item.get("일정_유형", ""))
            standardized["emotion_score"] = item.get("emotion_score", item.get("감정_점수", None))
            standardized["keywords"] = item.get("keywords", item.get("키워드", []))
        
        elif source == "graph":
            # 그래프 결과는 이미 표준 형식에 가까움
            standardized = {k: v for k, v in item.items()}
        
        return standardized
    
    def get_data_for_report(self):
        """하이브리드 RAG 기반 보고서 데이터 준비"""
        try:
            # 벡터 데이터 가져오기
            print("\n=== 벡터 RAG 데이터 가져오는 중... ===\n")
            try:
                vector_data = self.vector_loader.get_vector_data_for_report()
            except AttributeError:
                # get_vector_data_for_report 메서드가 없으면 get_data_for_report 호출
                vector_data = self.vector_loader.get_data_for_report()
            
            # 그래프 데이터 가져오기 (그래프 특화 분석 포함)
            print("\n=== 그래프 RAG 데이터 가져오는 중... ===\n")
            try:
                graph_data = self.graph_loader.get_graph_data_for_report()
            except AttributeError:
                # get_graph_data_for_report 메서드가 없으면 get_data_for_report 호출
                graph_data = self.graph_loader.get_data_for_report()
            
            # 두 데이터 병합
            hybrid_data = {**vector_data, **graph_data}
            
            # 추가 하이브리드 통계 정보
            hybrid_data["hybrid_stats"] = {
                "vector_data_points": len(vector_data.get("events", [])),
                "graph_data_points": len(graph_data.get("events", [])),
                "combined_data_points": len(hybrid_data.get("events", [])),
                "vector_keywords": len(vector_data.get("activity_analysis", {}).get("top_keywords", [])),
                "graph_keywords": len(graph_data.get("behavioral_insights", {}).get("top_keywords", []) 
                                     if "behavioral_insights" in graph_data else []),
            }
            
            return hybrid_data
            
        except Exception as e:
            print(f"하이브리드 데이터 준비 중 오류: {str(e)}")
            traceback.print_exc()
            
            # 기본 데이터라도 반환
            basic_loader = DataLoader(self.user_id)
            return basic_loader.get_data_for_report()
    
    def _merge_data(self, vector_data, graph_data):
        """벡터 및 그래프 데이터 병합 - 중복 제거 및 통합"""
        merged_data = {}
        
        # 기본 데이터 복사
        for key in set(vector_data.keys()) | set(graph_data.keys()):
            if key in vector_data and key in graph_data:
                # 두 소스에 모두 있는 항목 병합
                if key == "events":
                    # 이벤트 병합 (중복 제거)
                    merged_data[key] = self._merge_events(vector_data[key], graph_data[key])
                elif key == "chat_history":
                    # 대화 기록 병합 (중복 제거)
                    merged_data[key] = self._merge_chat_history(vector_data[key], graph_data[key])
                elif isinstance(vector_data[key], dict) and isinstance(graph_data[key], dict):
                    # 두 딕셔너리 병합
                    merged_data[key] = {**vector_data[key], **graph_data[key]}
                else:
                    # 기본적으로 벡터 데이터 우선
                    merged_data[key] = vector_data[key]
            elif key in vector_data:
                merged_data[key] = vector_data[key]
            else:
                merged_data[key] = graph_data[key]
        
        return merged_data
    
    def _merge_events(self, vector_events, graph_events):
        """이벤트 목록 병합 (중복 제거)"""
        # ID 기반 중복 제거
        event_map = {}
        
        # 벡터 이벤트 먼저 추가
        for event in vector_events:
            event_id = event.get("id", "")
            if not event_id:
                event_id = f"event_{hash(str(event))}"
            event_map[event_id] = event
        
        # 그래프 이벤트 추가 (중복 확인)
        for event in graph_events:
            event_id = event.get("id", "")
            if not event_id:
                event_id = f"event_{hash(str(event))}"
            
            # 이미 있는 이벤트는 그래프 데이터로 보강
            if event_id in event_map:
                # 그래프에서만 있는 키 추가
                for key, value in event.items():
                    if key not in event_map[event_id]:
                        event_map[event_id][key] = value
            else:
                event_map[event_id] = event
        
        # 병합된 이벤트 목록 반환
        return list(event_map.values())
    
    def _merge_chat_history(self, vector_chats, graph_chats):
        """대화 기록 병합 (중복 제거)"""
        # ID 기반 중복 제거
        chat_map = {}
        
        # 벡터 대화 먼저 추가
        for chat in vector_chats:
            chat_id = chat.get("id", "")
            if not chat_id:
                chat_id = f"chat_{hash(str(chat))}"
            chat_map[chat_id] = chat
        
        # 그래프 대화 추가 (중복 확인)
        for chat in graph_chats:
            chat_id = chat.get("id", "")
            if not chat_id:
                chat_id = f"chat_{hash(str(chat))}"
            
            # 이미 있는 대화는 병합하지 않음 (충돌 방지)
            if chat_id not in chat_map:
                chat_map[chat_id] = chat
        
        # 병합된 대화 목록 반환
        return list(chat_map.values())


# 5. LLM 리포트 생성 파이프라인
class LLMReportGenerator:
    """LangChain 기반 3단계 LLM 파이프라인 - RAG 통합 강화"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._init_llm_models()
    
    def _init_llm_models(self):
        """LLM 모델 초기화 - 안전한 초기화 적용"""
        try:
            # 환경 변수 확인
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            
            # LLM 모델 초기화
            self.llm1 = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=api_key,
                max_tokens=1000,
                temperature=0.1
            )
            
            self.llm2 = ChatOpenAI(
                model="gpt-4.5-preview",
                api_key=api_key,
                max_tokens=1200,
                temperature=0.7
            )
            
            self.llm3 = ChatOpenAI(
                model="gpt-4.5-preview",
                api_key=api_key,
                max_tokens=1500,
                temperature=0.6
            )
        except Exception as e:
            print(f"LLM 모델 초기화 중 오류: {str(e)}")
            traceback.print_exc()
            
            raise
    
    def _generate_data_analysis_prompt(self, data):
        """데이터 분석 프롬프트 생성"""
        # 기본 데이터 추출
        events = data.get("events", [])
        emotion_analysis = data.get("emotion_analysis", {})
        activity_analysis = data.get("activity_analysis", {})
        chat_analysis = data.get("chat_analysis", {})
        graph_stats = data.get("graph_stats", {})
        event_patterns = data.get("event_patterns", {})
        behavioral_insights = data.get("behavioral_insights", {})
        correlations = data.get("correlations", {})
        hybrid_stats = data.get("hybrid_stats", {})
        
        # 중요 이벤트 데이터 강조 (RAG 관점)
        important_events = self._extract_important_events(events)
        
        # 감정 분석 강화 (이벤트와 감정 연결)
        enhanced_emotion_analysis = self._enhance_emotion_analysis(emotion_analysis, events)
        
        # RAG 특화 프롬프트 생성
        rag_specific_prompt = self._generate_rag_specific_prompt(data)
        
        # 활동 유형 텍스트 생성
        activity_types_text = ", ".join([
            f"{k}: {len(v)}회" for k, v in activity_analysis.get("activity_types", {}).items()
        ])
        
        # 시간대별 활동 텍스트 생성
        time_slots_text = ", ".join([
            f"{k}: {len(v)}회" for k, v in activity_analysis.get("time_slots", {}).items() if v
        ])
        
        # 요일별 활동 텍스트 생성
        weekday_text = ", ".join([
            f"{day}: {len(activities)}회" 
            for day, activities in activity_analysis.get("weekday_activities", {}).items() if activities
        ])
        
        # 감정 점수 분포 텍스트 생성
        emotion_labels = {
            1: '매우 나쁨',
            2: '나쁨',
            3: '보통',
            4: '좋음',
            5: '매우 좋음'
        }
        emotion_text = ", ".join([
            f"{emotion_labels.get(score, score)}({count}회)" 
            for score, count in emotion_analysis.get("emotion_counts", {}).items()
        ])
        
        # 주요 키워드 텍스트 생성
        top_keywords_text = ", ".join([
            f"{keyword}({count}회)" for keyword, count in activity_analysis.get("top_keywords", [])
        ])
        
        # 대화 분석 정보 텍스트 생성
        chat_keywords_text = ", ".join([
            f"{keyword}({count}회)" for keyword, count in list(chat_analysis.get("keywords", {}).items())[:5]
        ])
        
        # 대화 토픽 텍스트 생성
        topics_text = ", ".join(chat_analysis.get("topics", []))
        
        # 그래프 통계 및 분석 텍스트 생성
        graph_stats_text = ""
        if graph_stats:
            graph_stats_text = f"""
그래프 분석 통계:
- 총 노드 수: {graph_stats.get('node_count', 0)}개
- 총 엣지 수: {graph_stats.get('edge_count', 0)}개
- 키워드 노드 수: {graph_stats.get('keyword_count', 0)}개
- 이벤트 노드 수: {graph_stats.get('event_count', 0)}개
- 대화 노드 수: {graph_stats.get('chat_count', 0)}개
"""
        
        # 키워드 상관관계 텍스트 생성
        keyword_co_occurrence_text = ""
        if event_patterns and "keyword_co_occurrence" in event_patterns:
            keyword_co_occurrence = event_patterns.get("keyword_co_occurrence", {})
            if keyword_co_occurrence:
                top_co_occurrences = sorted(keyword_co_occurrence.items(), key=lambda x: x[1], reverse=True)[:5]
                top_co_occurrences = sorted(keyword_co_occurrence.items(), key=lambda x: x[1], reverse=True)[:5]
                keyword_co_occurrence_text = "주요 키워드 상관관계:\n" + "\n".join(
                    [f"- {kw1}와(과) {kw2}: {count}회 함께 등장" for (kw1, kw2), count in top_co_occurrences]
                )
            else:
                keyword_co_occurrence_text = "주요 키워드 상관관계: 데이터 없음"
        
        # 감정 트렌드 텍스트 생성
        emotion_trend_text = ""
        if behavioral_insights and "emotion_trend" in behavioral_insights:
            emotion_trend = behavioral_insights.get("emotion_trend", [])
            if emotion_trend:
                emotion_trend_text = "감정 변화 추이:\n" + "\n".join(
                    [f"- {item.get('date', '')[:10]} {item.get('title', '')}: {item.get('score', 0)}점" 
                     for item in emotion_trend[:5]]
                )
            else:
                emotion_trend_text = "감정 변화 추이: 데이터 없음"
        
        # 이벤트 타입별 감정 점수 텍스트 생성
        emotion_by_type_text = ""
        if correlations and "avg_emotion_by_type" in correlations:
            avg_emotion_by_type = correlations.get("avg_emotion_by_type", {})
            if avg_emotion_by_type:
                emotion_by_type_text = "활동 타입별 평균 감정 점수:\n" + "\n".join(
                    [f"- {event_type}: {score:.2f}/5" for event_type, score in avg_emotion_by_type.items()]
                )
            else:
                emotion_by_type_text = "활동 타입별 평균 감정 점수: 데이터 없음"
        
        # 시간대별 감정 점수 텍스트 생성
        emotion_by_time_text = ""
        if correlations and "avg_emotion_by_time" in correlations:
            avg_emotion_by_time = correlations.get("avg_emotion_by_time", {})
            if avg_emotion_by_time:
                emotion_by_time_text = "시간대별 평균 감정 점수:\n" + "\n".join(
                    [f"- {time_slot}: {score:.2f}/5" for time_slot, score in avg_emotion_by_time.items()]
                )
            else:
                emotion_by_time_text = "시간대별 평균 감정 점수: 데이터 없음"
        
        # 하이브리드 통계 정보 텍스트 생성
        hybrid_stats_text = ""
        if hybrid_stats:
            hybrid_stats_text = f"""
하이브리드 RAG 분석 통계:
- 벡터 데이터 포인트 수: {hybrid_stats.get('vector_data_points', 0)}개
- 그래프 데이터 포인트 수: {hybrid_stats.get('graph_data_points', 0)}개
- 통합 데이터 포인트 수: {hybrid_stats.get('combined_data_points', 0)}개
- 벡터 키워드 수: {hybrid_stats.get('vector_keywords', 0)}개
- 그래프 키워드 수: {hybrid_stats.get('graph_keywords', 0)}개
"""
        
        # 데이터 분석 프롬프트 생성
        prompt = f"""
당신은 RAG(Retrieval-Augmented Generation) 기반 사용자 데이터 분석 전문가입니다. 
벡터 검색과 그래프 구조 분석을 결합한 하이브리드 RAG 시스템에서 추출한 사용자의 일정, 대화 기록, 감정 데이터를 분석하여 
객관적이고 통찰력 있는 결과를 제공해주세요.

분석할 데이터:

[중요 이벤트 정보]
{important_events}

[감정 분석 정보]
{enhanced_emotion_analysis}

[RAG 특화 분석]
{rag_specific_prompt}

1. 활동 유형별 분포:
{activity_types_text}

2. 시간대별 활동:
{time_slots_text}

3. 요일별 활동:
{weekday_text}

4. 주요 활동 키워드:
{top_keywords_text}

5. 감정 점수 분포:
{emotion_text}

6. 평균 감정 점수: {emotion_analysis.get("avg_emotion", 0):.2f}/5

7. 대화 분석:
- 총 대화수: {chat_analysis.get("message_count", 0)}개
- 주요 대화 키워드: {chat_keywords_text}
- 주요 관심사: {topics_text}

8. 반복 일정: 총 {len(activity_analysis.get("recurring_events", []))}개

9. 활동별 감정 정보:
{f"가장 높은 감정 점수 활동: {emotion_analysis.get('highest', {}).get('event', {}).get('일정', '없음')} ({emotion_analysis.get('highest', {}).get('score', 0)}점)" if emotion_analysis.get('highest') else "데이터 없음"}
{f"가장 낮은 감정 점수 활동: {emotion_analysis.get('lowest', {}).get('event', {}).get('일정', '없음')} ({emotion_analysis.get('lowest', {}).get('score', 0)}점)" if emotion_analysis.get('lowest') else "데이터 없음"}

{graph_stats_text if graph_stats_text else ""}

{keyword_co_occurrence_text if keyword_co_occurrence_text else ""}

{emotion_trend_text if emotion_trend_text else ""}

{emotion_by_type_text if emotion_by_type_text else ""}

{emotion_by_time_text if emotion_by_time_text else ""}

{hybrid_stats_text if hybrid_stats_text else ""}

이 데이터를 기반으로 다음 내용을 심도 있게 분석해주세요:

1. 주간 활동 및 감정 분석 
   - 사용자의 주요 일정을 요약하고 감정 변화를 분석하세요.
   - 선호/비선호 활동을 명확히 파악하고, 이러한 활동과 감정 변화 간의 상관관계를 분석하세요.
   - 특별히 인용할 만한 사용자의 메시지가 있다면 이를 중요한 통찰로 연결하세요.

2. 감정 및 심리 상태 분석:
   - 어떤 활동에서 사용자가 가장 긍정적/부정적 감정을 느끼는지 상세히 분석하세요.
   - 감정 변화 추이를 파악하고, 이에 영향을 미치는 요인을 찾아보세요.
   - 사용자의 대화에서 드러나는 주요 관심사, 고민, 희망사항을 심리학적 관점에서 분석하세요.
   - 사용자의 현재 고민이나 목표와 관련된 감정 패턴이 있는지 살펴보세요.

3. 목표 연계 및 실행 가능한 제안을 위한 인사이트:
   - 사용자의 목표 달성에 도움이 되는 패턴과 방해가 되는 패턴을 파악하세요.
   - 사용자의 고민에 직접 연결될 수 있는 데이터 포인트를 찾아보세요.
   - 사용자의 활동 및 감정 패턴에 기반하여 즉시 실행 가능한 행동 제안을 위한 통찰을 제공하세요.
   - 한 달 내 사용자 목표 달성을 위한 구체적인 연계 활동을 제안할 수 있는 근거를 분석하세요.

4. 개인 맞춤 인사이트:
   - 이 사용자만의 독특한 특성이나 패턴이 있다면 이를 객관적으로 설명해주세요.
   - 사용자가 스스로 인식하지 못할 수 있는 패턴이나 연관성을 발견하세요.
   - 사용자의 MBTI나 성향을 직접 언급하지 않되, 그에 부합하는 맞춤형 인사이트를 제공하세요.

벡터 검색과 그래프 분석의 결합된 하이브리드 데이터를 통해, 단일 분석 방법으로는 얻을 수 없는 심층적인 통찰력을 제공해주세요.

분석은 객관적 사실에 기반하되 심리학적 통찰이 풍부해야 하며, 600~700자로 간결하게 정리해주세요. 
이 분석 결과는 개인화된 주간 회고 리포트를 작성하는 데 직접적으로 활용될 것이므로, 가능한 한 구체적이고 실행 가능한 인사이트를 제공해주세요.
"""
        return prompt

    def _extract_important_events(self, events):
        """중요 이벤트 추출 (RAG 관점)"""
        if not events:
            return "중요 이벤트 정보가 없습니다."
        
        # 감정 점수가 높거나 낮은 이벤트 찾기
        emotion_events = []
        for event in events:
            emotion_score = event.get("감정 점수", None)
            if emotion_score is not None and emotion_score != "":
                try:
                    score = int(emotion_score)
                    if score >= 4 or score <= 2:  # 긍정적(4-5) 또는 부정적(1-2) 이벤트
                        emotion_events.append((event, score))
                except (ValueError, TypeError):
                    pass
        
        # 감정 점수 기준 정렬 (높은 것, 낮은 것 순)
        emotion_events.sort(key=lambda x: abs(x[1] - 3), reverse=True)
        
        # 상위 5개 이벤트만 사용
        top_events = emotion_events[:5]
        
        # 포맷팅
        formatted_events = []
        for event, score in top_events:
            event_text = f"- 일정: {event.get('일정', '알 수 없음')}\n"
            event_text += f"  시작: {event.get('시작', '')}\n"
            event_text += f"  유형: {event.get('타입', '기타')}\n"
            event_text += f"  감정 점수: {score}/5\n"
            formatted_events.append(event_text)
        
        if formatted_events:
            return "주요 감정 관련 이벤트:\n" + "\n".join(formatted_events)
        else:
            return "주요 감정 관련 이벤트 정보가 없습니다."
    
    def _enhance_emotion_analysis(self, emotion_analysis, events):
        """감정 분석 강화 (RAG 관점)"""
        if not emotion_analysis:
            return "감정 분석 데이터가 없습니다."
        
        # 기본 감정 분석 정보
        enhanced_analysis = f"평균 감정 점수: {emotion_analysis.get('avg_emotion', 0):.2f}/5\n\n"
        
        # 감정 분포 분석
        emotion_counts = emotion_analysis.get("emotion_counts", {})
        if emotion_counts:
            enhanced_analysis += "감정 점수 분포:\n"
            for score, count in sorted(emotion_counts.items()):
                label = ""
                if score == 1:
                    label = "매우 부정적"
                elif score == 2:
                    label = "부정적"
                elif score == 3:
                    label = "중립"
                elif score == 4:
                    label = "긍정적"
                elif score == 5:
                    label = "매우 긍정적"
                enhanced_analysis += f"- {score}점({label}): {count}회\n"
            enhanced_analysis += "\n"
        
        # 이벤트 유형별 감정 분석
        event_types = {}
        for event in events:
            event_type = event.get("타입", "기타")
            emotion_score = event.get("감정 점수", None)
            
            if emotion_score is not None and emotion_score != "":
                try:
                    score = int(emotion_score)
                    if event_type not in event_types:
                        event_types[event_type] = []
                    event_types[event_type].append(score)
                except (ValueError, TypeError):
                    pass
        
        # 이벤트 유형별 평균 감정
        if event_types:
            enhanced_analysis += "이벤트 유형별 평균 감정:\n"
            for event_type, scores in event_types.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    enhanced_analysis += f"- {event_type}: {avg_score:.2f}/5\n"
            enhanced_analysis += "\n"
        
        return enhanced_analysis
    
    def _generate_rag_specific_prompt(self, data):
        """RAG 특화 프롬프트 생성"""
        # 그래프 통계 정보
        graph_stats = data.get("graph_stats", {})
        graph_info = ""
        if graph_stats:
            graph_info = f"""
그래프 분석 통계:
- 총 노드 수: {graph_stats.get('node_count', 0)}개
- 총 엣지 수: {graph_stats.get('edge_count', 0)}개
- 키워드 노드 수: {graph_stats.get('keyword_count', 0)}개
- 이벤트 노드 수: {graph_stats.get('event_count', 0)}개
- 대화 노드 수: {graph_stats.get('chat_count', 0)}개
"""
        
        # 행동 인사이트 정보
        behavioral_insights = data.get("behavioral_insights", {})
        insights_info = ""
        if behavioral_insights:
            # 상위 키워드 정보
            top_keywords = behavioral_insights.get("top_keywords", [])
            if top_keywords:
                insights_info += "주요 키워드 (그래프 중심성 기준):\n"
                for keyword, score in top_keywords[:5]:
                    insights_info += f"- {keyword}: 중심성 점수 {score:.4f}\n"
                insights_info += "\n"
            
            # 감정 트렌드 정보
            emotion_trend = behavioral_insights.get("emotion_trend", [])
            if emotion_trend:
                insights_info += "감정 변화 트렌드 (시간순):\n"
                for item in emotion_trend[:5]:
                    date = item.get("date", "")[:10] if item.get("date") else ""
                    title = item.get("title", "")
                    score = item.get("score", 0)
                    
                    insights_info += f"- {date} '{title}': {score}점\n"
                insights_info += "\n"
        
        # 상관관계 정보
        correlations = data.get("correlations", {})
        correlation_info = ""
        if correlations:
            # 이벤트 타입별 감정 점수
            avg_emotion_by_type = correlations.get("avg_emotion_by_type", {})
            if avg_emotion_by_type:
                correlation_info += "활동 유형별 평균 감정 점수:\n"
                for event_type, score in avg_emotion_by_type.items():
                    correlation_info += f"- {event_type}: {score:.2f}/5\n"
                correlation_info += "\n"
            
            # 시간대별 감정 점수
            avg_emotion_by_time = correlations.get("avg_emotion_by_time", {})
            if avg_emotion_by_time:
                correlation_info += "시간대별 평균 감정 점수:\n"
                for time_slot, score in avg_emotion_by_time.items():
                    correlation_info += f"- {time_slot}: {score:.2f}/5\n"
                correlation_info += "\n"
        
        # RAG 특화 정보 결합
        rag_specific_prompt = f"{graph_info}\n{insights_info}\n{correlation_info}".strip()
        
        if not rag_specific_prompt:
            rag_specific_prompt = "RAG 특화 분석 데이터가 부족합니다."
        
        return rag_specific_prompt
    
    def _generate_report_prompt(self, analysis_result, data):
        """리포트 생성 프롬프트 생성"""
        events = data.get("events", [])
        user_tendency = data.get("user_tendency", {})
        chat_history = data.get("chat_history", [])
        emotion_analysis = data.get("emotion_analysis", {})
        chat_analysis = data.get("chat_analysis", {})

        # RAG 강화된 이벤트 요약
        rag_enhanced_events = self._summarize_events_with_rag(events)
        
        # RAG 강화된 감정 분석
        rag_enhanced_emotion = self._summarize_emotions_with_rag(emotion_analysis, data)
        
        # RAG 강화된 대화 분석
        rag_enhanced_chat = self._summarize_chat_with_rag(chat_analysis, chat_history)
        
        # 이전 주 날짜 계산
        today = datetime.now(ZoneInfo("Asia/Seoul"))
        end_of_previous_week = today - timedelta(days=today.weekday() + 1)
        start_of_previous_week = end_of_previous_week - timedelta(days=6)
        week_dates = {
            "start_date": start_of_previous_week.strftime("%Y%m%d"),
            "end_date": end_of_previous_week.strftime("%Y%m%d"),
        }
        
        # 감정 요약 생성
        emotion_summary = ""
        if emotion_analysis:
            avg_emotion = emotion_analysis.get("avg_emotion", 0)
            highest = emotion_analysis.get("highest", None)
            lowest = emotion_analysis.get("lowest", None)
            
            emotion_summary = f"감정 분석 요약:\n"
            emotion_summary += f"평균 감정 점수: {avg_emotion:.2f}/5\n"
            
            if highest and isinstance(highest, dict):
                event = highest.get("event", {})
                score = highest.get("score", 0)
                event_title = event.get("일정", "알 수 없음") if isinstance(event, dict) else "알 수 없음"
                emotion_summary += f"가장 높은 감정 점수: {event_title} ({score}점)\n"
            
            if lowest and isinstance(lowest, dict):
                event = lowest.get("event", {})
                score = lowest.get("score", 0) 
                event_title = event.get("일정", "알 수 없음") if isinstance(event, dict) else "알 수 없음"
                emotion_summary += f"가장 낮은 감정 점수: {event_title} ({score}점)\n"
        
        # 대화 요약 생성
        chat_summary = ""
        if chat_analysis:
            keywords = chat_analysis.get("keywords", {})
            topics = chat_analysis.get("topics", [])
            
            if keywords:
                chat_summary = "대화 분석 요약:\n"
                chat_summary += "주요 키워드: " + ", ".join([
                    f"{k}({v}회)" for k, v in list(keywords.items())[:5]
                ])
                chat_summary += "\n"
            
            if topics:
                chat_summary += f"주요 주제: {', '.join(topics)}\n"
        
        # 이벤트 메시지 추출
        event_messages = []
        for event in events[:5]:  # 최대 5개 이벤트만 추출
            event_title = event.get("일정", "")
            if event_title:
                event_messages.append(f"일정: {event_title}")
        
        
        formatted_prompt = f"""
당신은 RAG(Retrieval-Augmented Generation) 기반 개인 성장을 돕는 회고 생성 전문가입니다. 
하이브리드 RAG 시스템에서 제공한 사용자 데이터 분석 결과를 기반으로 개인화된 주간 회고 리포트를 작성해주세요.

회고 리포트는 다음 형식으로 작성해야 합니다:

============================================================================================

## 지난 주를 돌아보며 
지난주에 있었던 특이 사항을 언급하며 사용자의 감정도 언급해준다. 

## 주간 활동과 감정 들여다보기
### 지난 주 의미 있었던 순간들
사용자의 일정과 감정 및 대화를 분석해 중요한 일정이 뭔지 파악하고 해당 일정을 상기 시킨다. 일정과 대화, 그리고 감정을 연결해 어떤 일정을 소화했을 때 긍정적 감정을 보였는지, 혹은 부정적 감정을 보였는지 말해준다.

### 나의 패턴 발견하기 
데이터 분석 결과의 개인 맞춤 인사이트를 참고해 사용자에게 인사이트를 제공한다. 사용자의 일정과 감정을 연결해 데이터로 도출해서 사용자에게 자신의 성향과 경향을 알려준다.

## 나를 위한 맞춤 조언
사용자의 감정 데이터를 활용해 감정을 다스리는 데 도움되는 맞춤형 피드백 및 조언을 해준다. 

## 다가올 한 달을 위한 액션 플랜
한달 이내 목표 및 달성 방안을 제시해준다.
   
## 이번 주 나에게 보내는 메시지
사용자 데이터 기반으로 맞춤형 명언으로 감성적인 마무리를 준다. 명언한 인물 이름도 적어준다. 
명언을 먼저 적고, 그 아래 사용자에게 긍정적 메시지를 준다. 

=========================================================================================

One shot:
=========================================================================================
## 지난 주를 돌아보며 
지난주는 회사의 퇴사와 새로운 직장으로의 전환을 맞이한 굉장히 특별한 시간이었네요. 커리어 전환과 관련된 내적 갈등과 앞으로의 성장 기대감을 동시에 느낄 수 있었어요. 

## 주간 활동과 감정 들여다보기
### 지난 주 의미 있었던 순간들
6개월 간 다닌 회사를 퇴사하며 싱숭생숭하다고 느끼는 동시에 새로운 회사에 대한 기대감을 표출해주셨는데, 이 대목에서 목표지향적 태도가 명확히 드러났어요. 

### 나의 패턴 발견하기
개인적 의미와 성취감을 주는는 활동(러닝 등)을 통해 내적 에너지를 얻는 반면, 급격한 변화의 순간에는 불안한 감정을 느끼는 경향이 있어요. 

## 나를 위한 맞춤 조언
새로운 회사 출근을 앞두고 있기 때문에 불확실성을 느낄 수 있어요. 그럴땐 다음과 같이 생각해보세요. "불안은 성장을 향한 초대장이다." 혹시라도 생각이 복잡해질때는 좋아하는 러닝을 해보는 건 어떨까요?
몸을 움직이면 기분이 좋아지니깐요.   

## 다가올 한 달을 위한 액션 플랜
한달 이내로 현재 배우고 있는 클로드 AI 활용 프로젝트를 완성해보세요. 이를 위해서는 매일 한 시간씩 프로젝트에 임해보세요. 생활 패턴을 보아 저녁 시간에 비어있는 시간이 많으니 저녁 시간을 이용해보세요. 
   
## 이번 주 나에게 보내는 메시지
"인생에는 파도가 많습니다. 중요한 것은 좋은 서퍼가 되는 법을 배우는 것입니다." - 존 카밧 진

지난 주에는 복잡한 변화의 파도를 멋지게 타셨어요. 앞으로 올 파도 또한 멋지게 타실거예요. 제가 항상 함께 할께요. 
==========================================================================================
One shot은 예시일 뿐이니 형식은 그대로 하되, 반드시 실제 내용은 데이터 분석 결과와 사용자의 활동 패턴에 맞게 완전히 새롭게 작성해주세요. 
반드시 어미를 '요'로 끝내주세요.

하이브리드 RAG 분석 결과:
{analysis_result}

[하이브리드 RAG로 발견한 주요 일정 요약]
{rag_enhanced_events}

[하이브리드 RAG로 분석한 감정 분석 요약]
{rag_enhanced_emotion}

[하이브리드 RAG로 추출한 대화 분석 요약]
{rag_enhanced_chat}

참고 데이터:
사용자 프로필:
- 사용자 ID: {self.user_id}
- MBTI: {user_tendency.get('mbti', 'N/A')}
- 연령대: {user_tendency.get('age', 'N/A')}
- 성별: {user_tendency.get('gender', 'N/A')}

지난 주 ({week_dates['start_date']} ~ {week_dates['end_date']}) 활동 기간
"""
        return formatted_prompt
    
    def _summarize_events_with_rag(self, events):
        """RAG 기반 이벤트 요약 생성"""
        if not events:
            return "주요 일정 정보가 없습니다."
        
        # 최대 5개의 중요 이벤트 선택
        important_events = []
        
        # 1. 감정 점수가 높거나 낮은 이벤트 우선
        events_with_emotion = []
        for event in events:
            emotion_score = event.get("감정 점수", None)
            if emotion_score is not None and emotion_score != "":
                try:
                    score = int(emotion_score)
                    if score >= 4 or score <= 2:  # 긍정적(4-5) 또는 부정적(1-2) 이벤트
                        events_with_emotion.append((event, score))
                except (ValueError, TypeError):
                    pass
        
        # 감정 강도(중립에서 멀수록)에 따라 정렬
        events_with_emotion.sort(key=lambda x: abs(x[1] - 3), reverse=True)
        
        # 상위 이벤트 추가
        for event, score in events_with_emotion[:3]:
            event_title = event.get("일정", "")
            event_type = event.get("타입", "")
            start_time = event.get("시작", "")
            
            formatted_date = ""
            if "T" in start_time:
                try:
                    date_part = start_time.split("T")[0]
                    date_obj = datetime.fromisoformat(date_part)
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = start_time.split("T")[0]
            
            emotion_text = ""
            if score >= 4:
                emotion_text = f"긍정적인 감정(점수: {score}/5)"
            elif score <= 2:
                emotion_text = f"부정적인 감정(점수: {score}/5)"
                
            event_summary = f"- '{event_title}' ({event_type}, {formatted_date}): {emotion_text}"
            important_events.append(event_summary)
        
        # 2. 남은 자리는 중요한 유형의 이벤트로 채우기
        if len(important_events) < 5:
            remaining_events = [e for e in events if not any(e.get("일정", "") in s for s in important_events)]
            
            # 중요 이벤트 유형 (변경 가능)
            important_types = ["업무", "미팅", "건강", "운동", "학습", "가족", "약속"]
            
            for event in remaining_events:
                event_type = event.get("타입", "")
                if event_type in important_types:
                    event_title = event.get("일정", "")
                    start_time = event.get("시작", "")
                    
                    formatted_date = ""
                    if "T" in start_time:
                        try:
                            date_part = start_time.split("T")[0]
                            date_obj = datetime.fromisoformat(date_part)
                            formatted_date = date_obj.strftime("%Y-%m-%d")
                        except:
                            formatted_date = start_time.split("T")[0]
                    
                    event_summary = f"- '{event_title}' ({event_type}, {formatted_date})"
                    important_events.append(event_summary)
                    
                    if len(important_events) >= 5:
                        break
        
        # 최종 요약 반환
        if important_events:
            return "RAG 시스템이 발견한 지난 주 주요 일정:\n" + "\n".join(important_events)
        else:
            return "주요 일정 정보가 부족합니다."
        
    def _summarize_emotions_with_rag(self, emotion_analysis, data):
        """RAG 기반 감정 분석 요약 생성"""
        if not emotion_analysis:
            return "감정 분석 데이터가 없습니다."
        
        # 기본 감정 분석 정보
        avg_emotion = emotion_analysis.get("avg_emotion", 0)
        highest = emotion_analysis.get("highest", None)
        lowest = emotion_analysis.get("lowest", None)
        
        # RAG 기반 상관관계 정보
        correlations = data.get("correlations", {})
        avg_emotion_by_type = correlations.get("avg_emotion_by_type", {})
        avg_emotion_by_time = correlations.get("avg_emotion_by_time", {})
        
        # 요약 구성
        summary = []
        
        # 1. 평균 감정 점수
        summary.append(f"지난 주 평균 감정 점수: {avg_emotion:.2f}/5")
        
        # 2. 최고/최저 감정 이벤트
        if highest and isinstance(highest, dict):
            event = highest.get("event", {})
            score = highest.get("score", 0)
            event_title = event.get("일정", "알 수 없음") if isinstance(event, dict) else "알 수 없음"
            summary.append(f"가장 긍정적 활동: '{event_title}' (감정 점수: {score}/5)")
        
        if lowest and isinstance(lowest, dict):
            event = lowest.get("event", {})
            score = lowest.get("score", 0)
            event_title = event.get("일정", "알 수 없음") if isinstance(event, dict) else "알 수 없음"
            summary.append(f"가장 부정적 활동: '{event_title}' (감정 점수: {score}/5)")
        
        # 3. 활동 유형별 감정 평균 (상위 3개)
        if avg_emotion_by_type:
            summary.append("\n활동 유형별 감정 점수 (상위 3개):")
            sorted_types = sorted(avg_emotion_by_type.items(), key=lambda x: x[1], reverse=True)
            for event_type, score in sorted_types[:3]:
                summary.append(f"- {event_type}: {score:.2f}/5")
        
        # 4. 시간대별 감정 평균
        if avg_emotion_by_time:
            summary.append("\n시간대별 감정 점수:")
            for time_slot, score in avg_emotion_by_time.items():
                summary.append(f"- {time_slot}: {score:.2f}/5")
        
        # 최종 요약 반환
        return "\n".join(summary)
    
    def _summarize_chat_with_rag(self, chat_analysis, chat_history):
        """RAG 기반 대화 분석 요약 생성"""
        if not chat_analysis:
            return "대화 분석 데이터가 없습니다."
        
        try:
            summary = []
            if 'sentiment_distribution' in chat_analysis:
                sentiment_dist = chat_analysis['sentiment_distribution']
                summary.append(f"전체 대화의 감정 분포:")
                for sentiment, count in sentiment_dist.items():
                    summary.append(f"- {sentiment}: {count}회")
            return "\n".join(summary)
        except Exception as e:
            print(f"대화 분석 요약 생성 중 오류 발생: {e}")
            return "대화 분석 요약을 생성할 수 없습니다."
    
    def _extract_important_messages(self, chat_history):
        """중요 대화 메시지 추출"""
        if not chat_history:
            return []
        
        try:
            important_messages = []
            for message in chat_history:
                content = message.get('content', '')
                if not content:
                    continue
                
                importance_score = 0
                if len(content) > 50:
                    importance_score += 2
                
                if importance_score >= 2:
                    important_messages.append(content)
            
            return important_messages[:5]
        except Exception as e:
            print(f"중요 메시지 추출 중 오류 발생: {e}")
            return []
    
    def _generate_personalization_prompt(self, structured_report, user_tendency):
        """개인화 프롬프트 생성"""
        try:
            tendency_prompt = self._get_latest_user_tendency_prompt()
            return f"""
사용자 성향:
{tendency_prompt}

구조화된 리포트:
{structured_report}
"""
        except Exception as e:
            print(f"개인화 프롬프트 생성 중 오류 발생: {e}")
            return structured_report

    def _get_analysis_prompt_template(self):
        """데이터 분석 프롬프트 템플릿 생성"""
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 하이브리드 RAG 분석 전문가입니다. 벡터 검색과 그래프 구조 분석을 결합한 하이브리드 분석 결과를 바탕으로 사용자의 일정, 대화, 감정 데이터를 심층적으로 분석하여 통찰력 있는 결과를 제공합니다."
            ),
            HumanMessagePromptTemplate.from_template("{analysis_prompt}")
        ])
    
    def _get_report_prompt_template(self):
        """리포트 생성 프롬프트 템플릿 생성"""
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 하이브리드 RAG 분석과 심리 분석에 전문성을 갖춘 개인 맞춤형 회고 리포트 생성 전문가입니다. 벡터 검색과 그래프 분석이 결합된 하이브리드 RAG 분석 결과를 바탕으로 개인화된 회고 리포트를 작성합니다. 사용자의 행동, 감정, 관심사 간의 다층적 관계를 파악하여 더 심층적인 분석과 통찰력을 제공합니다."
            ),
            HumanMessagePromptTemplate.from_template("{report_prompt}")
        ])
    
    def _get_personalization_prompt_template(self):
        """개인화 프롬프트 템플릿 생성"""
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 사용자의 성향과 심리적 특성을 이해하고 이를 반영한 회고 리포트를 수정하는 전문가입니다. 기존 회고 리포트의 구조와 형식은 유지하면서, 사용자의 성향에 맞게 내용과 톤을 자연스럽게 조정해주세요."
            ),
            HumanMessagePromptTemplate.from_template("{personalization_prompt}")
        ])
    
    def _get_default_tendency_prompt(self):
        """기본 성향 프롬프트 생성"""
        return f"""
사용자 ID: {self.user_id}
MBTI: N/A
연령대: N/A
성별: N/A
성향: 일반적인 특성을 가진 사용자로 가정합니다.
"""

    def _get_latest_user_tendency_prompt(self) -> str:
        """사용자 성향 데이터에서 가장 최근의 prompt를 가져옴"""
        try:
            #  self.data_loader 의존성 제거
            tendency_path = os.path.join(
                "data", "faiss",
                self.user_id,
                "tendency",
                "events.json"
            )
            
            if not os.path.exists(tendency_path):
                print(f"사용자 성향 데이터가 없습니다: {tendency_path}")
                return self._get_default_tendency_prompt()
                    
            with open(tendency_path, "r", encoding="utf-8") as f:
                tendency_data = json.load(f)
            
            # 1. 최상위 레벨의 user_tendency > prompt 확인
            if "user_tendency" in tendency_data and "prompt" in tendency_data["user_tendency"]:
                return tendency_data["user_tendency"]["prompt"]
            
            # 2. updated_at 이후의 user_tendency 확인 
            if "updated_at" in tendency_data and "user_tendency" in tendency_data and "prompt" in tendency_data["user_tendency"]:
                return tendency_data["user_tendency"]["prompt"]
            
            print("사용자 성향 prompt를 찾을 수 없습니다.")
            
            # 4. 기본 성향 데이터 생성 (성향을 찾지 못했을 때)
            user_tendency = {}
            if "user_tendency" in tendency_data:
                user_tendency = tendency_data["user_tendency"]
                
            # 기본 성향 텍스트 생성
            default_prompt = f"""
사용자 ID: {self.user_id}
MBTI: {user_tendency.get('mbti', 'N/A')}
연령대: {user_tendency.get('age', 'N/A')}
성별: {user_tendency.get('gender', 'N/A')}
"""
            return default_prompt
            
        except Exception as e:
            print(f"사용자 성향 데이터 로드 중 오류: {e}")
            traceback.print_exc()
            
            # 오류 발생 시에도 기본 성향 데이터 반환
            return self._get_default_tendency_prompt()
    
    def analyze_data_with_llm1(self, data):
        """LLM1: 하이브리드 RAG 데이터 분석"""
        try:
            # 데이터 분석 프롬프트 생성
            analysis_prompt = self._generate_data_analysis_prompt(data)
            
            # LangChain 파이프라인 실행
            analysis_prompt_template = self._get_analysis_prompt_template()
            
            analysis_chain = (
                {"analysis_prompt": RunnablePassthrough()}
                | analysis_prompt_template
                | self.llm1
                | StrOutputParser()
            )
            
            analysis_result = analysis_chain.invoke(analysis_prompt)
            return analysis_result
        except Exception as e:
            print(f"데이터 분석 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return "데이터 분석을 완료할 수 없습니다."
        
    def generate_structured_report_with_llm2(self, analysis_result, data):
        """LLM2: 구조화된 리포트 생성"""
        try:
            # 리포트 생성 프롬프트 생성
            report_prompt = self._generate_report_prompt(analysis_result, data)
            
            # LangChain 파이프라인 실행
            report_prompt_template = self._get_report_prompt_template()
            
            report_chain = (
                {"report_prompt": RunnablePassthrough()}
                | report_prompt_template
                | self.llm2
                | StrOutputParser()
            )
            
            structured_report = report_chain.invoke(report_prompt)
            return structured_report
        except Exception as e:
            print(f"구조화된 리포트 생성 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return "구조화된 리포트를 생성할 수 없습니다."
        
    def personalize_report_with_llm3(self, structured_report, tendency_data):
        """LLM3: 사용자 성향을 반영한 최종 리포트 생성"""
        try:
            # 사용자 성향 반영 프롬프트 생성
            personalization_prompt = self._generate_personalization_prompt(structured_report, tendency_data)
            
            # LangChain 파이프라인 실행
            tendency_prompt_template = self._get_personalization_prompt_template()
            
            tendency_chain = (
                {"personalization_prompt": RunnablePassthrough()}
                | tendency_prompt_template
                | self.llm3
                | StrOutputParser()
            )
            
            final_report = tendency_chain.invoke(personalization_prompt)
            return final_report
        except Exception as e:
            print(f"리포트 개인화 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return structured_report  # 실패 시 구조화된 리포트 반환

    def generate_complete_report(self, hybrid_data):
        """전체 3단계 LLM 파이프라인 실행"""
        try:
            success_stages = []
            error_stages = []
            
            # 1단계: 데이터 분석
            analysis_result = self.analyze_data_with_llm1(hybrid_data)
            if analysis_result:
                success_stages.append("analysis")
            else:
                error_stages.append("analysis")
            
            # 2단계: 구조화된 리포트 생성
            structured_report = self.generate_structured_report_with_llm2(
                analysis_result, hybrid_data
            )
            if structured_report:
                success_stages.append("structured_report")
            else:
                error_stages.append("structured_report")
            
            # 3단계: 개인화된 리포트 생성
            final_report = self.personalize_report_with_llm3(
                structured_report, hybrid_data
            )
            if final_report:
                success_stages.append("personalization")
            else:
                error_stages.append("personalization")
            
            # 결과 저장
            self._save_report(
                analysis_result,
                structured_report,
                final_report,
                success_stages,
                error_stages
            )
            
            return {
                "analysis_result": analysis_result,
                "structured_report": structured_report,
                "final_report": final_report,
                "success_stages": success_stages,
                "error_stages": error_stages
            }
        except Exception as e:
            print(f"리포트 생성 중 오류 발생: {e}")
            return None

    def _save_report(self, analysis_result, structured_report, final_report, success_stages=None, error_stages=None):
        """생성된 리포트 저장"""
        try:
            timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
            report_data = {
                "user_id": self.user_id,
                "generated_at": timestamp,
                "analysis_result": analysis_result,
                "structured_report": structured_report,
                "final_report": final_report,
                "success_stages": success_stages or [],
                "error_stages": error_stages or [],
                "rag_enabled": True
            }
            
            save_path = os.path.join(
                "data",
                "reports",
                self.user_id,
                f"report_{timestamp}.json"
            )
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"리포트가 저장되었습니다: {save_path}")
        except Exception as e:
            print(f"리포트 저장 중 오류 발생: {e}")
            traceback.print_exc()


# API 요청 및 응답 모델
class ReportRequest(BaseModel):
    user_id: str
    
class ReportListResponse(BaseModel):
    reports: List[str]
    
class ReportDetailResponse(BaseModel):
    user_id: str
    filename: str
    generated_at: str
    analysis_result: str
    structured_report: str
    final_report: str
    rag_enabled: bool = True
    
@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """기본 회고 리포트 생성 API - RAG 기능 강화"""
    try:
        user_id = request.user_id
        
        # 하이브리드 RAG 시스템 초기화
        hybrid_system = HybridRAGSystem(user_id)
        
        # 데이터 준비 (벡터 및 그래프 인덱스 구축)
        hybrid_system.prepare_data()
        
        # 하이브리드 데이터 가져오기
        hybrid_data = hybrid_system.get_data_for_report()
        
        # LLM 리포트 생성기 초기화
        report_generator = LLMReportGenerator(user_id)
        
        # 완전한 리포트 생성
        report_result = report_generator.generate_complete_report(hybrid_data)
        
        # 실패 상태 확인
        if "error" in report_result and report_result["error"]:
            return {
                "status": "partial_success",
                "message": f"리포트 생성 중 일부 오류 발생: {report_result['error']}",
                "report": report_result["final_report"],
                "success_stages": report_result.get("success_stages", []),
                "error_stages": report_result.get("error_stages", [])
            }
        
        # 결과 반환
        return {
            "status": "success",
            "message": "회고 리포트가 성공적으로 생성되었습니다.",
            "report": report_result["final_report"],
            "success_stages": report_result.get("success_stages", []),
            "rag_enabled": True
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")

@app.get("/get-retrospective-reports")
async def get_retrospective_reports(user_id: str):
    """저장된 회고 리포트 목록 조회 - 오류 처리 강화"""
    try:
        # 리포트 폴더 경로
        reports_path = os.path.join("data", "faiss", user_id, "reports")
        
        # 폴더가 존재하지 않는 경우
        if not os.path.exists(reports_path):
            return {"reports": [], "count": 0}
        
        # 리포트 파일 목록 조회
        report_files = [
            filename for filename in os.listdir(reports_path)
            if filename.endswith(".json") and filename.startswith("hybrid_report_")
        ]
        
        # 날짜순으로 정렬 (최신순)
        report_files.sort(reverse=True)
        
        # 메타데이터 추가
        reports_with_metadata = []
        for filename in report_files:
            try:
                file_path = os.path.join(reports_path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 메타데이터 추출
                reports_with_metadata.append({
                    "filename": filename,
                    "generated_at": data.get("generated_at", ""),
                    "rag_enabled": data.get("system_info", {}).get("rag_enabled", False),
                    "success_stages": data.get("success_stages", [])
                })
            except:
                # 파일 읽기 실패해도 기본 정보는 추가
                reports_with_metadata.append({
                    "filename": filename,
                    "generated_at": "",
                    "rag_enabled": False,
                    "success_stages": []
                })
        
        return {
            "reports": reports_with_metadata,
            "count": len(reports_with_metadata)
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 목록 조회 실패: {str(e)}")

@app.get("/get-report-details/{user_id}/{filename}")
async def get_report_details(user_id: str, filename: str):
    """특정 회고 리포트의 상세 정보 조회 - 오류 처리 강화"""
    try:
        # 리포트 파일 경로
        report_path = os.path.join("data", "faiss", user_id, "reports", filename)
        
        # 파일이 존재하지 않는 경우
        if not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail=f"리포트를 찾을 수 없습니다: {filename}")
        
        # 리포트 파일 읽기
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        # 응답 데이터 구성
        response_data = {
            "user_id": user_id,
            "filename": filename,
            "generated_at": report_data.get("generated_at", ""),
            "analysis_result": report_data.get("analysis_result", ""),
            "structured_report": report_data.get("structured_report", ""),
            "final_report": report_data.get("final_report", ""),
            "success_stages": report_data.get("success_stages", []),
            "error_stages": report_data.get("error_stages", []),
            "rag_enabled": report_data.get("system_info", {}).get("rag_enabled", False),
            "graph_enabled": report_data.get("system_info", {}).get("graph_enabled", False)
        }
        
        return response_data
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 상세 조회 실패: {str(e)}")
