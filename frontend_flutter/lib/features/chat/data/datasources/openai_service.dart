import 'package:dart_openai/dart_openai.dart';

class OpenAIService {
  static const _apiKey =
      "sk-svcacct-zY39Ocq6wykqfJZEumHBQoRFpUFYZtGEOwb3jtsbGr-dm8eWDf5kdall_hmL4vdT3BlbkFJ0AZRR89htmNa7bTUqAsXLQ43IXJ8-5vBlegHq8yDx947U6YK_rNhbY6YrV7YT_wA";

  OpenAIService() {
    OpenAI.apiKey = _apiKey;
  }

  Future<String> getReflectionResponse({
    required String mbti,
    required String gender,
    required int age,
    required String eventTitle,
    required String emotion,
    required DateTime eventDate,
  }) async {
    final systemPrompt = '''
당신은 MBTI 전문 상담사입니다. 사용자의 MBTI($mbti)를 고려하여 맞춤형 대화를 제공합니다.
- 성별: $gender
- 나이: $age세
- MBTI: $mbti
- 일정: $eventTitle
- 감정: $emotion
- 날짜: ${eventDate.toString().split(' ')[0]}

위 정보를 바탕으로:
1. MBTI 특성을 고려한 공감적 대화를 해주세요
2. 해당 감정에 대한 이해를 보여주세요
3. MBTI 유형별 특성을 활용한 조언을 제공해주세요
4. 친근하고 따뜻한 톤으로 대화해주세요
5. 답변은 2-3문장으로 간단하게 해주세요
''';

    try {
      final chatCompletion = await OpenAI.instance.chat.create(
        model: 'gpt-4o',
        messages: [
          OpenAIChatCompletionChoiceMessageModel(
            role: OpenAIChatMessageRole.system,
            content: [
              OpenAIChatCompletionChoiceMessageContentItemModel.text(
                systemPrompt,
              ),
            ],
          ),
          OpenAIChatCompletionChoiceMessageModel(
            role: OpenAIChatMessageRole.user,
            content: [
              OpenAIChatCompletionChoiceMessageContentItemModel.text(
                "이 일정에 대해 어떻게 생각하시나요?",
              ),
            ],
          ),
        ],
      );

      if (chatCompletion.choices.isEmpty) {
        return '죄송합니다. 응답을 생성할 수 없습니다.';
      }

      final messageContent = chatCompletion.choices.first.message.content;
      if (messageContent != null && messageContent.isNotEmpty) {
        return messageContent.first.text ?? '죄송합니다. 응답을 생성할 수 없습니다.';
      }

      return '죄송합니다. 응답을 생성할 수 없습니다.';
    } catch (e) {
      print('OpenAI Error: $e');
      return '죄송합니다. 지금은 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.';
    }
  }

  Future<String> sendMessage(String prompt) async {
    try {
      final chatCompletion = await OpenAI.instance.chat.create(
        model: 'gpt-4',
        messages: [
          OpenAIChatCompletionChoiceMessageModel(
            role: OpenAIChatMessageRole.user,
            content: [
              OpenAIChatCompletionChoiceMessageContentItemModel.text(prompt),
            ],
          ),
        ],
      );

      if (chatCompletion.choices.isEmpty) {
        return '죄송합니다. 응답을 생성할 수 없습니다.';
      }

      final messageContent = chatCompletion.choices.first.message.content;
      if (messageContent != null && messageContent.isNotEmpty) {
        return messageContent.first.text ?? '죄송합니다. 응답을 생성할 수 없습니다.';
      }

      return '죄송합니다. 응답을 생성할 수 없습니다.';
    } catch (e) {
      print('OpenAI Error: $e');
      return '죄송합니다. 지금은 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.';
    }
  }
}
