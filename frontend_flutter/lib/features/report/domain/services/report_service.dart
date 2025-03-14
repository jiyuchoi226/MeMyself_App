import '../../../chat/data/datasources/openai_service.dart';

class ReportService {
  final OpenAIService _openAIService;

  ReportService(this._openAIService);

  Future<String> generateWeeklyReport(List<String> reflections) async {
    final prompt = '''
지난 일주일 동안의 회고를 분석하여 리포트를 생성해주세요:

회고 내용:
${reflections.join('\n')}

다음 형식으로 분석해주세요:
1. 이번 주 핵심 키워드
2. 감정 분석
3. 주요 활동 요약
4. 개선점 및 제안
''';

    return await _openAIService.sendMessage(prompt);
  }
}
