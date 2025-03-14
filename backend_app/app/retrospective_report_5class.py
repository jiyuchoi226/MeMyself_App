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
                    
            print(f"전체 일정 수: {len(parsed_events)}, 지난 주 일정 수: {len(filtered_events)}")
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
        # 벡터 검색 모델 초기화 (UpstageEmbeddings 등)
        self.embeddings = UpstageEmbeddings(
            model="embedding-query", api_key=os.getenv("UPSTAGE_API_KEY")
        )
    
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
            
            # 이 부분이 수정된 부분: allow_dangerous_deserialization=True 추가
            vectorstore = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            
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
        
    def prepare_data(self):
        """벡터 검색을 위한 데이터 준비"""
        # 일정 및 대화 데이터 로드
        events = self.load_calendar_events()
        chat_history = self.load_chat_history()
        
        # 벡터 인덱싱을 위한 문서 변환
        documents = []
        
        # 일정 데이터를 문서로 변환
        for event in events:
            event_id = event.get("id", f"event_{hash(str(event))}")
            event_text = f"일정: {event.get('일정', '')}\n"
            event_text += f"시작: {event.get('시작', '')}\n"
            event_text += f"종료: {event.get('종료', '')}\n"
            event_text += f"타입: {event.get('타입', '')}\n"
            
            documents.append({
                "id": event_id,
                "source": "event",
                "text": event_text
            })
        
        # 대화 데이터를 문서로 변환
        for chat in chat_history:
            chat_id = chat.get("id", f"chat_{hash(str(chat))}")
            chat_text = f"사용자 메시지: {chat.get('user_answer', '')}\n"
            chat_text += f"이벤트: {chat.get('event_info', {}).get('summary', '')}\n"
            
            documents.append({
                "id": chat_id,
                "source": "chat",
                "text": chat_text
            })
        
        # 벡터 인덱스 생성
        self.create_vector_index(documents)
        
    def get_rag_results(self, query_text, top_k=5):
        """벡터 검색 기반 RAG 결과 반환"""
        # 벡터 검색 수행 후 결과 반환
        return self.query_vector_store(query_text, top_k)

    def get_vector_data_for_report(self):
        """벡터 RAG 데이터 준비"""
        # 기본 데이터 수집
        return super().get_data_for_report()


# 3. Graph RAG 시스템 - DataLoader에서 직접 상속
class GraphRAGDataLoader(DataLoader):
    """그래프 검색 기반 RAG 시스템 구현"""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        # 그래프 데이터베이스 초기화
        self.graph = nx.DiGraph()
    
    def build_knowledge_graph(self):
        """지식 그래프 구축"""
        try:
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
                self.graph.add_node(event_id, type="event", data=event)
                
                # 사용자와 일정의 관계
                self.graph.add_edge(self.user_id, event_id, relation="HAS_EVENT")
                
                # 일정 키워드 추출 및 연결
                event_title = event.get("일정", "")
                if event_title:
                    for keyword in event_title.split():
                        if len(keyword) > 1:
                            keyword_id = f"keyword_{keyword}"
                            self.graph.add_node(keyword_id, type="keyword", value=keyword)
                            self.graph.add_edge(event_id, keyword_id, relation="HAS_KEYWORD")
                
                # 일정과 감정 연결
                emotion_score = event.get("감정 점수", None)
                if emotion_score is not None and emotion_score != "":
                    try:
                        score = int(emotion_score)
                        emotion_id = f"emotion_{score}"
                        self.graph.add_node(emotion_id, type="emotion", value=score)
                        self.graph.add_edge(event_id, emotion_id, relation="HAS_EMOTION")
                    except (ValueError, TypeError):
                        pass
            
            # 대화 노드 생성 및 관계 설정
            for chat in chat_history:
                chat_id = chat.get("id", f"chat_{hash(str(chat))}")
                self.graph.add_node(chat_id, type="chat", data=chat)
                
                # 사용자와 대화의 관계
                self.graph.add_edge(self.user_id, chat_id, relation="HAS_CHAT")
                
                # 대화와 관련 일정 연결
                event_info = chat.get("event_info", {})
                event_id = event_info.get("id", "")
                if event_id and event_id in self.graph:
                    self.graph.add_edge(chat_id, event_id, relation="ABOUT_EVENT")
                
                # 대화 키워드 추출 및 연결
                user_answer = chat.get("user_answer", "")
                if user_answer:
                    for keyword in user_answer.split():
                        if len(keyword) > 1:
                            keyword_id = f"keyword_{keyword}"
                            if keyword_id not in self.graph:
                                self.graph.add_node(keyword_id, type="keyword", value=keyword)
                            self.graph.add_edge(chat_id, keyword_id, relation="MENTIONS_KEYWORD")
            
            print(f"지식 그래프 구축 완료: 노드 {len(self.graph.nodes)} 개, 엣지 {len(self.graph.edges)} 개")
            return
            
        except Exception as e:
            print(f"지식 그래프 구축 중 오류: {str(e)}")
            traceback.print_exc()
            return
            
    def prepare_data(self):
        """그래프 검색을 위한 데이터 준비"""
        # 그래프 구축
        self.build_knowledge_graph()
        
    def query_graph(self, query_text):
        """그래프 검색 수행"""
        try:
            print(f"쿼리 그래프 시작: '{query_text}'")
            
            # 쿼리에서 키워드 추출
            keywords = [word for word in query_text.split() if len(word) > 1]
            print(f"추출된 키워드: {keywords}")
            
            # 그래프의 모든 키워드 노드 출력
            keyword_nodes = {n: attrs.get('value', '') 
                           for n, attrs in self.graph.nodes(data=True) 
                           if attrs.get('type') == 'keyword'}
            print(f"그래프 내 키워드 노드 수: {len(keyword_nodes)}")
            if keyword_nodes:
                sample_nodes = list(keyword_nodes.items())[:5]
                print(f"그래프 내 키워드 노드 샘플: {sample_nodes}")
                
            # 관련 노드 찾기
            relevant_nodes = set()
            
            # 1. 직접 일치 검색
            for keyword in keywords:
                keyword_id = f"keyword_{keyword}"
                
                # 직접 일치하는 키워드 찾기
                if keyword_id in self.graph:
                    relevant_nodes.add(keyword_id)
                    print(f"직접 일치 키워드 발견: {keyword}")
                    
            # 2. 부분 문자열 검색 
            if not relevant_nodes:  # 직접 일치 결과가 없을 경우 부분 일치 시도
                print("직접 일치하는 키워드 없음, 부분 일치 시도")
                for node, attrs in self.graph.nodes(data=True):
                    if attrs.get('type') == 'keyword':
                        node_value = attrs.get('value', '').lower()
                        
                        # 쿼리의 키워드가 노드 값에 부분적으로 포함되는지 확인
                        for keyword in keywords:
                            if keyword.lower() in node_value or node_value in keyword.lower():
                                relevant_nodes.add(node)
                                print(f"부분 일치 키워드 발견: {node_value} <-> {keyword}")
                                break
            
            print(f"찾은 관련 키워드 노드 수: {len(relevant_nodes)}")
            
            # 3. 관련 키워드 노드와 연결된 모든 이벤트 노드 찾기
            event_nodes = set()
            for keyword_node in relevant_nodes:
                # 키워드와 연결된 모든 이벤트 찾기 (predecessors 사용)
                for predecessor in self.graph.predecessors(keyword_node):
                    if self.graph.nodes[predecessor].get('type') == 'event':
                        event_nodes.add(predecessor)
                        print(f"키워드 '{self.graph.nodes[keyword_node].get('value', '')}' 관련 이벤트 찾음: {predecessor}")
                        
            # 4. 관련 키워드가 없는 경우 모든 이벤트 중 쿼리와 관련 있는 것 찾기
            if not event_nodes and keywords:
                print("관련 이벤트 없음, 모든 이벤트 중 검색")
                for node, attrs in self.graph.nodes(data=True):
                    if attrs.get('type') == 'event':
                        event_data = attrs.get('data', {})
                        event_title = event_data.get('일정', '').lower()
                        event_type = event_data.get('타입', '').lower()
                        
                        # 이벤트 제목이나 타입이 쿼리 키워드를 포함하는지 확인
                        for keyword in keywords:
                            if (keyword.lower() in event_title or 
                                keyword.lower() in event_type):
                                event_nodes.add(node)
                                print(f"이벤트 제목/타입에서 키워드 '{keyword}' 발견: {event_title}")
                                break
            
            # 5. 결과가 여전히 없는 경우 최신 이벤트 몇 개를 반환
            if not event_nodes:
                print("어떤 방법으로도 관련 이벤트를 찾지 못했습니다. 최근 이벤트 반환.")
                event_nodes_list = [n for n, attrs in self.graph.nodes(data=True) 
                                  if attrs.get('type') == 'event']
                
                # 이벤트 시작 시간 기준으로 최근 이벤트 정렬
                sorted_events = []
                for node in event_nodes_list:
                    event_data = self.graph.nodes[node].get('data', {})
                    start_time = event_data.get('시작', '')
                    sorted_events.append((node, start_time))
                
                # 시작 시간 기준 내림차순 정렬 (최신 순)
                sorted_events.sort(key=lambda x: x[1], reverse=True)
                
                # 상위 5개 이벤트 선택
                top_events = [node for node, _ in sorted_events[:min(5, len(sorted_events))]]
                event_nodes = set(top_events)
                print(f"최근 이벤트 {len(event_nodes)}개 반환")
            
            # 관련 노드에서 정보 추출
            results = []
            for node in event_nodes:
                event_data = self.graph.nodes[node].get('data', {})
                
                # 감정 점수 찾기
                emotion_score = None
                for successor in self.graph.successors(node):
                    if self.graph.nodes[successor].get('type') == 'emotion':
                        emotion_score = self.graph.nodes[successor].get('value')
                        break
                
                results.append({
                    'type': 'event',
                    'data': event_data,
                    'emotion_score': emotion_score
                })
            
            print(f"총 {len(results)}개 이벤트 결과 반환")
            return results
                
        except Exception as e:
            print(f"그래프 쿼리 중 오류: {str(e)}")
            traceback.print_exc()
            return []
    
    def extract_event_patterns(self):
        """그래프 구조를 활용한 이벤트 패턴 분석"""
        try:
            # 이벤트 클러스터링 및 패턴 분석
            event_nodes = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'event']
            
            # 일정 유형별 클러스터링
            event_clusters = {}
            for event_node in event_nodes:
                event_data = self.graph.nodes[event_node].get('data', {})
                event_type = event_data.get('타입', '기타')
                
                if event_type not in event_clusters:
                    event_clusters[event_type] = []
                event_clusters[event_type].append(event_data)
            
            # 연결된 감정 분석
            event_emotions = {}
            for event_node in event_nodes:
                for neighbor in self.graph.successors(event_node):
                    if self.graph.nodes[neighbor].get('type') == 'emotion':
                        emotion_value = self.graph.nodes[neighbor].get('value')
                        event_data = self.graph.nodes[event_node].get('data', {})
                        event_title = event_data.get('일정', '')
                        
                        if event_title:
                            event_emotions[event_title] = emotion_value
            
            # 자주 함께 등장하는 키워드 분석
            keyword_co_occurrence = {}
            keyword_nodes = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'keyword']
            
            for keyword1 in keyword_nodes:
                keyword1_value = self.graph.nodes[keyword1].get('value', '')
                event_with_kw1 = set()
                
                # 키워드1이 연결된 이벤트 찾기
                for predecessor in self.graph.predecessors(keyword1):
                    if self.graph.nodes[predecessor].get('type') == 'event':
                        event_with_kw1.add(predecessor)
                
                for keyword2 in keyword_nodes:
                    if keyword1 != keyword2:
                        keyword2_value = self.graph.nodes[keyword2].get('value', '')
                        event_with_kw2 = set()
                        
                        # 키워드2가 연결된 이벤트 찾기
                        for predecessor in self.graph.predecessors(keyword2):
                            if self.graph.nodes[predecessor].get('type') == 'event':
                                event_with_kw2.add(predecessor)
                        
                        # 공통 이벤트 수 계산
                        common_events = event_with_kw1.intersection(event_with_kw2)
                        if common_events:
                            pair = tuple(sorted([keyword1_value, keyword2_value]))
                            keyword_co_occurrence[pair] = len(common_events)
            
            return {
                "event_clusters": event_clusters,
                "event_emotions": event_emotions,
                "keyword_co_occurrence": keyword_co_occurrence
            }
            
        except Exception as e:
            print(f"이벤트 패턴 분석 중 오류: {str(e)}")
            traceback.print_exc()
            return {}
    
    def extract_user_behavioral_insights(self):
        """그래프 분석을 통한 사용자 행동 패턴 인사이트 추출"""
        try:
            # 중심성 분석을 통한 주요 키워드 확인
            keyword_nodes = {n: attrs.get('value', '') 
                            for n, attrs in self.graph.nodes(data=True) 
                            if attrs.get('type') == 'keyword'}
            
            if keyword_nodes:
                # 키워드 서브그래프 생성
                keyword_subgraph = self.graph.subgraph(keyword_nodes.keys())
                
                # 연결 중심성 계산 (해당 키워드가 얼마나 많은 이벤트/대화와 연결되어 있는지)
                degree_centrality = nx.degree_centrality(keyword_subgraph)
                
                # 상위 키워드 추출
                top_keywords = sorted(
                    [(keyword_nodes[node], score) for node, score in degree_centrality.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:
                top_keywords = []
            
            # 감정 분포 분석
            emotion_distribution = {}
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'emotion':
                    emotion_value = attrs.get('value')
                    emotion_distribution[emotion_value] = emotion_distribution.get(emotion_value, 0) + 1
            
            # 사용자 활동 시간대별 분포
            time_distribution = {"아침(06-09)": 0, "오전(09-12)": 0, "오후(12-18)": 0, "저녁(18-22)": 0, "밤(22-06)": 0}
            
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    event_data = attrs.get('data', {})
                    start_time = event_data.get('시작', '')
                    
                    if "T" in start_time:
                        try:
                            hour = int(start_time.split("T")[1][:2])
                            
                            if 6 <= hour < 9:
                                time_distribution["아침(06-09)"] += 1
                            elif 9 <= hour < 12:
                                time_distribution["오전(09-12)"] += 1
                            elif 12 <= hour < 18:
                                time_distribution["오후(12-18)"] += 1
                            elif 18 <= hour < 22:
                                time_distribution["저녁(18-22)"] += 1
                            else:
                                time_distribution["밤(22-06)"] += 1
                        except:
                            pass
            
            # 감정 트렌드 분석 (시간순 배열)
            emotion_trend = []
            event_nodes = [(n, attrs.get('data', {})) 
                          for n, attrs in self.graph.nodes(data=True) 
                          if attrs.get('type') == 'event']
            
            # 시간 순으로 정렬
            sorted_events = sorted(
                event_nodes,
                key=lambda x: x[1].get('시작', ''),
                reverse=False
            )
            
            for event_node, event_data in sorted_events:
                emotion_score = None
                
                # 이벤트에 연결된 감정 찾기
                for neighbor in self.graph.successors(event_node):
                    if self.graph.nodes[neighbor].get('type') == 'emotion':
                        emotion_score = self.graph.nodes[neighbor].get('value')
                        break
                
                if emotion_score is not None:
                    event_title = event_data.get('일정', '')
                    event_start = event_data.get('시작', '')
                    
                    emotion_trend.append({
                        'title': event_title,
                        'date': event_start,
                        'score': emotion_score
                    })
            
            return {
                "top_keywords": top_keywords,
                "emotion_distribution": emotion_distribution,
                "time_distribution": time_distribution,
                "emotion_trend": emotion_trend
            }
            
        except Exception as e:
            print(f"사용자 행동 인사이트 추출 중 오류: {str(e)}")
            traceback.print_exc()
            return {}
    
    def identify_correlations(self):
        """그래프 기반 상관관계 분석"""
        try:
            # 감정 점수와 이벤트 타입 간의 상관관계
            emotion_by_event_type = {}
            
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    event_data = attrs.get('data', {})
                    event_type = event_data.get('타입', '기타')
                    
                    # 이벤트에 연결된 감정 찾기
                    emotion_score = None
                    for neighbor in self.graph.successors(node):
                        if self.graph.nodes[neighbor].get('type') == 'emotion':
                            emotion_score = self.graph.nodes[neighbor].get('value')
                            break
                    
                    if emotion_score is not None:
                        if event_type not in emotion_by_event_type:
                            emotion_by_event_type[event_type] = []
                        emotion_by_event_type[event_type].append(emotion_score)
            
            # 이벤트 타입별 평균 감정 점수 계산
            avg_emotion_by_type = {}
            for event_type, scores in emotion_by_event_type.items():
                if scores:
                    avg_emotion_by_type[event_type] = sum(scores) / len(scores)
            
            # 시간대별 감정 점수 상관관계
            emotion_by_time = {"아침(06-09)": [], "오전(09-12)": [], "오후(12-18)": [], "저녁(18-22)": [], "밤(22-06)": []}
            
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    event_data = attrs.get('data', {})
                    start_time = event_data.get('시작', '')
                    
                    # 감정 점수 찾기
                    emotion_score = None
                    for neighbor in self.graph.successors(node):
                        if self.graph.nodes[neighbor].get('type') == 'emotion':
                            emotion_score = self.graph.nodes[neighbor].get('value')
                            break
                    
                    if emotion_score is not None and "T" in start_time:
                        try:
                            hour = int(start_time.split("T")[1][:2])
                            
                            if 6 <= hour < 9:
                                emotion_by_time["아침(06-09)"].append(emotion_score)
                            elif 9 <= hour < 12:
                                emotion_by_time["오전(09-12)"].append(emotion_score)
                            elif 12 <= hour < 18:
                                emotion_by_time["오후(12-18)"].append(emotion_score)
                            elif 18 <= hour < 22:
                                emotion_by_time["저녁(18-22)"].append(emotion_score)
                            else:
                                emotion_by_time["밤(22-06)"].append(emotion_score)
                        except:
                            pass
            
            # 시간대별 평균 감정 점수 계산
            avg_emotion_by_time = {}
            for time_slot, scores in emotion_by_time.items():
                if scores:
                    avg_emotion_by_time[time_slot] = sum(scores) / len(scores)
            
            # 긍정/부정 이벤트 클러스터링
            positive_events = []
            negative_events = []
            
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get('type') == 'event':
                    event_data = attrs.get('data', {})
                    
                    # 감정 점수 찾기
                    emotion_score = None
                    for neighbor in self.graph.successors(node):
                        if self.graph.nodes[neighbor].get('type') == 'emotion':
                            emotion_score = self.graph.nodes[neighbor].get('value')
                            break
                    
                    if emotion_score is not None:
                        if emotion_score >= 4:  # 긍정적 이벤트 (4-5점)
                            positive_events.append(event_data)
                        elif emotion_score <= 2:  # 부정적 이벤트 (1-2점)
                            negative_events.append(event_data)
            
            return {
                "avg_emotion_by_type": avg_emotion_by_type,
                "avg_emotion_by_time": avg_emotion_by_time,
                "positive_events": positive_events,
                "negative_events": negative_events
            }
            
        except Exception as e:
            print(f"상관관계 분석 중 오류: {str(e)}")
            traceback.print_exc()
            return {}
        
    def get_rag_results(self, query_text, top_k=5):
        """그래프 검색 기반 RAG 결과 반환"""
        # 그래프 검색 수행 후 결과 반환
        return self.query_graph(query_text)
    
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
        
        # 결과 순위 조정 - 그래프와 벡터 결과를 최대한 균형 있게 제공
        # 그래프 결과와 벡터 결과 분리
        graph_items = [item for item in combined_results if item.get('source') == 'graph']
        vector_items = [item for item in combined_results if item.get('source') == 'vector']
        
        # 결과 재구성
        result_count = min(top_k, len(graph_items) + len(vector_items))
        half_count = result_count // 2
        
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


# 5. LLM 리포트 생성 파이프라인
class LLMReportGenerator:
    """LangChain 기반 3단계 LLM 파이프라인"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        # LangChain 컴포넌트 초기화
        self.llm1 = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=1000,
            temperature=0.1
        )
        self.llm2 = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=1200,
            temperature=0.7
        )
        self.llm3 = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=1500,
            temperature=0.6
        )
    
    def _generate_data_analysis_prompt(self, data):
        """데이터 분석 프롬프트 생성"""
        events = data.get("events", [])
        emotion_analysis = data.get("emotion_analysis", {})
        activity_analysis = data.get("activity_analysis", {})
        chat_analysis = data.get("chat_analysis", {})
        graph_stats = data.get("graph_stats", {})
        event_patterns = data.get("event_patterns", {})
        behavioral_insights = data.get("behavioral_insights", {})
        correlations = data.get("correlations", {})
        hybrid_stats = data.get("hybrid_stats", {})
        
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
당신은 사용자 데이터 분석 전문가입니다. 사용자의 일정, 대화 기록, 감정 데이터를 분석하여 객관적이고 통찰력 있는 결과를 제공해주세요.

분석할 데이터:

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
    
    def _generate_report_prompt(self, analysis_result, data):
        """리포트 생성 프롬프트 생성"""
        events = data.get("events", [])
        user_tendency = data.get("user_tendency", {})
        chat_history = data.get("chat_history", [])
        emotion_analysis = data.get("emotion_analysis", {})
        chat_analysis = data.get("chat_analysis", {})
        
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
        
        # 템플릿에서 ${} 대신 {} 사용
        formatted_prompt = f"""
당신은 개인 성장을 돕는 회고 생성 전문가입니다. 데이터 분석가가 제공한 사용자 데이터 분석 결과를 기반으로 개인화된 주간 회고 리포트를 작성해주세요.

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

데이터 분석가의 분석 결과:
{analysis_result}

{emotion_summary if emotion_summary else ""}

{chat_summary if chat_summary else ""}

{f"사용자 메시지 기록:\\n{chr(10).join(event_messages)}" if event_messages else ""}

참고 데이터:
사용자 프로필:
- 사용자 ID: {self.user_id}
- MBTI: {user_tendency.get('mbti', 'N/A')}
- 연령대: {user_tendency.get('age', 'N/A')}
- 성별: {user_tendency.get('gender', 'N/A')}

지난 주 ({week_dates['start_date']} ~ {week_dates['end_date']}) 활동 요약:

1. 일정 정보:
{events[:10] if events else "일정 정보 없음"}

2. 대화 주요 키워드:
{chat_analysis.get("keywords", {}) if chat_analysis else "키워드 정보 없음"}
"""
        return formatted_prompt
    
    def _generate_personalization_prompt(self, structured_report, tendency_data):
        """개인화 프롬프트 생성"""
        # 성향 프롬프트 무조건 _get_latest_user_tendency_prompt()에서 가져오기
        tendency_prompt = self._get_latest_user_tendency_prompt()
        
        # 개인화 프롬프트 생성
        prompt = f"""
다음은 사용자를 위해 생성된 회고 리포트입니다:

{structured_report}

다음은 이 사용자의 성향과 특성에 대한 정보입니다:

{tendency_prompt}

위 회고 리포트를 사용자의 성향과 특성에 맞게 수정해주세요. 리포트의 구조와 주요 내용은 그대로 유지하되, 사용자가 더 공감하고 동기부여 받을 수 있도록 톤, 표현 방식, 조언 등을 사용자 성향에 맞게 자연스럽게 조정해주세요. 
형식은 변경하지 말고 내용만 수정해주세요.
"""
        return prompt

    def _get_latest_user_tendency_prompt(self) -> str:
        """사용자 성향 데이터에서 가장 최근의 prompt를 가져옴"""
        try:
            # 경로를 고정 값으로 설정하여 self.data_loader 의존성 제거
            tendency_path = os.path.join(
                "data", "faiss",
                self.user_id,
                "tendency",
                "events.json"
            )
            
            if not os.path.exists(tendency_path):
                print(f"사용자 성향 데이터가 없습니다: {tendency_path}")
                return ""
                    
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
            return f"""
사용자 ID: {self.user_id}
MBTI: N/A
연령대: N/A
성별: N/A
"""

    def analyze_data_with_llm1(self, data):
        """LLM1: 하이브리드 RAG 데이터 분석"""
        # 데이터 분석 프롬프트 생성
        analysis_prompt = self._generate_data_analysis_prompt(data)
        
        # LangChain 파이프라인 실행
        analysis_prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 하이브리드 RAG 분석 전문가입니다. 벡터 검색과 그래프 구조 분석을 결합한 하이브리드 분석 결과를 바탕으로 사용자의 일정, 대화, 감정 데이터를 심층적으로 분석하여 통찰력 있는 결과를 제공합니다."
            ),
            HumanMessagePromptTemplate.from_template("{analysis_prompt}")
        ])
        
        analysis_chain = (
            {"analysis_prompt": RunnablePassthrough()}
            | analysis_prompt_template
            | self.llm1
            | StrOutputParser()
        )
        
        analysis_result = analysis_chain.invoke(analysis_prompt)
        return analysis_result
        
    def generate_structured_report_with_llm2(self, analysis_result, data):
        """LLM2: 구조화된 리포트 생성"""
        # 리포트 생성 프롬프트 생성
        report_prompt = self._generate_report_prompt(analysis_result, data)
        
        # LangChain 파이프라인 실행
        report_prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 하이브리드 RAG 분석과 심리 분석에 전문성을 갖춘 개인 맞춤형 회고 리포트 생성 전문가입니다. 벡터 검색과 그래프 분석이 결합된 하이브리드 RAG 분석 결과를 바탕으로 개인화된 회고 리포트를 작성합니다. 사용자의 행동, 감정, 관심사 간의 다층적 관계를 파악하여 더 심층적인 분석과 통찰력을 제공합니다."
            ),
            HumanMessagePromptTemplate.from_template("{report_prompt}")
        ])
        
        report_chain = (
            {"report_prompt": RunnablePassthrough()}
            | report_prompt_template
            | self.llm2
            | StrOutputParser()
        )
        
        structured_report = report_chain.invoke(report_prompt)
        return structured_report
        
    def personalize_report_with_llm3(self, structured_report, tendency_data):
        """LLM3: 사용자 성향을 반영한 최종 리포트 생성"""
        # 사용자 성향 반영 프롬프트 생성
        personalization_prompt = self._generate_personalization_prompt(structured_report, {})
        
        # LangChain 파이프라인 실행
        tendency_prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "당신은 사용자의 성향과 심리적 특성을 이해하고 이를 반영한 회고 리포트를 수정하는 전문가입니다. 기존 회고 리포트의 구조와 형식은 유지하면서, 사용자의 성향에 맞게 내용과 톤을 자연스럽게 조정해주세요."
            ),
            HumanMessagePromptTemplate.from_template("{personalization_prompt}")
        ])
        
        tendency_chain = (
            {"personalization_prompt": RunnablePassthrough()}
            | tendency_prompt_template
            | self.llm3
            | StrOutputParser()
        )
        
        final_report = tendency_chain.invoke(personalization_prompt)
        return final_report
        
    def generate_complete_report(self, hybrid_data):
        """전체 3단계 LLM 파이프라인 실행"""
        try:
            # 1. LLM1: 데이터 분석
            print("\n=== 하이브리드 RAG 데이터 분석 진행 중... ===\n")
            analysis_result = self.analyze_data_with_llm1(hybrid_data)
            print("\n=== 데이터 분석 완료 ===\n")
            
            # 2. LLM2: 구조화된 리포트 생성
            print("\n=== 구조화된 리포트 생성 중... ===\n")
            structured_report = self.generate_structured_report_with_llm2(analysis_result, hybrid_data)
            print("\n=== 구조화된 리포트 생성 완료 ===\n")
            
            # 3. LLM3: 사용자 성향 반영
            print("\n=== 사용자 성향 반영 리포트 생성 중... ===\n")
            tendency_data = hybrid_data.get("user_tendency", {})
            final_report = self.personalize_report_with_llm3(structured_report, tendency_data)
            print("\n=== 사용자 성향 반영 리포트 생성 완료 ===\n")
            
            # 결과 저장
            self._save_report(analysis_result, structured_report, final_report)
            
            return {
                "analysis_result": analysis_result,
                "structured_report": structured_report,
                "final_report": final_report
            }
        except Exception as e:
            print(f"리포트 생성 중 오류: {str(e)}")
            traceback.print_exc()
            return {
                "error": str(e),
                "analysis_result": "",
                "structured_report": "",
                "final_report": ""
            }
    
    def _save_report(self, analysis_result, structured_report, final_report):
        """생성된 리포트 저장"""
        try:
            # 저장 경로 생성
            report_path = os.path.join(
                "data", "faiss", self.user_id, "reports",
                f"hybrid_report_{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')}.json"
            )
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            # 리포트 저장
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "generated_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                    "analysis_result": analysis_result,
                    "structured_report": structured_report,
                    "final_report": final_report
                }, f, ensure_ascii=False, indent=2)
                
            print(f"리포트 저장 완료: {report_path}")
        except Exception as e:
            print(f"리포트 저장 중 오류: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {e}")
        
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

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """기본 회고 리포트 생성 API"""
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
        
        # 결과 반환
        if "error" in report_result and report_result["error"]:
            raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {report_result['error']}")
        
        return {
            "status": "success",
            "message": "회고 리포트가 성공적으로 생성되었습니다.",
            "report": report_result["final_report"]
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")

@app.get("/get-retrospective-reports")
async def get_retrospective_reports(user_id: str):
    """저장된 회고 리포트 목록 조회"""
    try:
        # 리포트 폴더 경로
        reports_path = os.path.join("data", "faiss", user_id, "reports")
        
        # 폴더가 존재하지 않는 경우
        if not os.path.exists(reports_path):
            return {"reports": []}
        
        # 리포트 파일 목록 조회
        report_files = [
            filename for filename in os.listdir(reports_path)
            if filename.endswith(".json") and filename.startswith("hybrid_report_")
        ]
        
        # 날짜순으로 정렬 (최신순)
        report_files.sort(reverse=True)
        
        return {"reports": report_files}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 목록 조회 실패: {str(e)}")

@app.get("/get-report-details/{user_id}/{filename}")
async def get_report_details(user_id: str, filename: str):
    """특정 회고 리포트의 상세 정보 조회"""
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
            "final_report": report_data.get("final_report", "")
        }
        
        return response_data
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"리포트 상세 조회 실패: {str(e)}")