import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 프로젝트 루트 디렉토리를 PYTHONPATH에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# .env 파일 로드
load_dotenv()

from app.retrospective_report import RetrospectiveReportGenerator, FaissDataLoader

def print_debug_info(user_id):
    """디버깅을 위한 데이터 로드 및 출력 함수"""
    print("\n===== 데이터 로드 디버깅 정보 =====")
    
    # FaissDataLoader 초기화
    data_loader = FaissDataLoader(user_id)
    
    # 기간 정보 확인
    week_dates = data_loader._get_previous_week_dates()
    print(f"분석 대상 기간: {week_dates['start_date']} ~ {week_dates['end_date']}")
    
    # 현재 시간 정보 (디버깅용)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    print(f"현재 시간: {now.isoformat()}")
    print(f"현재 요일: {now.weekday()} (0:월요일, 6:일요일)")
    
    # 일정 파일 경로 확인
    calendar_path = os.path.join(
        data_loader.base_path, user_id, "schedule", "events.json"
    )
    print(f"일정 파일 경로: {calendar_path}")
    print(f"파일 존재 여부: {os.path.exists(calendar_path)}")
    
    # 일정 데이터 로드
    events = data_loader.load_calendar_events()
    print(f"로드된 일정 데이터 수: {len(events)}")
    
    # 일정 데이터 샘플 출력 (최대 3개)
    if events:
        print("\n일정 데이터 샘플:")
        for i, event in enumerate(events[:3]):
            print(f"일정 {i+1}:")
            for key, value in event.items():
                print(f"  {key}: {value}")
    else:
        print("로드된 일정이 없습니다.")
    
    # 대화 기록 로드
    chat_history = data_loader.load_chat_history()
    print(f"\n로드된 대화 기록 수: {len(chat_history)}")
    
    # 대화 기록 샘플 출력 (최대 2개)
    if chat_history:
        print("\n대화 기록 샘플:")
        for i, chat in enumerate(chat_history[:2]):
            print(f"대화 {i+1}:")
            for key, value in {k: v for k, v in chat.items() if k in ["event_info", "user_answer", "created_at"]}.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
    else:
        print("로드된 대화 기록이 없습니다.")
    
    # 사용자 성향 데이터 로드
    user_tendency = data_loader.load_user_tendency()
    if user_tendency:
        print("\n사용자 성향 데이터:")
        if isinstance(user_tendency, dict):
            # user_tendency 내의 키 표시
            print(f"키: {list(user_tendency.keys())}")
            
            # 특정 중요 필드 표시
            if "user_tendency" in user_tendency:
                print("\nuser_tendency 내용:")
                for key, value in user_tendency["user_tendency"].items():
                    if key == "prompt":
                        print(f"  prompt: {value[:100]}... (잘림)")
                    else:
                        print(f"  {key}: {value}")
    else:
        print("\n사용자 성향 데이터가 없습니다.")
    
    print("\n===== 디버깅 정보 종료 =====\n")

def main():
    # 테스트할 사용자 ID
    user_id = "ica.2team02@gmail.com"

    try:
        # 데이터 로드 디버깅 정보 출력
        print_debug_info(user_id)
        
        # 리포트 생성기 초기화
        report_generator = RetrospectiveReportGenerator(user_id)
        
        # 회고 리포트 생성
        print("\n=== 회고 리포트 생성 시작 ===")
        print("처리 중입니다... (최대 1분 소요될 수 있습니다)")
        result = report_generator.generate_retrospective_report()
        
        # 결과 출력
        print("\n=== 생성 결과 ===")
        
        # 데이터 분석 결과
        if "analysis" in result:
            print("\n1. 데이터 분석 결과:")
            print("-" * 40)
            print(result["analysis"])
            print("-" * 40)
        
        # 회고 리포트
        print("\n2. 회고 리포트:")
        print("-" * 40)
        print(result["report"])
        print("-" * 40)

    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()