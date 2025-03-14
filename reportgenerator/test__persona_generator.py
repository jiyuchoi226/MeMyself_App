import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# 프로젝트 루트 디렉토리를 PYTHONPATH에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# .env 파일 로드
load_dotenv()

from persona_generator import PersonaGenerator

def main():
    # 테스트할 사용자 ID
    user_id = "ica.2team02@gmail.com"

    try:
        # 리포트 생성기 초기화
        persona_generator = PersonaGenerator(user_id)
        
        # 회고 리포트 생성
        print("\n=== 페르소나 프롬프트 생성 시작 ===")
        print("처리 중입니다... (최대 1분 소요될 수 있습니다)")
        result = persona_generator.generate_persona_prompt()
                
        # 회고 리포트
        print("\n2. 프롬프트:")
        print("-" * 40)
        print(result["report"])
        print("-" * 40)

    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()