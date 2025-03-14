import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'calendar_page.dart';
import '../utils/calendar_cache.dart';
import 'chat_bot_page.dart';

class RetrospectPage extends StatefulWidget {
  const RetrospectPage({super.key});

  @override
  State<RetrospectPage> createState() => _RetrospectPageState();
}

class _RetrospectPageState extends State<RetrospectPage> {
  String _userName = '';
  String _userEmail = '';
  String? _userPhotoUrl;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'https://www.googleapis.com/auth/userinfo.profile',
      'https://www.googleapis.com/auth/userinfo.email',
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
        final googleAuth = await account.authentication;
        
        final response = await http.get(
          Uri.parse('https://www.googleapis.com/oauth2/v2/userinfo'),
          headers: {
            'Authorization': 'Bearer ${googleAuth.accessToken}',
            'Accept': 'application/json',
          },
        );

        if (response.statusCode == 200) {
          final userData = jsonDecode(response.body);
          setState(() {
            _userName = userData['name'] ?? '';
            _userEmail = userData['email'] ?? '';
            _userPhotoUrl = userData['picture'];
          });
        }
      }
    } catch (error) {
      print('프로필 로드 에러: $error');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('회고 리포트'),
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
                        Positioned(  // 사용자 프로필 정보 추가
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
                            Navigator.pop(context);  // Drawer 닫기
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
                          title: const Text('챗봇'),
                          onTap: () {
                            Navigator.pop(context);
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const ChatBotPage(),
                              ),
                            );
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.analytics_outlined),
                          title: const Text(
                            '회고 리포트',
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
      body: const Center(
        child: Text('회고 페이지 내용이 들어갈 자리입니다.'),
      ),
    );
  }
} 