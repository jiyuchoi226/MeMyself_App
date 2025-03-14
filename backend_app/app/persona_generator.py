import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Any
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings
from openai import OpenAI
import traceback

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from user_tendency import UserTendency


app = FastAPI()

class FaissDataLoader:
    """FAISS 벡터 저장소에서 데이터를 로드하고 분석하는 클래스"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_path = "data\\faiss"
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
        
    def get_data_for_persona(self) -> Dict:
        """페르소나 프롬프트 생성을 위한 데이터 획득"""
        events = self.load_calendar_events()
        chat_history = self.load_chat_history()
        user_tendency = self.load_user_tendency()
        
        return {
            "events": events,
            "chat_history": chat_history,
            "user_tendency": user_tendency,
        }
    
    def save_persona_prompt(self, prompt):
        """페르소나 프롬프트를 파일에 저장"""
        try:
            # 사용자 성향 데이터 파일 경로
            tendency_path = os.path.join(self.base_path, self.user_id, "tendency", "events.json")
            
            if not os.path.exists(tendency_path):
                print(f"사용자 성향 파일을 찾을 수 없음: {tendency_path}")
                return False
            
            # 사용자 성향 데이터 파일 읽기
            with open(tendency_path, "r", encoding="utf-8") as f:
                tendency_data = json.load(f)
            
            # 데이터 구조 확인 후 프롬프트 추가
            if 'user_tendency' not in tendency_data:
                tendency_data['user_tendency'] = {}
            
            tendency_data['user_tendency']['prompt'] = prompt

            # 파일에 저장
            with open(tendency_path, "w", encoding="utf-8") as f:
                json.dump(tendency_data, f, indent=4, ensure_ascii=False)

            return True
            
        except Exception as e:
            print(f"페르소나 프롬프트 저장 중 오류: {str(e)}")
            traceback.print_exc()
            return False

    def filter_oneWeek_Event(self, events: List[Dict]):
        """한 주간의 이벤트 필터링 및 포맷팅"""
        try:
            today = datetime.now(ZoneInfo("Asia/Seoul"))
            end_of_previous_week = today - timedelta(days=today.weekday() + 1)
            start_of_previous_week = end_of_previous_week - timedelta(days=6)

            oneWeek_Event = ""
            emotion_labels = {
                0: '등록 안됨',
                1: '매우 나쁨',
                2: '나쁨',
                3: '보통',
                4: '좋음',
                5: '매우 좋음'
            }

            for event in events:
                try:
                    # 필요한 키가 있는지 확인
                    if all(key in event for key in ['타입', '일정', '시작', '종료', '감정 점수']):
                        # 날짜 추출 및 비교
                        start_date_str = event['시작'].split('T')[0].replace("-","")
                        end_date_str = event['종료'].split('T')[0].replace("-","")
                        
                        # Holidays in United States가 아니고 지난주에 해당하는 일정만 필터링
                        if (event['타입'] != 'Holidays in United States' and 
                            int(start_date_str) >= int(start_of_previous_week.strftime("%Y%m%d")) and 
                            int(end_date_str) <= int(end_of_previous_week.strftime("%Y%m%d"))):
                            
                            # 감정 점수를 정수로 변환
                            try:
                                emotion_score = int(event['감정 점수'])
                            except (ValueError, TypeError):
                                emotion_score = 0  # 변환 실패 시 기본값
                                
                            # 감정 레이블 찾기
                            emotion_label = emotion_labels.get(emotion_score, '등록 안됨')
                            
                            oneWeek_Event += " ".join(["{'summary':", event['일정'], 
                                                   "Start Date:", event['시작'].split('T')[0],
                                                   "Start Time:", event['시작'].split('T')[1].split(':')[0],
                                                   "End Date:", event['종료'].split('T')[0], 
                                                   "End Time:", event['종료'].split('T')[1].split(':')[0],
                                                   "feeling:", emotion_label+"}\n"])
                except (KeyError, IndexError, ValueError) as e:
                    print(f"이벤트 처리 중 오류: {e}, 이벤트: {event}")
                    continue
                    
            return oneWeek_Event
        except Exception as e:
            print(f"이벤트 필터링 전체 오류: {e}")
            traceback.print_exc()
            return ""

class PersonaGenerator:
    """페르소나 생성기"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # FAISS 데이터 로더 초기화
        self.data_loader = FaissDataLoader(user_id)

    def filter_oneWeek_Event(self, events: List[Dict]):
        """한 주간의 이벤트 필터링 및 포맷팅"""
        try:
            today = datetime.now(ZoneInfo("Asia/Seoul"))
            end_of_previous_week = today - timedelta(days=today.weekday() + 1)
            start_of_previous_week = end_of_previous_week - timedelta(days=6)

            oneWeek_Event = ""
            emotion_labels = {
                0: '등록 안됨',
                1: '매우 나쁨',
                2: '나쁨',
                3: '보통',
                4: '좋음',
                5: '매우 좋음'
            }

            for event in events:
                try:
                    # 필요한 키가 있는지 확인
                    if all(key in event for key in ['타입', '일정', '시작', '종료', '감정 점수']):
                        # 날짜 추출 및 비교
                        start_date_str = event['시작'].split('T')[0].replace("-","")
                        end_date_str = event['종료'].split('T')[0].replace("-","")
                        
                        # Holidays in United States가 아니고 지난주에 해당하는 일정만 필터링
                        if (event['타입'] != 'Holidays in United States' and 
                            int(start_date_str) >= int(start_of_previous_week.strftime("%Y%m%d")) and 
                            int(end_date_str) <= int(end_of_previous_week.strftime("%Y%m%d"))):
                            
                            # 감정 점수를 정수로 변환
                            try:
                                emotion_score = int(event['감정 점수'])
                            except (ValueError, TypeError):
                                emotion_score = 0  # 변환 실패 시 기본값
                                
                            # 감정 레이블 찾기
                            emotion_label = emotion_labels.get(emotion_score, '등록 안됨')
                            
                            oneWeek_Event += " ".join(["{'summary':", event['일정'], 
                                                   "Start Date:", event['시작'].split('T')[0],
                                                   "Start Time:", event['시작'].split('T')[1].split(':')[0],
                                                   "End Date:", event['종료'].split('T')[0], 
                                                   "End Time:", event['종료'].split('T')[1].split(':')[0],
                                                   "feeling:", emotion_label+"}\n"])
                except (KeyError, IndexError, ValueError) as e:
                    print(f"이벤트 처리 중 오류: {e}, 이벤트: {event}")
                    continue
                    
            return oneWeek_Event
        except Exception as e:
            print(f"이벤트 필터링 전체 오류: {e}")
            traceback.print_exc()
            return ""

    def format_cvt_oneWeek_Chat(self, chat_history: List[Dict]):
        """채팅 기록 포맷팅"""
        try:
            cvt_oneWeek_Chat = ""
            for chat in chat_history:
                try:
                    # 필요한 키와 중첩 구조가 있는지 확인
                    if ('event_info' in chat and 'user_answer' in chat and
                        'summary' in chat['event_info'] and 'start' in chat['event_info'] and
                        'end' in chat['event_info'] and 'emotion' in chat and 'text' in chat['emotion']):
                        
                        cvt_oneWeek_Chat += " ".join(["{'summary':", chat['event_info']['summary'], 
                                                   "Start Date:", chat['event_info']['start'].split('T')[0],
                                                   "Start Time:", chat['event_info']['start'].split('T')[1].split(':')[0],
                                                   "End Date:", chat['event_info']['end'].split('T')[0], 
                                                   "End Time:", chat['event_info']['end'].split('T')[1].split(':')[0],
                                                   "feeling:", chat['emotion']['text'],
                                                   # "retrospect_qeustion(bot):", chat.get('bot_question', "질문 없음"),
                                                   "retrospect_answered(user):", chat['user_answer']+"}\n"])
                except (KeyError, IndexError, TypeError) as e:
                    print(f"채팅 항목 처리 중 오류: {e}, 채팅: {chat}")
                    continue
                    
            return cvt_oneWeek_Chat
        except Exception as e:
            print(f"채팅 데이터 포맷팅 전체 오류: {e}")
            traceback.print_exc()
            return ""

    def _generate_structured_input_from_raw_data(self, data: Dict):
        """원시 데이터에서 구조화된 입력 생성"""
        try:
            formatted_data = {}

            # 디버깅: 실제 데이터 구조 출력
            print("===== user_tendency 데이터 구조 =====")
            print(data.get('user_tendency', {}))
            print("=====================================")

            # 안전하게 데이터 접근
            raw_user_tendency = data.get('user_tendency', {})
            
            # 기본값 설정
            default_tendency = {
                "gender": "알 수 없음",
                "birthdate": "알 수 없음",
                "mbti": "알 수 없음"
            }
            
            # events.json 파일 구조에 따라 데이터 접근 방식 결정
            if isinstance(raw_user_tendency, dict):
                # user_tendency가 있는지 확인
                if 'user_tendency' in raw_user_tendency:
                    raw_user_tendency = raw_user_tendency['user_tendency']
            else:
                raw_user_tendency = default_tendency
            
            # 필드 존재 여부 확인 및 기본값 설정
            gender = raw_user_tendency.get("gender", "알 수 없음")
            birthdate = raw_user_tendency.get("birthdate", "알 수 없음")
            mbti = raw_user_tendency.get("mbti", "알 수 없음")
            
            # 올바른 문자열 포맷팅
            unchanged_user_tendency = " ".join(["{'gender':", gender,
                                             "birthdate:", birthdate,
                                             "mbti:", mbti+"}\n"])
             
            formatted_data['ucg_tendency'] = unchanged_user_tendency

            # 일주일 이벤트 데이터 처리
            try:
                oneWeek_Event = self.filter_oneWeek_Event(data.get('events', []))
            except Exception as e:
                print(f"이벤트 필터링 중 오류: {str(e)}")
                oneWeek_Event = ""
            formatted_data['oneWeek_Event'] = oneWeek_Event

            # 채팅 데이터 처리
            try:
                cvt_oneWeek_Chat = self.format_cvt_oneWeek_Chat(data.get('chat_history', []))
            except Exception as e:
                print(f"채팅 데이터 처리 중 오류: {str(e)}")
                cvt_oneWeek_Chat = ""
            formatted_data['cvt_oneWeek_Chat'] = cvt_oneWeek_Chat

            return formatted_data
            
        except Exception as e:
            print(f"데이터 구조화 중 일반 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            # 기본 데이터 반환
            return {
                'ucg_tendency': "{'gender': 알 수 없음, birthdate: 알 수 없음, mbti: 알 수 없음}\n",
                'oneWeek_Event': "",
                'cvt_oneWeek_Chat': ""
            }

    def generate_persona_prompt(self):
        """페르소나 프롬프트 생성"""
        try:
            # 1단계: 데이터 로드 (FaissDataLoader 사용)
            data = self.data_loader.get_data_for_persona()
            
            # 2단계: 직접 데이터 구조화
            formatted_data = {}
            
            # 사용자 성향 데이터 처리
            user_tendency_data = data.get('user_tendency', {})
            raw_user_tendency = {}
            
            # 디버깅: 실제 데이터 구조 출력
            print("===== user_tendency 데이터 구조 =====")
            print(user_tendency_data)
            print("=====================================")
            
            # 다양한 구조를 처리할 수 있도록 접근 로직 설정
            # 경우 1: 직접 user_tendency에 사용자 정보가 있는 경우
            if isinstance(user_tendency_data, dict) and 'gender' in user_tendency_data:
                raw_user_tendency = user_tendency_data
                print("사용자 정보를 직접 user_tendency에서 찾았습니다")
            # 경우 2: events.json 구조 (original_events 배열 내 위치)
            elif 'original_events' in user_tendency_data and len(user_tendency_data.get('original_events', [])) > 0:
                if 'user_tendency' in user_tendency_data['original_events'][0]:
                    raw_user_tendency = user_tendency_data['original_events'][0]['user_tendency']
                    print("original_events 내 user_tendency에서 사용자 정보를 찾았습니다:", raw_user_tendency)
            # 경우 3: user_tendency 내 user_tendency 구조
            elif 'user_tendency' in user_tendency_data:
                raw_user_tendency = user_tendency_data['user_tendency']
                print("중첩된 user_tendency에서 사용자 정보를 찾았습니다")
            # 경우 4: 다른 구조 탐색
            else:
                for key, value in user_tendency_data.items():
                    if isinstance(value, dict) and ('gender' in value or 'mbti' in value):
                        raw_user_tendency = value
                        print(f"키 '{key}' 내에서 사용자 정보를 찾았습니다")
                        break
            
            # 사용자 정보 추출
            gender = raw_user_tendency.get("gender", "알 수 없음")
            age = raw_user_tendency.get("age", "알 수 없음")
            birthday = raw_user_tendency.get("birthday", raw_user_tendency.get("birthdate", "알 수 없음"))
            mbti = raw_user_tendency.get("mbti", "알 수 없음")
            
            print(f"추출된 사용자 정보: 성별={gender}, 나이={age}, 생일={birthday}, MBTI={mbti}")
            
            # 사용자 정보 객체 생성 (이후 프롬프트에서 사용)
            user_info = {
                "gender": gender,
                "age": age,
                "mbti": mbti
            }
            
            # 사용자 정보 포맷팅
            unchanged_user_tendency = " ".join(["{'gender':", gender,
                                             "age:", age, 
                                             "birthdate:", birthday,
                                             "mbti:", mbti+"}\n"])
            
            formatted_data['ucg_tendency'] = unchanged_user_tendency
            
            # 이벤트 및 채팅 데이터 처리
            try:
                oneWeek_Event = self.filter_oneWeek_Event(data.get('events', []))
            except Exception as e:
                print(f"이벤트 필터링 중 오류: {str(e)}")
                oneWeek_Event = ""
            
            try:
                cvt_oneWeek_Chat = self.format_cvt_oneWeek_Chat(data.get('chat_history', []))
            except Exception as e:
                print(f"채팅 데이터 처리 중 오류: {str(e)}")
                cvt_oneWeek_Chat = ""
            
            formatted_data['oneWeek_Event'] = oneWeek_Event
            formatted_data['cvt_oneWeek_Chat'] = cvt_oneWeek_Chat

            system_prompt = f"""
# 초개인화 페르소나 도출 LLM 프롬프트
당신은 사용자의 온보딩 정보, 구글 일정 데이터, 감정 기록 및 챗봇 회고 데이터를 분석하여 사용자의 페르소나를 도출하는 전문가입니다.

아래 데이터를 바탕으로 다음 두 가지 형식의 페르소나를 작성하세요.

---

## 1단계: 키워드 중심 페르소나 요약
다음 항목을 키워드 중심으로 간결히 작성하세요.

- **이름**: 
- **성별**: {user_info.get('gender', '알 수 없음')}  
- **연령대**: {user_info.get('age', '알 수 없음')}  
- **MBTI 유형**: {user_info.get('mbti', '알 수 없음')}  
- **직업 (사회적 역할)**:  
- **관심 분야**: (최대 5개)  
- **성격 특징**: (최대 5개)  
- **선호 활동**: (최대 5개)  
- **비선호 활동**: (최대 3개)  
- **현재 고민 및 니즈**: (최대 3개)  
- **목표 예측**: (최대 3개)  
- **트리거 이벤트**: (최대 4개)  
- **기타 특이사항**: (최대 3개)

---

## 2단계: 간략한 문장형 페르소나 설명 (1~2문장)
키워드를 바탕으로 아래 각 항목에 대해 1~2문장으로 짧고 명료하게 작성하세요.

### 1. 성격 및 성향 설명  
(내면적 성격, 행동 스타일, 감정 처리 방식)

### 2. 관심 분야와 선호 활동 설명  
(일상 및 개인 목표와의 연관성)

### 3. 직업적 역할과 고민 설명  
(현재 직업 상황과 고민)

### 4. 목표와 예상 변화 설명  
(목표 달성 시 예상되는 성격, 역할 변화)

### 5. 주요 트리거 이벤트와 반응 설명  
(중요한 이벤트 및 사용자의 반응)

---

## 작성 시 주의사항
- 간결하고 명확하게 작성합니다.
- 추측은 최소화하며 데이터에 기반하여 작성합니다.
- 온보딩 데이터, 구글 일정, 감정 데이터를 모두 활용합니다.
- 특히 다음 사용자 정보를 반영합니다: 성별({user_info.get('gender', '알 수 없음')}), 연령대({user_info.get('age', '알 수 없음')}), MBTI({user_info.get('mbti', '알 수 없음')})

---
"""

            query_prompt = f"""
## 입력 데이터
**온보딩 데이터**:  
{formatted_data['ucg_tendency']}

**구글 일정 데이터**:  
{formatted_data['oneWeek_Event']}

**감정 기록 및 챗봇 회고 데이터**:  
{formatted_data['cvt_oneWeek_Chat']}  
"""

            print("====== 최종 시스템 프롬프트 ======")
            print(system_prompt)
            print("====== 최종 쿼리 프롬프트 ======")
            print(query_prompt)

            analysis_response = self.client.chat.completions.create(
                # model="gpt-4o",
                model="gpt-4.5-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_prompt},
                ],
                max_tokens=800,
                temperature=0.1,
            )

            prompt_content = analysis_response.choices[0].message.content.strip()

            ret = self.data_loader.save_persona_prompt(prompt_content)
            if not ret:
                print("Save Fail: Can't save persona prompt")

            return {"report": prompt_content}
        
        except Exception as e:
            print(f"페르소나 프롬프트 생성 중 오류: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

# API 엔드포인트
@app.post("/generate-retrospective-report")
async def generate_persona_prompt(request: Request):
    body = await request.json()
    user_id = body.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")

    report_generator = PersonaGenerator(user_id)
    return report_generator.generate_persona_prompt()
