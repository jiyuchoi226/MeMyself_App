import 'package:flutter/material.dart';
import '../../../../core/presentation/widgets/gnb.dart';
import 'package:intl/intl.dart';
import '../../../../injection.dart';
import 'package:firebase_auth/firebase_auth.dart' hide UserMetadata;
import '../../../auth/data/repositories/firebase_user_repository.dart';
import '../../../../core/presentation/widgets/lumy_profile_header.dart';
import '../../data/datasources/chat_service.dart';
import '../../domain/entities/message.dart';
import '../../data/datasources/chat_local_storage.dart';

class ReflectionChatPage extends StatefulWidget {
  final String eventTitle;
  final String emotion;
  final DateTime eventDate;
  final String eventId;

  const ReflectionChatPage({
    super.key,
    required this.eventTitle,
    required this.emotion,
    required this.eventDate,
    required this.eventId,
  });

  @override
  State<ReflectionChatPage> createState() => _ReflectionChatPageState();
}

class _ReflectionChatPageState extends State<ReflectionChatPage> {
  final TextEditingController _messageController = TextEditingController();
  List<Message> _messages = [];
  bool _isLoading = true;
  late ChatService _chatService;
  final ScrollController _scrollController = ScrollController();
  String? _error;

  @override
  void initState() {
    super.initState();
    _chatService = getIt<ChatService>();
    _initializeChat();
  }

  Future<void> _initializeChat() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        setState(() {
          _error = '로그인이 필요합니다.';
          _isLoading = false;
        });
        return;
      }

      // Firebase에서 사용자 메타데이터 가져오기
      final userRepository = getIt<FirebaseUserRepository>();
      final metadata = await userRepository.getUserMetadata(user.uid);

      if (metadata == null) {
        setState(() {
          _error = '사용자 정보를 찾을 수 없습니다.';
          _isLoading = false;
        });
        return;
      }

      // 초기 메시지 생성
      final initialMessage = await _chatService.initializeChat(
        user.uid,
        eventTitle: widget.eventTitle,
        emotion: widget.emotion,
        eventDate: widget.eventDate,
      );

      // 채팅 기록 로드
      await _loadChatHistory();

      // 초기 메시지 추가
      if (initialMessage.isNotEmpty && _messages.isEmpty) {
        setState(() {
          _messages.add(Message(
            text: initialMessage,
            isUser: false,
            timestamp: DateTime.now(),
          ));
          _isLoading = false;
        });
      } else {
        setState(() {
          _isLoading = false;
        });
      }

      // 스크롤 맨 아래로
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollToBottom();
      });
    } catch (e) {
      print('초기화 오류: $e');
      setState(() {
        _error = '채팅을 초기화하는 중 오류가 발생했습니다: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _loadChatHistory() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return;

      // ChatService를 사용하여 채팅 기록 가져오기
      final messages = await _chatService.getChatHistory(user.email ?? '');

      setState(() {
        _messages = messages;
        _isLoading = false;
      });
    } catch (e) {
      print('채팅 기록 조회 오류: $e');
      setState(() {
        _isLoading = false;
        _error = e.toString();
      });
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(
                  bottom: BorderSide(
                    color: Colors.grey[200]!,
                    width: 1,
                  ),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: GNB(
                selectedIndex: 1,
                onItemSelected: (index) {
                  switch (index) {
                    case 0:
                      Navigator.pushReplacementNamed(context, '/home');
                      break;
                    case 1:
                      // 현재 페이지이므로 아무것도 하지 않음
                      break;
                    case 2:
                      Navigator.pushReplacementNamed(context, '/report');
                      break;
                    case 3:
                      Navigator.pushReplacementNamed(context, '/settings');
                      break;
                  }
                },
              ),
            ),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _messages.length + (_isLoading ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index == _messages.length) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  return _ChatBubble(
                    message: _messages[index].text,
                    isUser: _messages[index].isUser,
                    timestamp: _messages[index].timestamp,
                    showAvatar: true,
                  );
                },
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(
                  top: BorderSide(color: Colors.grey[300]!, width: 1),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      keyboardType: TextInputType.text,
                      textInputAction: TextInputAction.send,
                      maxLines: 1,
                      decoration: InputDecoration(
                        hintText: '메시지를 입력하세요',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        filled: true,
                        fillColor: Colors.grey[100],
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                      textCapitalization: TextCapitalization.sentences,
                      enableSuggestions: true,
                      enableInteractiveSelection: true,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.black,
                        height: 1.3,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _sendMessage,
                    icon: const Icon(Icons.send),
                    color: Colors.deepPurple,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;

    final messageText = _messageController.text.trim();
    _messageController.clear();

    setState(() {
      // 사용자 메시지 추가
      _messages.add(Message(
        text: messageText,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
    });

    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('로그인이 필요합니다');
      }

      // 채팅 ID 생성 (이벤트 ID 사용)
      final chatId = widget.eventId;

      // 서버에 메시지 전송
      final response = await _chatService.sendMessage(messageText, chatId);

      // AI 응답 메시지 생성
      setState(() {
        _messages.add(response);
        _isLoading = false;
      });
    } catch (e) {
      print('메시지 전송 오류: $e');
      setState(() {
        _messages.add(Message(
          text: '죄송합니다, 오류가 발생했습니다: $e',
          isUser: false,
          timestamp: DateTime.now(),
        ));
        _isLoading = false;
      });
    }
  }
}

class _ChatBubble extends StatelessWidget {
  final String message;
  final bool isUser;
  final DateTime timestamp;
  final bool showAvatar;

  const _ChatBubble({
    required this.message,
    required this.isUser,
    required this.timestamp,
    this.showAvatar = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser && showAvatar) ...[
            const LumyProfileHeader(imageSize: 32, fontSize: 14),
            const SizedBox(width: 8),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment:
                  isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isUser ? Colors.deepPurple : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    message,
                    style: TextStyle(
                      color: isUser ? Colors.white : Colors.black,
                      height: 1.5,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  DateFormat('HH:mm').format(timestamp),
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              backgroundColor: Colors.grey[200],
              radius: 16,
              child: const Icon(Icons.person, size: 20),
            ),
          ],
        ],
      ),
    );
  }
}

Widget _buildChatHistoryHeader() {
  return Container(
    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
    color: Colors.grey[200],
    child: Row(
      children: [
        const Icon(Icons.history, size: 18),
        const SizedBox(width: 8),
        Text(
          '이전 대화 기록',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.grey[700],
          ),
        ),
      ],
    ),
  );
}
