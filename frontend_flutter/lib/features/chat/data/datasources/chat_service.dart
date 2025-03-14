import 'package:dio/dio.dart';
import '../../domain/entities/message.dart';
import '../datasources/chat_local_storage.dart';
import 'package:firebase_auth/firebase_auth.dart';

class ChatService {
  final Dio _dio;
  final String baseUrl;
  final ChatLocalStorage _localStorage = ChatLocalStorage();

  ChatService({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://10.0.2.2:8000',
        _dio = Dio() {
    // Dio 인스턴스 초기화 시 인터셉터와 타임아웃 설정
    _dio.options.connectTimeout = const Duration(seconds: 20);
    _dio.options.receiveTimeout = const Duration(seconds: 20);
    _dio.options.sendTimeout = const Duration(seconds: 20);

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          print('API 요청: ${options.uri}');
          return handler.next(options);
        },
        onResponse: (response, handler) {
          print('API 응답: ${response.statusCode}');
          return handler.next(response);
        },
        onError: (DioException e, handler) {
          print('Dio 오류 발생: ${e.type}, ${e.message}');

          // 네트워크 오류 처리
          if (e.type == DioExceptionType.connectionTimeout ||
              e.type == DioExceptionType.receiveTimeout ||
              e.type == DioExceptionType.sendTimeout) {
            // 타임아웃 발생 시 로컬 폴백 응답 반환
            return handler.resolve(
              Response(
                requestOptions: e.requestOptions,
                data: {
                  'fallback': true,
                  'message': '네트워크 연결이 원활하지 않습니다. 로컬 데이터를 사용합니다.'
                },
                statusCode: 200,
              ),
            );
          }

          // 서버 오류 처리
          if (e.response?.statusCode != null &&
              e.response!.statusCode! >= 500) {
            return handler.resolve(
              Response(
                requestOptions: e.requestOptions,
                data: {
                  'fallback': true,
                  'message': '서버에 일시적인 문제가 발생했습니다. 로컬 데이터를 사용합니다.'
                },
                statusCode: 200,
              ),
            );
          }

          return handler.next(e);
        },
      ),
    );
  }

  Future<String> initializeChat(
    String userId, {
    required String eventTitle,
    required String emotion,
    required DateTime eventDate,
    bool forceRefresh = true,
  }) async {
    try {
      // 로컬 저장소에서 이전 대화 기록 확인
      final messages = await ChatLocalStorage.getMessagesStatic(userId);

      // forceRefresh가 false이고 이전 대화가 있으면 마지막 AI 메시지 반환
      if (!forceRefresh && messages.isNotEmpty) {
        for (int i = messages.length - 1; i >= 0; i--) {
          if (!messages[i].isUser) {
            print('로컬 캐시에서 마지막 AI 메시지 반환: ${messages[i].text}');
            return messages[i].text;
          }
        }
      }

      // 엔드포인트 URL 확인 및 수정
      final endpoint = '/init-chat';
      print('chat-init API 호출 시작: $baseUrl$endpoint');

      // 요청 데이터 로깅
      final requestData = {
        'user_id': userId,
        'event_title': eventTitle,
        'emotion': emotion,
        'event_date': eventDate.toIso8601String(),
      };
      print('chat-init 요청 데이터: $requestData');

      // 새로운 Dio 인스턴스 생성 (기존 인스턴스와 분리)
      final initDio = Dio()
        ..options.connectTimeout = const Duration(seconds: 30)
        ..options.receiveTimeout = const Duration(seconds: 30)
        ..options.sendTimeout = const Duration(seconds: 30);

      // 디버깅을 위한 인터셉터 추가
      initDio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            print('init-chat 요청 URL: ${options.uri}');
            print('init-chat 요청 헤더: ${options.headers}');
            print('init-chat 요청 데이터: ${options.data}');
            return handler.next(options);
          },
          onResponse: (response, handler) {
            print('init-chat 응답 상태 코드: ${response.statusCode}');
            print('init-chat 응답 데이터: ${response.data}');
            return handler.next(response);
          },
          onError: (DioException e, handler) {
            print('init-chat 오류 타입: ${e.type}');
            print('init-chat 오류 메시지: ${e.message}');
            if (e.response != null) {
              print('init-chat 오류 응답 코드: ${e.response?.statusCode}');
              print('init-chat 오류 응답 데이터: ${e.response?.data}');
            }
            return handler.next(e);
          },
        ),
      );

      // API 호출 시도
      print('chat-init API 호출 직전');
      final response = await initDio.post(
        '$baseUrl$endpoint',
        data: requestData,
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json',
          },
        ),
      );
      print('chat-init API 호출 완료');

      print('chat-init API 응답: ${response.statusCode}, ${response.data}');

      if (response.statusCode == 200) {
        // 응답 데이터 구조 확인
        final responseData = response.data;
        String welcomeMessage;

        // 응답 구조에 따라 메시지 추출
        if (responseData is Map<String, dynamic>) {
          welcomeMessage = responseData['message'] ??
              responseData['response'] ??
              '안녕하세요! 무엇을 도와드릴까요?';
        } else if (responseData is String) {
          welcomeMessage = responseData;
        } else {
          welcomeMessage = '안녕하세요! 무엇을 도와드릴까요?';
        }

        print('chat-init 환영 메시지: $welcomeMessage');

        // 환영 메시지 저장
        await _localStorage.saveMessage(
          userId,
          Message(
            text: welcomeMessage,
            isUser: false,
            timestamp: DateTime.now(),
          ),
        );

        return welcomeMessage;
      } else {
        throw Exception('채팅 초기화 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('채팅 초기화 오류 상세: $e');
      if (e is DioException) {
        print('Dio 오류 타입: ${e.type}');
        print('Dio 오류 메시지: ${e.message}');
        if (e.response != null) {
          print('응답 상태 코드: ${e.response?.statusCode}');
          print('응답 데이터: ${e.response?.data}');
        }
      }

      // 오류 발생 시 기본 메시지 반환 및 로컬에 저장
      const fallbackMessage = '현재 서버 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.';

      try {
        await _localStorage.saveMessage(
          userId,
          Message(
            text: fallbackMessage,
            isUser: false,
            timestamp: DateTime.now(),
          ),
        );
      } catch (saveError) {
        print('오류 메시지 저장 실패: $saveError');
      }

      return fallbackMessage;
    }
  }

  Future<Message> sendMessage(String text, String chatId) async {
    try {
      // 사용자 메시지 생성
      final userMessage = Message(
        text: text,
        isUser: true,
        timestamp: DateTime.now(),
      );

      // 로컬에 사용자 메시지 저장
      await _localStorage.saveMessage(chatId, userMessage);

      // 현재 로그인한 사용자 ID 가져오기
      final user = FirebaseAuth.instance.currentUser;
      final userId = user?.uid ?? 'anonymous';

      // 서버에 메시지 전송 (필수 필드 추가)
      final response = await _dio.post(
        '$baseUrl/chat',
        data: {
          'message': text,
          'chat_id': chatId,
          'user_id': userId, // 필수 필드 추가
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        // AI 응답 메시지 생성
        final aiMessage = Message(
          text: response.data['response'] ?? '죄송합니다, 응답을 생성할 수 없습니다.',
          isUser: false,
          timestamp: DateTime.now(),
        );

        // 로컬에 AI 응답 저장
        await _localStorage.saveMessage(chatId, aiMessage);

        return aiMessage;
      } else {
        throw Exception('메시지 전송 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('메시지 전송 오류: $e');

      // 오류 발생 시 오류 메시지 반환
      final errorMessage = Message(
        text: '죄송합니다, 현재 서버 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.',
        isUser: false,
        timestamp: DateTime.now(),
      );

      // 오류 메시지도 저장
      try {
        await _localStorage.saveMessage(chatId, errorMessage);
      } catch (saveError) {
        print('오류 메시지 저장 실패: $saveError');
      }

      return errorMessage;
    }
  }

  /// 채팅 기록 조회
  /// [userId] 사용자 ID (이메일)
  Future<List<Message>> getChatHistory(String userId) async {
    try {
      print('채팅 기록 조회 요청: $baseUrl/get-chat-history?user_id=$userId');

      // URL 인코딩
      final encodedUserId = Uri.encodeComponent(userId);

      // 새로운 Dio 인스턴스 생성하여 타임아웃 설정 변경
      final chatDio = Dio()
        ..options.connectTimeout = const Duration(seconds: 30)
        ..options.receiveTimeout = const Duration(seconds: 30)
        ..options.sendTimeout = const Duration(seconds: 30);

      // GET 요청으로 변경하고 쿼리 파라미터로 user_id만 전달
      final response = await chatDio.get(
        '$baseUrl/get-chat-history',
        queryParameters: {'user_id': encodedUserId},
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final List<Message> messages = [];
        final data = response.data;

        print('서버 응답: $data');

        // 응답 구조에 맞게 파싱
        if (data['chat_history'] != null && data['chat_history'] is List) {
          for (var item in data['chat_history']) {
            if (item['user_message'] != null) {
              messages.add(Message(
                text: item['user_message'],
                isUser: true,
                timestamp: DateTime.parse(
                    item['timestamp'] ?? DateTime.now().toIso8601String()),
              ));
            }

            if (item['bot_message'] != null) {
              messages.add(Message(
                text: item['bot_message'],
                isUser: false,
                timestamp: DateTime.parse(
                    item['timestamp'] ?? DateTime.now().toIso8601String()),
              ));
            }
          }
        }

        print('서버에서 ${messages.length}개의 메시지를 가져왔습니다.');
        return messages;
      } else {
        final errorMessage = response.data['detail'] ?? '알 수 없는 오류가 발생했습니다';
        print('대화 기록 조회 실패: $errorMessage (상태 코드: ${response.statusCode})');

        // 서버 오류 시 로컬 저장소에서 가져오기 시도
        print('로컬 저장소에서 대화 기록 조회 시도');
        return await ChatLocalStorage.getMessagesStatic(userId);
      }
    } catch (e) {
      print('서버 API 호출 오류 상세: ${e.toString()}');
      if (e is DioException) {
        print('Dio 오류 타입: ${e.type}');
        print('Dio 오류 메시지: ${e.message}');
        print('Dio 응답 데이터: ${e.response?.data}');
        print('Dio 응답 상태 코드: ${e.response?.statusCode}');
      }
      print('로컬 저장소에서 대화 기록 조회 시도');

      // 오류 발생 시 로컬 저장소에서 가져오기
      return await ChatLocalStorage.getMessagesStatic(userId);
    }
  }
}

class TimeoutException implements Exception {
  final String message;
  TimeoutException(this.message);

  @override
  String toString() => message;
}
