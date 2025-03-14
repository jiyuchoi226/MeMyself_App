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

from app.retrospective_report import RetrospectiveReportGenerator

def main():
    # 테스트할 사용자 ID
    user_id = "ica.2team02@gmail.com"

    try:
        # 리포트 생성기 초기화
        report_generator = RetrospectiveReportGenerator(user_id)
        
        # 회고 리포트 생성
        print("\n=== 회고 리포트 생성 시작 ===")
        print("처리 중입니다... (최대 1분 소요될 수 있습니다)")
        result = report_generator.generate_retrospective_report()
        
        # 결과 출력
        print("\n=== 생성 결과 ===")
        
        # 데이터 분석 결과 (추가된 부분)
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