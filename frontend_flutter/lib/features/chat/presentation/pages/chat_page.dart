import 'package:flutter/material.dart';
import '../../../../core/presentation/widgets/gnb.dart';
import '../../data/datasources/chat_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../../../injection.dart';
import 'dart:convert';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final ChatService _chatService = getIt<ChatService>();
  final TextEditingController _messageController = TextEditingController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = true;
  String? _error;
  String _chatId = '';

  @override
  void initState() {
    super.initState();
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

      // 채팅 ID 생성 (사용자 ID + 현재 날짜)
      _chatId = '${user.uid}_${DateTime.now().toIso8601String().split('T')[0]}';

      print('채팅 초기화 시작: $_chatId');
      print('사용자 ID: ${user.uid}');
      print('사용자 이메일: ${user.email}');

      // 이메일을 사용자 ID로 사용 (서버 요구사항에 따라 조정)
      final userId = user.email ?? user.uid;

      // 로컬 캐시를 무시하고 항상 서버에서 새로운 초기화 메시지 가져오기
      final response = await _chatService.initializeChat(
        userId,
        eventTitle: '일반 채팅',
        emotion: '보통',
        eventDate: DateTime.now(),
        forceRefresh: true, // 강제 새로고침 옵션 활성화
      );

      print('채팅 초기화 응답 받음: $response');

      if (mounted) {
        setState(() {
          _messages.add(ChatMessage(
            message: response,
            isUser: false,
            timestamp: DateTime.now(),
          ));
          _isLoading = false;
        });

        print('채팅 초기화 메시지 UI에 추가됨');
      }

      // 이전 대화 기록 로드 (약간의 지연 추가)
      await Future.delayed(const Duration(milliseconds: 500));
      _loadChatHistory(userId);
    } catch (e) {
      print('채팅 초기화 오류: $e');
      if (mounted) {
        setState(() {
          _error = '채팅을 초기화하는 중 오류가 발생했습니다: $e';
          _isLoading = false;
        });
      }
    }
  }

  // 이전 대화 기록 로드
  Future<void> _loadChatHistory(String userId) async {
    try {
      print('대화 기록 로드 시작: $userId');
      final messages = await _chatService.getChatHistory(userId);
      print('대화 기록 로드 완료: ${messages.length}개 메시지');

      if (messages.isNotEmpty && mounted) {
        setState(() {
          // 기존 메시지를 지우고 서버에서 가져온 메시지로 대체
          _messages.clear();

          // 메시지를 시간순으로 정렬하여 추가
          for (var message in messages) {
            _messages.add(ChatMessage(
              message: message.text,
              isUser: message.isUser,
              timestamp: message.timestamp,
            ));
          }
        });
      }
    } catch (e) {
      print('대화 기록 로드 오류: $e');
      // 오류가 발생해도 UI에 영향을 주지 않음
    }
  }

  void _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;

    final message = _messageController.text.trim();
    _messageController.clear();

    setState(() {
      _messages.add(ChatMessage(
        message: message,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      _isLoading = true;
    });

    try {
      final response = await _chatService.sendMessage(message, _chatId);

      setState(() {
        _messages.add(ChatMessage(
          message: response.text,
          isUser: false,
          timestamp: DateTime.now(),
        ));
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          message: '오류가 발생했습니다: $e',
          isUser: false,
          timestamp: DateTime.now(),
        ));
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        elevation: 0,
        title: const Text('AI 상담'),
      ),
      body: Column(
        children: [
          Expanded(
            child: _buildMessageList(),
          ),
          _buildInputArea(),
        ],
      ),
      bottomNavigationBar: GNB(
        selectedIndex: 1,
        onItemSelected: (index) {
          switch (index) {
            case 0:
              Navigator.pushReplacementNamed(context, '/home');
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
    );
  }

  Widget _buildMessageList() {
    if (_isLoading && _messages.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final message = _messages[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Align(
            alignment:
                message.isUser ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 10,
              ),
              decoration: BoxDecoration(
                color: message.isUser ? Colors.blue[100] : Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 5,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: message.isUser
                    ? CrossAxisAlignment.end
                    : CrossAxisAlignment.start,
                children: [
                  Text(
                    message.message,
                    style: TextStyle(
                      color: message.isUser ? Colors.black87 : Colors.black,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatTime(message.timestamp),
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 5,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: const InputDecoration(
                  hintText: '메시지를 입력하세요',
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                ),
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: (text) => _sendMessage(),
              ),
            ),
            IconButton(
              icon: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
              onPressed: _isLoading ? null : _sendMessage,
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}

class ChatMessage {
  final String message;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.message,
    required this.isUser,
    required this.timestamp,
  });
}
