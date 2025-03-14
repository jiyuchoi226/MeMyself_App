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
        
        # 초기 회고 리포트 내용과 최종 리포트 내용을 저장할 변수 선언
        initial_report_content = ""
        final_report_content = ""
        
        # generate_retrospective_report 메소드를 수정하여 초기 리포트와 최종 리포트 모두 반환하도록 함
        # 이 부분은 RetrospectiveReportGenerator 클래스의 메소드를 오버라이드하는 방식으로 구현
        
        original_generate_report = report_generator.generate_retrospective_report
        
        def modified_generate_report():
            try:
                # 1단계: 데이터 로드 (FaissDataLoader 사용)
                data = report_generator.data_loader.get_data_for_report()
                
                # 2단계: 데이터 분석 프롬프트 생성
                data_analysis_prompt = report_generator._generate_data_analysis_prompt(data)
                
                # 3단계: 데이터 분석 LLM 호출
                print("\n=== 데이터 분석 진행 중... ===\n")
                analysis_response = report_generator.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "당신은 데이터 분석 전문가입니다. 사용자의 일정, 대화, 감정 데이터를 객관적으로 분석하여 정확하고 통찰력 있는 결과를 제공합니다."},
                        {"role": "user", "content": data_analysis_prompt},
                    ],
                    max_tokens=800,
                    temperature=0.1,
                )
                
                data_analysis_result = analysis_response.choices[0].message.content.strip()
                print("\n=== 데이터 분석 결과 ===\n")
                print(data_analysis_result)
                print("\n========================\n")
                
                # 4단계: 회고 리포트 프롬프트 생성
                report_prompt = report_generator._generate_report_prompt(data_analysis_result, data)
                
                # 5단계: 회고 리포트 LLM 호출
                print("\n=== 회고 리포트 생성 중... ===\n")
                report_response = report_generator.client.chat.completions.create(
                    model="gpt-4.5-preview",
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

                initial_report = report_response.choices[0].message.content.strip()
                print("\n=== 회고 리포트 생성 완료 ===\n")
                print(initial_report)
                print("\n=== 초기 회고 리포트 내용 출력 완료 ===\n")
                
                # 변수에 저장
                nonlocal initial_report_content
                initial_report_content = initial_report
                
                # 6단계: 사용자 성향 반영 리포트 생성
                tendency_prompt = report_generator._get_latest_user_tendency_prompt()
                final_report = report_generator._apply_user_tendency_to_report(initial_report, tendency_prompt)
                print("\n=== 사용자 성향 반영 리포트 생성 완료 ===\n")
                print(final_report)
                print("\n=== 최종 회고 리포트 내용 출력 완료 ===\n")
                
                # 변수에 저장
                nonlocal final_report_content
                final_report_content = final_report

                # 7단계: 리포트 저장
                report_path = os.path.join(
                    report_generator.data_loader.base_path,
                    report_generator.user_id,
                    "retrospective_reports",
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_report.json",
                )
                os.makedirs(os.path.dirname(report_path), exist_ok=True)

                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "generated_at": datetime.now().isoformat(),
                            "data_analysis": data_analysis_result,
                            "initial_report": initial_report,
                            "final_report": final_report,
                            "tendency_prompt": tendency_prompt
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )

                # 두 가지 리포트 모두 반환
                return {
                    "message": "회고 리포트 생성 성공", 
                    "report": final_report,
                    "analysis": data_analysis_result,
                    "initial_report": initial_report,
                    "final_report": final_report
                }

            except Exception as e:
                print(f"회고 리포트 생성 중 오류: {e}")
                raise Exception(f"회고 리포트 생성 실패: {e}")
        
        # 원래 메소드를 수정된 메소드로 대체
        report_generator.generate_retrospective_report = modified_generate_report
        
        # 회고 리포트 생성
        print("\n=== 회고 리포트 생성 시작 ===")
        print("처리 중입니다... (최대 2분 소요될 수 있습니다)")
        result = report_generator.generate_retrospective_report()
        
        # 결과 출력
        print("\n=== 생성 결과 요약 ===")
        
        # 데이터 분석 결과
        if "analysis" in result:
            print("\n1. 데이터 분석 결과:")
            print("-" * 80)
            print(result["analysis"])
            print("-" * 80)
        
        # 초기 회고 리포트와 최종 회고 리포트 비교
        print("\n2. 회고 리포트 비교:")
        print("\n=== 초기 회고 리포트 (사용자 성향 반영 전) ===")
        print("-" * 80)
        print(result["initial_report"])
        print("-" * 80)
        
        print("\n=== 최종 회고 리포트 (사용자 성향 반영 후) ===")
        print("-" * 80)
        print(result["final_report"])
        print("-" * 80)

    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()