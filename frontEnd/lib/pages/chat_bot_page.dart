import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'calendar_page.dart';
import 'retrospect_page.dart';
import '../utils/calendar_cache.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'login_page.dart';

class ChatBotPage extends StatefulWidget {
  const ChatBotPage({super.key});

  @override
  State<ChatBotPage> createState() => _ChatBotPageState();
}

class _ChatBotPageState extends State<ChatBotPage> {
  String _userName = '';
  String _userEmail = '';
  String? _userPhotoUrl;
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<Map<String, dynamic>> _messages = [];
  DateTime? _lastMessageDate;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'https://www.googleapis.com/auth/calendar.readonly',
      'https://www.googleapis.com/auth/userinfo.profile',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/calendar',
    ],
  );

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      final account = await _googleSignIn.signInSilently();
      if (account != null) {
        setState(() {
          _userName = account.displayName ?? '';
          _userEmail = account.email;
          _userPhotoUrl = account.photoUrl;
        });
      } else {
        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => const LoginPage(),
            ),
          );
        }
      }
    } catch (error) {
      print('프로필 로드 에러: $error');
      setState(() {
        _userName = '';
        _userEmail = '';
        _userPhotoUrl = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('챗봇'),
        backgroundColor: Colors.white,
        elevation: 0,
        actions: [
          Builder(
            builder: (context) => IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () {
                Scaffold.of(context).openEndDrawer();
              },
            ),
          ),
        ],
      ),
      endDrawer: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(1, 0),
          end: Offset.zero,
        ).animate(CurvedAnimation(
          parent: ModalRoute.of(context)!.animation!,
          curve: Curves.easeInOut,
        )),
        child: SizedBox(
          width: 304,
          child: Drawer(
            child: GestureDetector(
              onHorizontalDragStart: (_) {},
              onHorizontalDragUpdate: (_) {},
              child: Column(
                children: [
                  Container(
                    height: 180,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topRight,
                        end: Alignment.bottomLeft,
                        colors: [
                          Colors.blue.withOpacity(0.9),
                          Colors.blue[600]!.withOpacity(0.8),
                        ],
                      ),
                      border: Border(
                        bottom: BorderSide(
                          color: Colors.grey[300]!,
                          width: 1,
                        ),
                      ),
                    ),
                    child: Stack(
                      children: [
                        Positioned(
                          top: 30,
                          left: 10,
                          child: Material(
                            color: Colors.transparent,
                            child: InkWell(
                              onTap: () {
                                print('X button pressed');
                                Navigator.pop(context);
                              },
                              child: Container(
                                width: 60,
                                height: 50,
                                color: Colors.transparent,
                                child: const Center(
                                  child: Icon(
                                    Icons.close,
                                    color: Colors.white,
                                    size: 24,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                        Positioned(
                          bottom: 20,
                          left: 16,
                          right: 16,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              if (_userPhotoUrl != null)
                                CircleAvatar(
                                  radius: 25,
                                  backgroundImage: NetworkImage(_userPhotoUrl!),
                                )
                              else
                                const CircleAvatar(
                                  radius: 25,
                                  backgroundColor: Colors.white,
                                  child: Icon(Icons.person, size: 30, color: Colors.lightBlue),
                                ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      _userName,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 20,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    Text(
                                      _userEmail,
                                      style: const TextStyle(
                                        color: Colors.white70,
                                        fontSize: 14,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: ListView(
                      padding: EdgeInsets.zero,
                      children: [
                        ListTile(
                          leading: const Icon(Icons.calendar_month),
                          title: const Text('나의 일정'),
                          onTap: () {
                            Navigator.pop(context);
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const CalendarPage(),
                              ),
                            );
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.smart_toy_outlined),
                          title: const Text(
                            '챗봇',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          selected: true,
                          selectedTileColor: Colors.transparent,
                          onTap: () {
                            Navigator.pop(context);
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.analytics_outlined),
                          title: const Text('회고 리포트'),
                          onTap: () {
                            Navigator.pop(context);
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const RetrospectPage(),
                              ),
                            );
                          },
                        ),
                        ListTile(
                          leading: Icon(Icons.cleaning_services),
                          title: Text('캐시 삭제'),
                          onTap: () async {
                            await CalendarCache.clear();
                            Navigator.pop(context);
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      drawerEdgeDragWidth: 0,
      body: Column(
        children: [
          Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topRight,
                end: Alignment.bottomLeft,
                colors: [
                  Colors.blue[400]!,
                  Colors.blue[600]!,
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: const Icon(
                    Icons.smart_toy,
                    size: 30,
                    color: Colors.blue,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _userName.isNotEmpty ? '$_userName님 안녕하세요!' : '안녕하세요!',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        '일정과 회고에 대해 물어보세요',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageBubble(message, index);
              },
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            padding: EdgeInsets.only(
              top: 8,
              bottom: MediaQuery.of(context).viewInsets.bottom,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.mic),
                        onPressed: () {
                          // TODO: 음성 입력 구현
                        },
                        color: Colors.blue,
                      ),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(24),
                          ),
                          child: TextField(
                            controller: _messageController,
                            decoration: const InputDecoration(
                              hintText: '메시지를 입력하세요',
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.symmetric(vertical: 12),
                            ),
                            maxLines: null,
                            textInputAction: TextInputAction.send,
                            onSubmitted: (_) => _sendMessage(),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send),
                        onPressed: _sendMessage,
                        color: Colors.blue,
                      ),
                    ],
                  ),
                ),
                SizedBox(
                  height: MediaQuery.of(context).padding.bottom,
                  width: double.infinity,
                  child: Container(
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> message, int index) {
    final isUser = message['isUser'] as bool;
    final messageTime = DateTime.parse(message['timestamp']);
    final showDate = _shouldShowDate(messageTime, index);

    bool hideIcon = false;
    if (!isUser && index > 0) {
      final prevMessage = _messages[index - 1];
      final prevTime = DateTime.parse(prevMessage['timestamp']);
      final isPrevSameSender = !prevMessage['isUser'];

      if (isPrevSameSender &&
          prevTime.year == messageTime.year &&
          prevTime.month == messageTime.month &&
          prevTime.day == messageTime.day &&
          prevTime.hour == messageTime.hour &&
          prevTime.minute == messageTime.minute) {
        hideIcon = true;
      }
    }

    bool hideTimeVisually = false;
    if (index < _messages.length - 1) {
      final nextMessage = _messages[index + 1];
      final nextTime = DateTime.parse(nextMessage['timestamp']);
      final isNextSameSender = (nextMessage['isUser'] == isUser);

      if (isNextSameSender &&
          nextTime.year == messageTime.year &&
          nextTime.month == messageTime.month &&
          nextTime.day == messageTime.day &&
          nextTime.hour == messageTime.hour &&
          nextTime.minute == messageTime.minute) {
        hideTimeVisually = true;
      }
    }

    return Column(
      children: [
        if (showDate) ...[
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text(
              _formatDate(messageTime),
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 12,
              ),
            ),
          ),
        ],
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!isUser) ...[
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: hideIcon ? Colors.transparent : Colors.blue[100],
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(
                    Icons.smart_toy,
                    size: 16,
                    color: hideIcon ? Colors.transparent : Colors.blue,
                  ),
                ),
                const SizedBox(width: 8),
              ],
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.65,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    if (isUser) ...[
                      Text(
                        _formatTime(messageTime),
                        style: TextStyle(
                          color: hideTimeVisually ? Colors.transparent : Colors.grey[500],
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 4),
                    ],
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        decoration: BoxDecoration(
                          color: isUser ? Colors.blue : Colors.grey[100],
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          message['text'] as String,
                          style: TextStyle(
                            color: isUser ? Colors.white : Colors.black87,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ),
                    if (!isUser) ...[
                      const SizedBox(width: 4),
                      Text(
                        _formatTime(messageTime),
                        style: TextStyle(
                          color: hideTimeVisually ? Colors.transparent : Colors.grey[500],
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  bool _shouldShowDate(DateTime messageTime, int index) {
    if (index == 0) return true;

    if (index > 0) {
      final previousMessage = _messages[index - 1];
      final previousTime = DateTime.parse(previousMessage['timestamp']);

      return !_isSameDay(previousTime, messageTime);
    }

    return false;
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _formatDate(DateTime date) {
    return '${date.year}년 ${date.month}월 ${date.day}일';
  }

  String _formatTime(DateTime time) {
    final hour = time.hour;
    final minute = time.minute.toString().padLeft(2, '0');
    final period = hour < 12 ? '오전' : '오후';
    final hour12 = hour <= 12 ? hour : hour - 12;
    return '$period ${hour12}:$minute';
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    final now = DateTime.now().add(const Duration(hours: 9));

    setState(() {
      _messages.add({
        'text': text,
        'isUser': true,
        'timestamp': now.toIso8601String(),
      });
    });

    _messageController.clear();
    _scrollToBottom();

    try {
      final url = '${dotenv.env['BACKEND_URL']}/chat';
      final account = await _googleSignIn.signInSilently();
      if (account == null) throw Exception('로그인이 필요합니다.');

      final response = await http.post(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode({
          'message': text,
          'user_id': account.email,
        }),
      );

      if (response.statusCode == 200) {
        final botResponse = utf8.decode(response.bodyBytes);
        setState(() {
          _messages.add({
            'text': botResponse,
            'isUser': false,
            'timestamp': DateTime.now().add(const Duration(hours: 9)).toIso8601String(),
          });
        });
      } else {
        throw Exception('서버 오류: ${response.statusCode}');
      }
    } catch (e) {
      setState(() {
        _messages.add({
          'text': '죄송합니다. 오류가 발생했습니다: $e',
          'isUser': false,
          'timestamp': DateTime.now().add(const Duration(hours: 9)).toIso8601String(),
        });
      });
    }

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }
}