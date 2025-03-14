import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../../auth/data/repositories/firebase_user_repository.dart';
import '../../../../injection.dart';
import '../widgets/result_card.dart';
import 'package:dio/dio.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../../chat/data/datasources/chat_service.dart';

class DevTestPage extends StatefulWidget {
  const DevTestPage({super.key});

  @override
  State<DevTestPage> createState() => _DevTestPageState();
}

class _DevTestPageState extends State<DevTestPage> {
  final _userRepository = getIt<FirebaseUserRepository>();
  final _uidController = TextEditingController();
  final _resultController = TextEditingController();
  bool _isLoading = false;

  // 새로운 상태 변수들 추가
  final _startDateController = TextEditingController();
  final _endDateController = TextEditingController();
  final _calendarResultController = TextEditingController();
  final _eventTitleController = TextEditingController();
  final _aiResultController = TextEditingController();
  final String _selectedEmotion = '좋음';
  final DateTime _startDate = DateTime.now();
  final DateTime _endDate = DateTime.now();

  final _dio = Dio();
  final _serverUrlController = TextEditingController();
  final _responseController = TextEditingController();

  // 서버 통신을 위한 변수들
  final _baseUrlController =
      TextEditingController(text: 'http://10.0.2.2:8000'); // 안드로이드 에뮬레이터용 로컬호스트
  final _userIdController = TextEditingController();
  final _messageController = TextEditingController();
  final _eventSummaryController = TextEditingController();
  final int _emotionScore = 3;
  final _tokenController = TextEditingController();

  // Google 로그인 인스턴스 수정
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'https://www.googleapis.com/auth/calendar', // 전체 캘린더 접근 권한
      'https://www.googleapis.com/auth/calendar.events',
    ],
  );

  // 성향 테스트를 위한 변수 추가
  final _mbtiController = TextEditingController(text: 'ENFP');
  final _personalityModeController = TextEditingController(text: 'daily');
  final _personalityKeyController = TextEditingController(text: 'mbti');
  final _personalityIdController = TextEditingController(text: '123');
  final List<String> _selectedTraits = ['창의적', '외향적', '직관적'];

  @override
  void initState() {
    super.initState();
    _startDateController.text = DateTime.now().toString().split(' ')[0];
    _endDateController.text =
        DateTime.now().add(const Duration(days: 30)).toString().split(' ')[0];

    // Dio 설정
    _dio.options.validateStatus = (status) {
      return true; // 모든 상태 코드를 허용하여 오류 응답도 확인할 수 있도록 함
    };

    // 현재 로그인된 사용자 ID 가져오기
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      _userIdController.text = user.uid;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('백엔드 API 테스트'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _baseUrlController,
              decoration: const InputDecoration(
                labelText: '서버 URL',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _tokenController,
                    decoration: const InputDecoration(
                      labelText: 'Google 인증 토큰',
                      border: OutlineInputBorder(),
                    ),
                    readOnly: true,
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _refreshGoogleToken,
                  child: const Text('토큰 갱신'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _userIdController,
              decoration: const InputDecoration(
                labelText: '사용자 이메일',
                border: OutlineInputBorder(),
              ),
              readOnly: true,
            ),
            const SizedBox(height: 24),
            const Text('API 테스트',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _testSyncCalendar,
              child: const Text('캘린더 동기화'),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testInitChat,
              child: const Text('채팅 초기화'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _messageController,
              decoration: const InputDecoration(
                labelText: '메시지',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testSendMessage,
              child: const Text('메시지 전송'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _eventSummaryController,
              decoration: const InputDecoration(
                labelText: '일정 제목',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testUpdateEmotion,
              child: const Text('감정 상태 업데이트'),
            ),
            const SizedBox(height: 16),
            const Text('추가 API 테스트',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),

            // 성향 동기화
            ElevatedButton(
              onPressed: _testSyncPersonality,
              child: const Text('성향 동기화'),
            ),

            // 캘린더 조회
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _startDateController,
                    decoration: const InputDecoration(
                      labelText: '시작일',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _endDateController,
                    decoration: const InputDecoration(
                      labelText: '종료일',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testGetCalendarEvents,
              child: const Text('캘린더 조회'),
            ),

            // 성향 조회 (모드별)
            const SizedBox(height: 8),
            TextField(
              controller: _personalityModeController,
              decoration: const InputDecoration(
                labelText: '성향 모드',
                border: OutlineInputBorder(),
                hintText: 'daily, weekly, monthly',
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testGetPersonalityByMode,
              child: const Text('성향 조회 (모드별)'),
            ),

            // 성향 조회 (키값 기준)
            const SizedBox(height: 8),
            TextField(
              controller: _personalityKeyController,
              decoration: const InputDecoration(
                labelText: '성향 키',
                border: OutlineInputBorder(),
                hintText: 'mbti, enneagram',
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testGetPersonalityByKey,
              child: const Text('성향 조회 (키값 기준)'),
            ),

            // 성향 상세 조회
            const SizedBox(height: 8),
            TextField(
              controller: _personalityIdController,
              decoration: const InputDecoration(
                labelText: '성향 ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _testGetPersonalityDetail,
              child: const Text('성향 상세 조회'),
            ),

            const SizedBox(height: 16),
            ResultCard(
              controller: _responseController,
              isLoading: _isLoading,
            ),

            // 대화 기록 테스트 섹션 추가
            _buildChatHistoryTestSection(),
          ],
        ),
      ),
    );
  }

  Future<void> _testSyncCalendar() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.post(
        '${_baseUrlController.text}/sync-calendar',
        data: {
          'token': _tokenController.text,
          'user_id': _userIdController.text,
        },
      );
      _showSuccess('캘린더 동기화', response);
    } catch (e) {
      _showError('캘린더 동기화 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testInitChat() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.post(
        '${_baseUrlController.text}/init-chat',
        data: {
          'user_id': _userIdController.text,
        },
      );
      _showSuccess('채팅 초기화', response);
    } catch (e) {
      _showError('채팅 초기화 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testSendMessage() async {
    if (!_validateInputs() || _messageController.text.isEmpty) {
      _showError('메시지를 입력해주세요');
      return;
    }

    setState(() => _isLoading = true);
    try {
      final response = await _dio.post(
        '${_baseUrlController.text}/chat',
        data: {
          'user_id': _userIdController.text,
          'message': _messageController.text,
        },
      );
      _showSuccess('메시지 전송', response);
    } catch (e) {
      _showError('메시지 전송 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testUpdateEmotion() async {
    if (!_validateInputs() || _eventSummaryController.text.isEmpty) {
      _showError('일정 제목을 입력해주세요');
      return;
    }

    setState(() => _isLoading = true);
    try {
      final now = DateTime.now();
      final response = await _dio.post(
        '${_baseUrlController.text}/emotion',
        data: {
          'user_id': _userIdController.text,
          'event_date': now.toIso8601String().split('T')[0],
          'event_time': '${now.hour}:${now.minute}',
          'event_summary': _eventSummaryController.text,
          'emotion_score': _emotionScore,
        },
      );
      _showSuccess('감정 상태 업데이트', response);
    } catch (e) {
      _showError('감정 상태 업데이트 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _refreshGoogleToken() async {
    try {
      setState(() => _isLoading = true);

      // 현재 로그인된 사용자 확인
      GoogleSignInAccount? currentUser = _googleSignIn.currentUser;

      currentUser ??= await _googleSignIn.signIn();

      if (currentUser == null) {
        _showError('Google 로그인이 필요합니다');
        return;
      }

      // 인증 정보 가져오기
      final googleAuth = await currentUser.authentication;

      setState(() {
        _tokenController.text = googleAuth.accessToken ?? '';
        _userIdController.text = currentUser!.email;
      });

      _showSuccess(
          '토큰 갱신',
          Response(
            requestOptions: RequestOptions(path: ''),
            data: {
              'access_token': googleAuth.accessToken,
              'user_email': currentUser.email,
            },
            statusCode: 200,
          ));
    } catch (e) {
      print('Google Sign In Error: $e');
      _showError('토큰 갱신 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testSyncPersonality() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.post(
        '${_baseUrlController.text}/personality/sync',
        data: {
          'user_id': _userIdController.text,
          'mbti': _mbtiController.text,
          'traits': _selectedTraits,
        },
        options: Options(headers: _getAuthHeaders()),
      );
      _showSuccess('성향 동기화', response);
    } catch (e) {
      _showError('성향 동기화 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testGetCalendarEvents() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.get(
        '${_baseUrlController.text}/calendar/events',
        queryParameters: {
          'user_id': _userIdController.text,
          'start_date': _startDateController.text,
          'end_date': _endDateController.text,
        },
        options: Options(headers: _getAuthHeaders()),
      );
      _showSuccess('캘린더 조회', response);
    } catch (e) {
      _showError('캘린더 조회 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testGetPersonalityByMode() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.get(
        '${_baseUrlController.text}/personality/mode/${_personalityModeController.text}',
        queryParameters: {
          'user_id': _userIdController.text,
        },
        options: Options(headers: _getAuthHeaders()),
      );
      _showSuccess('성향 조회 (모드별)', response);
    } catch (e) {
      _showError('성향 조회 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testGetPersonalityByKey() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.get(
        '${_baseUrlController.text}/personality/key/${_personalityKeyController.text}',
        queryParameters: {
          'user_id': _userIdController.text,
        },
        options: Options(headers: _getAuthHeaders()),
      );
      _showSuccess('성향 조회 (키값 기준)', response);
    } catch (e) {
      _showError('성향 조회 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _testGetPersonalityDetail() async {
    if (!_validateInputs()) return;

    setState(() => _isLoading = true);
    try {
      final response = await _dio.get(
        '${_baseUrlController.text}/personality/detail/${_personalityIdController.text}',
        queryParameters: {
          'user_id': _userIdController.text,
        },
        options: Options(headers: _getAuthHeaders()),
      );
      _showSuccess('성향 상세 조회', response);
    } catch (e) {
      _showError('성향 상세 조회 실패: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // 인증 헤더 생성 헬퍼 메서드
  Map<String, String> _getAuthHeaders() {
    final headers = {
      'Content-Type': 'application/json',
    };

    if (_tokenController.text.isNotEmpty) {
      headers['Authorization'] = 'Bearer ${_tokenController.text}';
    }

    return headers;
  }

  bool _validateInputs() {
    if (_baseUrlController.text.isEmpty || _userIdController.text.isEmpty) {
      _showError('서버 URL과 사용자 이메일을 입력해주세요');
      return false;
    }
    return true;
  }

  void _showSuccess(String operation, Response response) {
    _responseController.text = '''
테스트 시간: ${DateTime.now()}
작업: $operation
상태 코드: ${response.statusCode}
응답 데이터:
${response.data}
''';
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  // 대화 기록 테스트 섹션 추가
  Widget _buildChatHistoryTestSection() {
    return Card(
      margin: const EdgeInsets.all(8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '대화 기록 테스트',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _userIdController,
              decoration: const InputDecoration(
                labelText: '사용자 ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _testChatHistory,
              child: const Text('대화 기록 조회'),
            ),
            const SizedBox(height: 16),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else
              TextField(
                controller: _responseController,
                maxLines: 10,
                readOnly: true,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: '대화 기록 결과가 여기에 표시됩니다',
                ),
              ),
          ],
        ),
      ),
    );
  }

  // 대화 기록 테스트 메소드
  Future<void> _testChatHistory() async {
    if (_userIdController.text.isEmpty) {
      _showError('사용자 ID를 입력해주세요');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final chatService = getIt<ChatService>();
      final messages = await chatService.getChatHistory(_userIdController.text);

      _responseController.text = '대화 기록 조회 성공\n\n';
      _responseController.text += '총 ${messages.length}개의 메시지\n\n';

      for (var message in messages) {
        _responseController.text +=
            '${message.isUser ? "사용자" : "AI"}: ${message.text}\n';
        _responseController.text += '시간: ${message.timestamp}\n\n';
      }
    } catch (e) {
      _responseController.text = '대화 기록 조회 실패: $e';
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _userIdController.dispose();
    _messageController.dispose();
    _eventSummaryController.dispose();
    _responseController.dispose();
    _tokenController.dispose();
    _mbtiController.dispose();
    _personalityModeController.dispose();
    _personalityKeyController.dispose();
    _personalityIdController.dispose();
    super.dispose();
  }
}
