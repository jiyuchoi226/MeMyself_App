import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Any
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings
from openai import OpenAI
import traceback

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

class FaissDataLoader:
    """FAISS 벡터 저장소에서 데이터를 로드하고 분석하는 클래스"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_path = "data/faiss"
        # 실제 환경에서는 API 키를 환경 변수로 설정
        self.embeddings = UpstageEmbeddings(
            model="embedding-query", api_key=os.getenv("UPSTAGE_API_KEY")
        )
    
    def _get_previous_week_dates(self) -> Dict[str, str]:
        """지난 주의 시작일과 종료일 계산"""
        today = datetime.now(ZoneInfo("Asia/Seoul"))
        end_of_previous_week = today - timedelta(days=today.weekday() + 1)
        start_of_previous_week = end_of_previous_week - timedelta(days=6)

        return {
            "start_date": start_of_previous_week.strftime("%Y%m%d"),
            "end_date": end_of_previous_week.strftime("%Y%m%d"),
        }
    
    def load_calendar_events(self) -> List[Dict]:
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
            
            return parsed_events
            
        except Exception as e:
            print(f"일정 데이터 로드 중 오류: {str(e)}")
            traceback.print_exc()
            return []
    
    def load_chat_history(self) -> List[Dict]:
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
    
    def load_user_tendency(self) -> Dict:
        """사용자 성향 데이터 로드"""
        try:
            # 사용자 성향 데이터 파일 경로
            tendency_path = os.path.join(self.base_path, f"{self.user_id}_tendency", "events.json")
            
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
    
    def analyze_emotion_data(self, events: List[Dict]) -> Dict:
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
    
    def analyze_activity_patterns(self, events: List[Dict]) -> Dict:
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
    
    def analyze_chat_content(self, chat_history: List[Dict]) -> Dict:
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
            
            # 주제 및 감정 키워드 분석 (간단한 버전)
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
    
    def get_data_for_report(self) -> Dict:
        """회고 리포트 생성을 위한 종합 데이터 획득"""
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


class RetrospectiveReportGenerator:
    """회고 리포트 생성기"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # FAISS 데이터 로더 초기화
        self.data_loader = FaissDataLoader(user_id)

    def _generate_data_analysis_prompt(self, data: Dict) -> str:
        """데이터 분석 프롬프트 생성"""
        events = data["events"]
        emotion_analysis = data["emotion_analysis"]
        activity_analysis = data["activity_analysis"]
        chat_analysis = data["chat_analysis"]
        
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

분석은 객관적 사실에 기반하되 심리학적 통찰이 풍부해야 하며, 600~700자로 간결하게 정리해주세요. 
이 분석 결과는 개인화된 주간 회고 리포트를 작성하는 데 직접적으로 활용될 것이므로, 가능한 한 구체적이고 실행 가능한 인사이트를 제공해주세요.
"""
        return prompt

    def _generate_report_prompt(self, data_analysis: str, data: Dict) -> str:
        """회고 리포트 프롬프트 생성"""
        events = data.get("events", [])
        user_tendency = data.get("user_tendency", {})
        chat_history = data.get("chat_history", [])
        emotion_analysis = data.get("emotion_analysis", {})
        chat_analysis = data.get("chat_analysis", {})
        
        # 이전 주 날짜 계산
        week_dates = self.data_loader._get_previous_week_dates()
        
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

## 지난 주 돌아보기 
지난주에 있었던 특이 사항을 언급하며 사용자의 감정도 언급해준다. 

## 주간 활동 및 감정 분석
### 지난 주 중요한 일정:
사용자의 일정과 감정 및 대화를 분석해 중요한 일정이 뭔지 파악하고 해당 일정을 상기 시킨다. 일정과 대화, 그리고 감정을 연결해 어떤 일정을 소화했을 때 긍정적 감정을 보였는지, 혹은 부정적 감정을 보였는지 말해준다.

### 이러한 데이터 분석을 바탕으로 
데이터 분석 결과의 개인 맞춤 인사이트를 참고해 사용자에게 인사이트를 제공한다. 사용자의 일정과 감정을 연결해 데이터로 도출해서 사용자에게 자신의 성향과 경향을 알려준다.

## 맞춤형 피드백 및 조언 강화
사용자의 감정 데이터를 활용해 감정을 다스리는 데 도움되는 맞춤형 피드백 및 조언을 해준다. 

## 미래 행동 제안 및 목표 달성 액션 플랜
한달 이내 목표 및 달성 방안을 제시해준다.
   
## 지난 주를 정리하며 떠올리고 싶은 명언언
사용자 데이터 기반으로 맞춤형 명언으로 감성적인 마무리를 준다. 명언한 인물 이름도 적어준다.
명언을 먼저 적고, 그 아래 사용자에게 긍정적 메시지를 준다. 

=========================================================================================

One shot:
=========================================================================================
## 지난 주 돌아보기 
지난주는 회사의 퇴사와 새로운 직장으로의 전환을 맞이한 굉장히 특별한 시간이었네요. 커리어 전환과 관련된 내적 갈등과 앞으로의 성장 기대감을 동시에 느낄 수 있었어요. 

## 주간 활동 및 감정 분석
### 지난 주 중요한 일정:
6개월 간 다닌 회사를 퇴사하며 싱숭생숭하다고 느끼는 동시에 새로운 회사에 대한 기대감을 표출해주셨는데, 이 대목에서 목표지향적 태도가 명확히 드러났어요. 

### 이러한 데이터 분석을 바탕으로 
개인적 의미와 성취감을 주는는 활동(러닝 등)을 통해 내적 에너지를 얻는 반면, 급격한 변화의 순간에는 불안한 감정을 느끼는 경향이 있어요. 

## 맞춤형 피드백 및 조언 강화
새로운 회사 출근을 앞두고 있기 때문에 불확실성을 느낄 수 있어요. 그럴땐 다음과 같이 생각해보세요. "불안은 성장을 향한 초대장이다." 혹시라도 생각이 복잡해질때는 좋아하는 러닝을 해보는 건 어떨까요?
몸을 움직이면 기분이 좋아지니깐요.   

## 미래 행동 제안 및 목표 달성 액션 플랜
한달 이내로 현재 배우고 있는 클로드 AI 활용 프로젝트를 완성해보세요. 이를 위해서는 매일 한 시간씩 프로젝트에 임해보세요. 생활 패턴을 보아 저녁 시간에 비어있는 시간이 많으니 저녁 시간을 이용해보세요. 
   
## 지난 주를 정리하며 떠올리고 싶은 명언언
"인생에는 파도가 많습니다. 중요한 것은 좋은 서퍼가 되는 법을 배우는 것입니다." - 존 카밧 진

지난 주에는 복잡한 변화의 파도를 멋지게 타셨어요. 앞으로 올 파도 또한 멋지게 타실거예요. 제가 항상 함께 할께요. 
==========================================================================================
One shot은 예시일 뿐이니 형식은 그대로 하되, 반드시 실제 내용은 데이터 분석 결과와 사용자의 활동 패턴에 맞게 완전히 새롭게 작성해주세요. 
반드시 어미를 '요'로 끝내주세요.

데이터 분석가의 분석 결과:
{data_analysis}

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

    def generate_retrospective_report(self) -> Dict[str, Any]:
        """OpenAI API를 통한 회고 리포트 생성 - 데이터 분석과 회고 작성을 명확히 분리"""
        try:
            # 1단계: 데이터 로드 (FaissDataLoader 사용)
            data = self.data_loader.get_data_for_report()
            
            # 2단계: 데이터 분석 프롬프트 생성
            data_analysis_prompt = self._generate_data_analysis_prompt(data)
            
            # 3단계: 데이터 분석 LLM 호출
            print("\n=== 데이터 분석 진행 중... ===\n")
            analysis_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 데이터 분석 전문가입니다. 사용자의 일정, 대화, 감정 데이터를 객관적으로 분석하여 정확하고 통찰력 있는 결과를 제공합니다."},
                    {"role": "user", "content": data_analysis_prompt},
                ],
                max_tokens=800,
                temperature=0.25,
            )
            
            data_analysis_result = analysis_response.choices[0].message.content.strip()
            print("\n=== 데이터 분석 결과 ===\n")
            print(data_analysis_result)
            print("\n========================\n")
            
            # 4단계: 회고 리포트 프롬프트 생성
            report_prompt = self._generate_report_prompt(data_analysis_result, data)
            
            # 5단계: 회고 리포트 LLM 호출
            print("\n=== 회고 리포트 생성 중... ===\n")
            report_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 개인 맞춤형 회고 리포트 생성 전문가입니다. 데이터 분석가가 제공한 분석 결과를 바탕으로 개인화된 회고 리포트를 작성합니다. 형식을 준수하면서도 내용은 사용자의 실제 데이터를 반영한 맞춤형 내용으로 작성해주세요. 또한 심리 전문가로서 저장된 사용자 페르소나 데이터와 지난주의 일정, 감정 기록, 챗봇 회고 데이터를 바탕으로 사용자의 현재 목표 및 고민과 직접 연관된 개인 맞춤형 주간 회고 리포트를 작성합니다.",
                    },
                    {"role": "user", "content": report_prompt},
                ],
                max_tokens=1200,
                temperature=0.75,
            )

            report_content = report_response.choices[0].message.content.strip()
            print("\n=== 회고 리포트 생성 완료 ===\n")

            # 6단계: 리포트 저장
            report_path = os.path.join(
                self.data_loader.base_path,
                self.user_id,
                "retrospective_reports",
                f"{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')}_report.json",
            )
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "generated_at": datetime.now(
                            ZoneInfo("Asia/Seoul")
                        ).isoformat(),
                        "data_analysis": data_analysis_result,
                        "report_content": report_content,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            return {
                "message": "회고 리포트 생성 성공", 
                "report": report_content,
                "analysis": data_analysis_result
            }

        except Exception as e:
            print(f"회고 리포트 생성 중 오류: {e}")
            raise HTTPException(status_code=500, detail=f"회고 리포트 생성 실패: {e}")
        
# API 엔드포인트
@router.post("/generate-retrospective-report")
async def generate_retrospective_report(request: Request):
    body = await request.json()
    user_id = body.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")

    report_generator = RetrospectiveReportGenerator(user_id)
    return report_generator.generate_retrospective_report()


@router.get("/get-retrospective-reports")
async def get_retrospective_reports(user_id: str):
    """저장된 회고 리포트 목록 조회"""
    try:
        reports_path = os.path.join("data", "faiss", user_id, "retrospective_reports")

        if not os.path.exists(reports_path):
            return {"message": "저장된 회고 리포트가 없습니다.", "reports": []}

        reports = []
        for filename in sorted(os.listdir(reports_path), reverse=True):
            if filename.endswith("_report.json"):
                with open(
                    os.path.join(reports_path, filename), "r", encoding="utf-8"
                ) as f:
                    report = json.load(f)
                    report["filename"] = filename
                    reports.append(report)

        return {"message": "회고 리포트 목록 조회 성공", "reports": reports}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회고 리포트 조회 실패: {e}")
