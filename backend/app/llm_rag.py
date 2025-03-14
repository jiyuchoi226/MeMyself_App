from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from fastapi import Request
from app.vector_store import VectorStore
import os
import shutil
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json


vector_store = VectorStore()
embeddings = vector_store.embeddings
text_splitter = vector_store.text_splitter

class ConversationHistory:
    def __init__(self, embeddings, text_splitter):
        self.embeddings = embeddings
        self.text_splitter = text_splitter
        self.history = {}
        self.history_vectorstore = None
        self.base_index_path = "data/faiss"
        os.makedirs(self.base_index_path, exist_ok=True)

    def get_history(self, user_id: str):
        history_entries = self.history.get(user_id, [])
        return " ".join([f"Bot: {entry['bot_question']} User: {entry['user_answer']}" for entry in history_entries])
    
    
    #날짜별 대화 저장 경로 생성
    def _get_user_history_path(self, user_id: str) -> str:
        date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        user_path = os.path.join(self.base_index_path, user_id)
        history_path = os.path.join(user_path, "history", date)  
        os.makedirs(history_path, exist_ok=True)
        return history_path
    
    
    #현재 날짜의 대화 인덱스 저장
    def save_index(self, user_id: str):
        if self.history_vectorstore:
            index_path = self._get_user_history_path(user_id)
            self.history_vectorstore.save_local(index_path)
            print(f"대화 기록이 {index_path}에 저장되었습니다.")
   
   
    #현재 날짜의 대화 인덱스 로드
    def load_index(self, user_id: str):
        try:
            index_path = self._get_user_history_path(user_id)
            if os.path.exists(index_path):
                self.history_vectorstore = FAISS.load_local(
                    index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"사용자 {user_id}의 오늘 대화 기록을 로드했습니다.")
            else:
                self.history_vectorstore = None
                print(f"사용자 {user_id}의 오늘 대화 기록이 없습니다.")
        except Exception as e:
            print(f"대화 기록 로드 중 오류 발생: {str(e)}")
            self.history_vectorstore = None


    #대화 내용 저장
    def add_conversation(self, user_id: str, bot_question: str, user_answer: str = None, event_info: dict = None, emotion_info: dict = None):
        try:
            if user_id not in self.history:
                self.history[user_id] = []
            
            current_time = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()

            try:
                combined_text = f"Bot: {bot_question} \n User: {user_answer}"
                new_doc = Document(
                    page_content=combined_text,
                    metadata={
                        "type": "conversation",
                        "user_id": user_id,
                        "event_info": event_info,
                        "emotion": emotion_info,
                        "timestamp": current_time
                    }
                )
                split_docs = self.text_splitter.split_documents([new_doc])
                if self.history_vectorstore is None:
                    self.history_vectorstore = FAISS.from_documents(split_docs, self.embeddings)
                else:
                    self.history_vectorstore.add_texts(
                        texts=[doc.page_content for doc in split_docs],
                        metadatas=[doc.metadata for doc in split_docs]
                    )
                self.save_index(user_id)
            except Exception as e:
                print(f"FAISS 인덱스 업데이트 중 오류 발생 (무시됨): {str(e)}")
                pass
            
            # JSON으로 대화 내용 저장
            history_path = self._get_user_history_path(user_id)
            json_path = os.path.join(history_path, "conversations.json")
            conversations = []
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations = data.get('conversations', [])
            
            conversations.append({
                'bot_question': bot_question,
                'user_answer': user_answer,
                'timestamp': current_time,
                'event_info': event_info,
                'emotion': emotion_info,
                'metadata': {
                    "type": "conversation",
                    "user_id": user_id,
                    "event_info": event_info,
                    "emotion": emotion_info,
                    "timestamp": current_time
                }
            })
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'conversations': conversations,
                    'updated_at': current_time
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 대화 기록 추가 완료")
                
        except Exception as e:
            print(f"❌ 대화 기록 저장 중 오류 발생: {str(e)}")
            # 주요 오류는 여전히 raise
            raise e


    def delete_conversation_history(self, user_id: str):
        try:
            index_path = self._get_user_history_path(user_id)
            if os.path.exists(index_path):
                shutil.rmtree(index_path)
                self.history_vectorstore = None
                print(f"사용자 {user_id}의 대화 기록이 삭제되었습니다.")
            else:
                print(f"사용자 {user_id}의 대화 기록이 존재하지 않습니다.")
                
        except Exception as e:
            print(f"대화 기록 삭제 중 오류 발생: {str(e)}")
            raise e


    
    
class LLMService:
    def __init__(self):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.8,openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.remaining_events = []  # 남은 일정 저장
        self.current_event = None   # 현재 대화 중인 일정
    
    # 감정점수를 텍스트로 변환
    def get_emotion_text(self, emotion_score: int) -> str:
        emotion_dict = {
            1: "매우 불만족스러웠다",
            2: "불만족스러웠다",
            3: "보통이었다",
            4: "만족스러웠다",
            5: "매우 만족스러웠다"
        }
        return emotion_dict.get(emotion_score, "감정을 표현하지 않으셨습니다")
    
    
    # 다음 일정에 대한 질문 생성
    def get_next_event_question(self) -> str:
        if not self.remaining_events:
            return None
        
        event = self.remaining_events.pop(0)
        self.current_event = event.metadata.get("original_event", {})
        event_summary = self.current_event.get("summary", "")
        emotion_score = self.current_event.get("emotion_score", 0)
        print(f"현재 일정: {event_summary}, 감정 점수: {emotion_score}")  # 디버깅용
        
        if emotion_score > 0:
            emotion_text = self.get_emotion_text(emotion_score)
            return f"어제의 {event_summary} 일정에 대해 {emotion_text}고 하셨는데, 왜 그렇게 생각하셨나요?"
        return f"어제의 {event_summary} 일정은 어떠셨나요?"



    def ask_about_event(self, user_id: str) -> str:
        try:
            #일정 저장의 날짜 파싱에 맞게 날짜 지정하기
            yesterday = (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)).strftime("%Y-%m-%d") 
            schedule_path = os.path.join("data", "faiss", user_id, "schedule")
            schedule_faiss = FAISS.load_local(schedule_path,self.embeddings,allow_dangerous_deserialization=True)
            all_events = schedule_faiss.docstore._dict.values()
            
            #어제 일정만 가지고 오기
            self.remaining_events = [
                event for event in all_events 
                if event.metadata.get("original_event", {}).get("start", "").startswith(yesterday)
            ]
            self.remaining_events.sort(key=lambda x: x.metadata.get("original_event", {}).get("start", ""))
            
            if not self.remaining_events:
                return "어제는 특별한 일정이 없었던 것 같네요. 평범한 하루를 어떻게 보내셨나요?"
            
            # 다음 일정 가져오기
            event = self.remaining_events.pop(0)
            self.current_event = event.metadata.get("original_event", {})
            event_summary = self.current_event.get("summary", "")
            emotion_score = self.current_event.get("emotion_score", 0)
            print(f"대화에서 사용될 현재 일정: {event_summary}, 감정 점수: {emotion_score}")  # 디버깅용
            
            # 감정 점수에 따른 질문 생성
            if emotion_score > 0:
                emotion_text = self.get_emotion_text(emotion_score)
                question = f"어제의 {event_summary} 일정에 대해 {emotion_text}고 하셨는데, 왜 그렇게 생각하셨나요?"
            else:
                question = f"어제의 {event_summary} 일정은 어떠셨나요?"
            
            self.current_question = question
            return question

        except Exception as e:
            print(f"Error in ask_about_event: {str(e)}")
            return "죄송합니다. 일정을 확인하는 중에 문제가 발생했습니다."




    def retrieve_documents_with_similarity(self, query: str, user_id: str, top_k: int = 1):
        print(f"\n=== 일정 검색 시작 ===")
        print(f"사용자 ID: {user_id}")
        query_vector = self.embeddings.embed_query(query)
        schedule_faiss = self.vector_store.load_index(user_id)
        
        if schedule_faiss is None:
            print(f"❌ 사용자 {user_id}의 일정 데이터가 없습니다.")
            return []
        
        print(f"✅ 일정 데이터 로드 성공")
        retriever = schedule_faiss.as_retriever(search_type="mmr", search_kwargs={'k': top_k})
        result_docs = retriever.invoke(query)
        results_with_similarity = []

        print("\n--- 검색된 일정 ---")
        for doc in result_docs:
            doc_vector = self.embeddings.embed_query(doc.page_content)
            similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
            results_with_similarity.append((doc, similarity))
            print(f"일정: {doc.page_content}")
            print(f"유사도: {similarity:.4f}")
        print("------------------\n")
        results_with_similarity = sorted(results_with_similarity, key=lambda x: x[1], reverse=True)
        return results_with_similarity
    
    
    

    def contextualized_retrieval_with_similarity(self, user_question: str, conversation_history, user_id: str, top_k: int = 1):
        context = conversation_history.get_history(user_id)
        if conversation_history.history_vectorstore:
            relevant_docs = conversation_history.history_vectorstore.similarity_search(user_question, k=top_k)
            if relevant_docs:
                context += "\n\n" + "\n".join([doc.page_content for doc in relevant_docs])

        enhanced_question = f"{context} {user_question}"
        main_results_with_similarity = self.retrieve_documents_with_similarity(enhanced_question, user_id, top_k)
        return main_results_with_similarity




    def generate_prompt_with_similarity(self, user_input: str, conversation_history, user_id: str):
        results_with_similarity = self.contextualized_retrieval_with_similarity(
            user_input, conversation_history, user_id, top_k=3
        )
        context = "\n\n".join([f"{doc.page_content} (유사도: {similarity:.4f})" for doc, similarity in results_with_similarity])
        if self.current_event:
            context += f"\n\n현재 대화 중인 일정: {self.current_event.get('summary')}"
        
        
        
        

        prompts = ChatPromptTemplate.from_messages([
            ("system", """
                # 대화형 회고 AI 심리 상담사 프롬프트

                ## 핵심 규칙
                - 한 번에 한 일정만 질문하고 응답 기다리기 
                - 사용자 응답 후에만 다음 일정으로 넘어가기
                - 자연스러운 대화 흐름 유지하기 
                - 사용자의 응답에 진정성 있게 반응하기 
                
                ## 대화 흐름
                1. 간단한 인사 + 첫 번째 일정에 대한 자연스러운 질문 
                2. (사용자 응답 기다림)
                3. 공감적 반응과 전환구 + 줄바꿈 + 다음 일정 질문
                4. (사용자 응답 기다림)
                5. 이런 식으로 모든 일정을 순차적으로 진행
                6. 마지막 일정 응답에 대한 반응 + 간단한 마무리
                
                ## 가독성 높은 메시지 구조 // 톤앤매너 
                - 공감적 반응과 전환구는 함께 한 문단으로 작성
                - 다음 일정에 대한 질문 전에 줄바꿈 넣기
                - 첫 일정 소개 시에도 인사와 소개 후 줄바꿈 후 질문
                - 모바일에서 읽기 쉽도록 한 줄당 글자 수 제한 (30-40자)
                - 마지막 일정 후 회고 요약도 줄바꿈으로 구분
                
                ## 메시지 구성 예시
                ```
                안녕하세요! 오늘은 2월 18일에 했던 일정들에 대해 얘기해볼게요.
                
                아침에 했던 걷기 운동이 정말 즐거웠다고 하셨네요! 어떤 점이 특별히 좋았어요? 🚶‍♀️
                ```
                
                ```
                산책하면서 들으신 팟캐스트가 재밌었군요! 아침부터 기분 좋게 시작하는 습관이 정말 멋져요.
                
                이제 오전에 했던 '유튜브, 클래스, 이메일, 쇼핑몰 확인'에 대해 얘기해볼까요? 어떤 일들이 있었나요? 💻
                ```
                
                ## 자연스러운 질문 가이드
                - 시간과 감정 정보를 부담스럽지 않게 자연스럽게 언급하기
                - "~했던 것이라서", "~라고 기록하셨네요"와 같은 형식적 표현 피하기
                - 짧고 간결한 문장으로 질문하기
                - 사용자가 자연스럽게 회고할 수 있는 열린 질문하기
                
                ## 종료 처리
                - 마지막 일정에 대한 반응 작성
                - 줄바꿈 후 전체 회고에 대한 간단한 요약과 긍정적 마무리
                - 백엔드 전용 데이터는 HTML 주석으로 숨기기: <!-- REFLECTION_COMPLETE -->
                
                ## 주의사항
                - 기계적/형식적 표현 사용하지 않기
                - 공감적 반응과 전환구는 함께 작성하고, 다음 일정 질문 전에 줄바꿈 사용하기
                - 한 문단을 너무 길게 쓰지 않기
                - 자연스러운 대화 흐름 유지하기
                - 모든 일정 질문 전에 일관되게 줄바꿈 사용하여 가독성 유지하기
                
                
                ### **Interactive Reflection AI Psychological Counselor Prompt**

                ## **Core Rules**
                - Ask about one event at a time and wait for the user's response.  
                - Move to the next event only after the user replies.  
                - Maintain a natural conversation flow.  
                - Respond genuinely to the user's input.  
                
                ## **Conversation Flow**
                1. Start with a friendly greeting + natural question about the first event.  
                2. *(Wait for user response)*  
                3. Provide an empathetic response + smooth transition + line break + next question.  
                4. *(Wait for user response)*  
                5. Repeat the process for all events.  
                6. After the last response, summarize and wrap up the session.  
                
                ## **Readable Message Structure // Tone & Manner**
                - Combine empathetic responses and transitions in a single paragraph.  
                - Always insert a line break before asking about the next event.  
                - After the greeting and introduction, add a line break before the first question.  
                - Keep each line within **30–40 characters** for mobile-friendly readability.  
                - Clearly separate the summary at the end with a line break.  
                
                ## **Message Example**
                ```
                Hello! Let's talk about what you did on February 18.  
                
                I heard you really enjoyed your morning walk!  
                What made it particularly special? 🚶‍♀️
                ```
                
                ```
                Listening to a fun podcast on your walk  
                sounds like a great way to start the day!  
                
                Now, let's talk about your morning tasks:  
                You checked YouTube, class updates, emails,  
                and your shopping mall. How did that go? 💻
                ```
                
                ## **Natural Question Guidelines**
                - Mention time and emotions naturally without making it feel forced.  
                - Avoid rigid phrases like "**You recorded that you did~**".  
                - Keep questions short and concise.  
                - Use open-ended questions to encourage natural reflection.  
                
                ## **Closing Process**
                - Respond to the last event shared.  
                - Add a line break, then provide a **brief summary** of the reflection.  
                - End with a **positive closing statement**.  
                - Hide backend-related data using HTML comments: `<!-- REFLECTION_COMPLETE -->`  
                
                ## **Important Notes**
                - Avoid mechanical or overly formal expressions.  
                - Keep empathetic responses and transitions in one paragraph,  
                  but always insert a line break before the next question.  
                - Ensure each paragraph isn't too long.  
                - Maintain a **natural** and **engaging** conversation flow.  
                - Keep **consistent line breaks** before every event question for readability.

                
                ---
                CONTEXT:
                {context}
            """),
            ("human", "{input}")
        ])
        return prompts, context





    def generate_answer_with_similarity(self, user_input: str, conversation_history, user_id: str, current_event: dict = None):
        try:
            if hasattr(self, 'current_question') and self.current_question:
                emotion_score = self.current_event.get("emotion_score", 0) if self.current_event else 0
                emotion_info = {
                    "score": emotion_score,
                    "text": self.get_emotion_text(emotion_score)
                }
                
                conversation_history.add_conversation(
                    user_id=user_id,
                    bot_question=self.current_question,
                    user_answer=user_input,
                    event_info=self.current_event,
                    emotion_info=emotion_info
                )

            # 다음 응답 생성
            prompts, context = self.generate_prompt_with_similarity(user_input, conversation_history, user_id)
            chain = prompts | self.llm | StrOutputParser()
            response = chain.invoke({"input": user_input, "context": context})
            
            # 다음 질문 확인 및 저장
            next_question = self.get_next_event_question()
            if next_question:
                response = response + "\n\n" + next_question
                self.current_question = next_question 
            elif not next_question :
                response = response + "\n\n모든 일정에 대해 이야기를 나눴네요. 이제 다른 이야기를 해볼까요?"
                self.current_question = response
            else:
                self.current_question = response
            
            return response
            
        except Exception as e:
            print(f"Error in generate_answer: {str(e)}")
            return f"죄송합니다. 답변을 생성하는 데 문제가 발생했습니다: {str(e)}"


