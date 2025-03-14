import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# UserTendency 클래스 import
from user_tendency import UserTendency

def setup_environment():
    """테스트 환경 설정"""
    # UPSTAGE_API_KEY 환경 변수 확인
    if not os.getenv('UPSTAGE_API_KEY'):
        api_key = input("UPSTAGE API 키를 입력하세요: ")
        os.environ['UPSTAGE_API_KEY'] = api_key
    
    # 데이터 경로 확인
    base_path = "data/faiss"
    os.makedirs(base_path, exist_ok=True)
    print(f"데이터 저장 경로: {os.path.abspath(base_path)}")

def get_user_info():
    """사용자로부터 정보 입력받기"""
    print("\n===== 사용자 정보 입력 =====")
    
    user_id = input("사용자 ID를 입력하세요: ")
    mbti = input("MBTI를 입력하세요 (예: INFP): ").upper()
    birthday = input("생일을 입력하세요 (예: 1990-01-01): ")
    gender = input("성별을 입력하세요 (남성/여성): ")
    age = input("연령대를 입력하세요 (예: 20대, 30대): ")
    
    # 성향 특성 추가
    traits = {}
    print("\n성향 특성을 입력하세요 (1-10 사이 점수, 입력 완료 시 빈 칸으로 제출)")
    
    while True:
        trait_name = input("특성 이름 (예: 감정적, 창의적, 내향적): ")
        if not trait_name:
            break
            
        while True:
            try:
                trait_score = int(input(f"{trait_name}의 점수 (1-10): "))
                if 1 <= trait_score <= 10:
                    traits[trait_name] = trait_score
                    break
                else:
                    print("점수는 1에서 10 사이 숫자여야 합니다.")
            except ValueError:
                print("숫자를 입력하세요.")
    
    # 간단한 프롬프트 생성
    traits_desc = []
    for trait, score in traits.items():
        level = "매우 " if score >= 8 else "" if score >= 5 else "약간 "
        traits_desc.append(f"{level}{trait}")
    
    traits_str = ", ".join(traits_desc)
    prompt = f"사용자는 {mbti} 성향의 {age} {gender}으로, {traits_str}한 특성을 가지고 있습니다."
    
    # 사용자 데이터 구조화
    user_data = {
        "user_id": user_id,
        "user_tendency": {
            "mbti": mbti,
            "birthday": birthday,
            "gender": gender,
            "age": age,
            "traits": traits,
            "prompt": prompt
        }
    }
    
    return user_id, user_data

def save_user_data(user_tendency, user_id, user_data):
    """사용자 데이터 저장"""
    print(f"\n===== {user_id}의 성향 데이터 저장 =====")
    
    # 데이터 저장
    user_tendency.add_tendency_events(user_id, [user_data])
    
    # 저장 경로 출력
    index_path = user_tendency._get_user_tendency_path(user_id)
    print(f"데이터가 저장된 경로: {os.path.abspath(index_path)}")
    
    return index_path

def check_saved_data(index_path):
    """저장된 JSON 데이터 확인"""
    print("\n===== 저장된 데이터 확인 =====")
    
    json_path = os.path.join(index_path, "events.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("JSON 파일 로드 성공!")
        
        # 원본 이벤트 데이터 출력
        if data.get('original_events'):
            user_data = data['original_events'][0]
            
            print("\n저장된 사용자 정보:")
            print(f"- 사용자 ID: {user_data.get('user_id', '정보 없음')}")
            
            tendency = user_data.get('user_tendency', {})
            print(f"- MBTI: {tendency.get('mbti', '정보 없음')}")
            print(f"- 생일: {tendency.get('birthday', '정보 없음')}")
            print(f"- 성별: {tendency.get('gender', '정보 없음')}")
            print(f"- 연령대: {tendency.get('age', '정보 없음')}")
            
            print("\n- 성향 특성:")
            traits = tendency.get('traits', {})
            for trait, score in traits.items():
                print(f"  · {trait}: {score}")
            
            print(f"\n- 프롬프트: {tendency.get('prompt', '정보 없음')}")
        
        print(f"\n업데이트 시간: {data.get('updated_at', '정보 없음')}")
    else:
        print(f"JSON 파일을 찾을 수 없습니다: {json_path}")

def search_user_tendency(user_tendency, user_id):
    """사용자 성향 검색"""
    print(f"\n===== {user_id}의 성향 검색 =====")
    
    # 벡터스토어 로드
    vectorstore = user_tendency.load_user_tendency(user_id)
    
    if vectorstore:
        print("벡터스토어 로드 성공!")
        
        # 검색어 입력
        query = input("\n사용자 성향에 대한 검색어를 입력하세요 (예: 감정적, INFP): ")
        if query:
            results = vectorstore.similarity_search(query, k=1)
            if results:
                print(f"\n검색 결과: {results[0].page_content}")
            else:
                print("검색 결과가 없습니다.")
    else:
        print("벡터스토어 로드 실패")

def main():
    try:
        print("===== UserTendency 테스트 프로그램 =====")
        
        # 환경 설정
        setup_environment()
        
        # UserTendency 객체 생성
        user_tendency = UserTendency()
        
        # 사용자 정보 입력
        user_id, user_data = get_user_info()
        
        # 사용자 데이터 저장
        index_path = save_user_data(user_tendency, user_id, user_data)
        
        # 저장된 데이터 확인
        check_saved_data(index_path)
        
        # 사용자 성향 검색
        search_user_tendency(user_tendency, user_id)
        
        print("\n===== 테스트 완료 =====")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()