import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import '../utils/calendar_cache.dart';
import '../pages/login_page.dart';
import '../widgets/emotion_picker.dart';
import 'dart:async';
import '../pages/calendar_page.dart';
import '../pages/retrospect_page.dart';
import 'chat_bot_page.dart';
import '../services/api_service.dart';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  CalendarFormat _calendarFormat = CalendarFormat.month;
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay = DateTime.now();
  Map<DateTime, List<Map<String, dynamic>>> _events = {};
  Map<String, Color> _calendarColors = {};  // 캘린더별 색상 저장
  String _userName = '';
  String _userEmail = '';
  String? _userPhotoUrl;
  String? _userBirthday;
  String? _userGender;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.events',
      'https://www.googleapis.com/auth/calendar.readonly',
      'https://www.googleapis.com/auth/userinfo.profile',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/user.birthday.read',
      'https://www.googleapis.com/auth/user.gender.read',
      'https://www.googleapis.com/auth/plus.login',
      'https://www.googleapis.com/auth/contacts.readonly',
      'https://www.googleapis.com/auth/profile.emails.read',
      'https://www.googleapis.com/auth/profile.photos.read',
    ],
  );

  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    // 화면 전환 후 데이터 로드하도록 수정
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadUserProfile();  // 프로필 정보 로드
      _loadEvents();
    });
  }

  Future<void> _loadUserProfile() async {
    try {
      final account = await _googleSignIn.signInSilently();
      if (account != null) {
        final googleAuth = await account.authentication;
        
        // userinfo API를 사용하여 프로필 정보 가져오기
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
            _userPhotoUrl = userData['picture'];  // 프로필 사진 URL
          });
        }
      }
    } catch (error) {
      print('프로필 로드 에러: $error');
    }
  }

  Future<void> _loadEvents() async {
    try {
      // 1. 먼저 캐시된 데이터 로드
      final cachedEvents = CalendarCache.getEvents();
      final cachedColors = CalendarCache.getColors();
      
      if (mounted) {
        setState(() {
          _events = cachedEvents;
          _calendarColors = cachedColors;
        });
      }

      // 2. 캐시 데이터가 오래되었거나 없는 경우에만 API 호출
      if (CalendarCache.shouldRefresh()) {
        await _loadAllCalendars();
      }
    } catch (e) {
      print('이벤트 로드 에러: $e');
    }
  }

  Future<void> _loadAllCalendars() async {
    final GoogleSignIn googleSignIn = GoogleSignIn(
      scopes: [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly',
      ],
    );

    try {
      final account = await googleSignIn.signInSilently();
      if (account != null) {
        CalendarCache.setUserId(account.id);
        final googleAuth = await account.authentication;
        
        // 1. 먼저 캘린더 목록을 가져옴
        final calendarListResponse = await http.get(
          Uri.parse('https://www.googleapis.com/calendar/v3/users/me/calendarList'),
          headers: {
            'Authorization': 'Bearer ${googleAuth.accessToken}',
            'Accept': 'application/json',
          },
        );

        if (calendarListResponse.statusCode == 200) {
          final calendarList = jsonDecode(calendarListResponse.body);
          final calendars = calendarList['items'] as List;
          print('발견된 캘린더 수: ${calendars.length}');

          // 캘린더 색상 정보 저장
          for (var calendar in calendars) {
            _calendarColors[calendar['id']] = Color(
              int.parse(
                (calendar['backgroundColor'] ?? '#4285F4')
                    .substring(1)
                    .padLeft(8, 'f'),
                radix: 16,
              ),
            );
          }

          // 2. 각 캘린더의 이벤트를 가져옴
          final allEvents = <DateTime, List<Map<String, dynamic>>>{};
          int totalEvents = 0;  // 전체 이벤트 개수를 세기 위한 변수
          
          for (var calendar in calendars) {
            try {
              final calendarId = calendar['id'];
              print('캘린더 로드 시도: ${calendar['summary']} ($calendarId)');
              
              final eventsResponse = await http.get(
                Uri.parse('https://www.googleapis.com/calendar/v3/calendars/${Uri.encodeComponent(calendarId)}/events'
                    '?timeMin=${DateTime.now().subtract(const Duration(days: 30)).toUtc().toIso8601String()}'
                    '&timeMax=${DateTime.now().add(const Duration(days: 60)).toUtc().toIso8601String()}'
                    '&singleEvents=true'
                    '&orderBy=startTime'
                    '&fields=items(id,summary,description,location,start,end,attendees)'),
                headers: {
                  'Authorization': 'Bearer ${googleAuth.accessToken}',
                  'Accept': 'application/json',
                },
              );

              if (eventsResponse.statusCode == 200) {
                final eventsData = jsonDecode(eventsResponse.body);
                print('API 응답: ${eventsData.toString()}');  // 전체 응답 데이터 확인
                final events = eventsData['items'] as List;
                print('캘린더 "${calendar['summary']}"에서 ${events.length}개의 이벤트 로드됨');
                totalEvents += events.length;
                
                for (var event in events) {
                  final startStr = event['start']?['dateTime'] ?? event['start']?['date'];
                  if (startStr != null) {
                    try {
                      DateTime start;
                      if (event['start']?['dateTime'] != null) {
                        // dateTime이 있는 경우 (시간이 있는 일정)
                        start = DateTime.parse(startStr).add(const Duration(hours: 9));  // UTC to KST
                      } else {
                        // date만 있는 경우 (종일 일정)
                        start = DateTime.parse(startStr);  // 이미 로컬 시간
                      }
                      
                      // 날짜 정규화 (한국시간 기준)
                      final day = DateTime(start.year, start.month, start.day);
                      
                      print('이벤트 파싱: ${event['summary']} - $day (원본: $startStr)');
                      
                      allEvents[day] ??= [];
                      event['calendarId'] = calendarId;
                      allEvents[day]!.add(event as Map<String, dynamic>);
                    } catch (e) {
                      print('이벤트 날짜 파싱 에러: ${event['summary']} - $startStr');
                    }
                  }
                }
              } else {
                print('캘린더 로드 실패: ${calendar['summary']} - ${eventsResponse.statusCode}');
                continue;  // 실패한 캘린더는 건너뛰고 계속 진행
              }
            } catch (e) {
              print('캘린더 처리 중 에러: ${calendar['summary']} - $e');
              continue;
            }
          }

          // 날짜별 이벤트 정렬 및 출력
          final sortedDates = allEvents.keys.toList()..sort();
          print('\n=== 날짜별 이벤트 (정렬됨) ===');
          for (var date in sortedDates) {
            print('$date: ${allEvents[date]!.length}개 이벤트');
            for (var event in allEvents[date]!) {
              print('  - ${event['summary']}');
            }
          }

          print('\n=== 이벤트 로드 완료 ===');
          print('총 로드된 이벤트 개수: $totalEvents');
          print('이벤트가 있는 날짜 수: ${allEvents.length}');

          if (mounted) {
            setState(() {
              _events = allEvents;
            });
            // 새로운 데이터 캐시에 저장
            await CalendarCache.cacheEvents(allEvents, _calendarColors);
          }
        }
      }
    } catch (error) {
      print('전체 로드 에러: $error');
    }
  }

  List<dynamic> _getEventsForDay(DateTime day) {
    final normalizedDay = DateTime(day.year, day.month, day.day);
    final events = _events[normalizedDay] ?? [];
    
    // 시간 순서대로 정렬 (한국 시간 기준)
    events.sort((a, b) {
      final aTime = a['start']?['dateTime'] != null
          ? DateTime.parse(a['start']['dateTime']).add(const Duration(hours: 9))
          : DateTime.parse(a['start']['date']);
      final bTime = b['start']?['dateTime'] != null
          ? DateTime.parse(b['start']['dateTime']).add(const Duration(hours: 9))
          : DateTime.parse(b['start']['date']);
      return aTime.compareTo(bTime);
    });
    
    return events;
  }

  Color _getEventColor(Map<String, dynamic> event) {
    return _calendarColors[event['calendarId']] ?? Colors.blue;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('나의 일정'),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Container(),  // 왼쪽 메뉴 버튼 제거
        actions: [
          Builder(  // Builder로 감싸서 올바른 context 제공
            builder: (BuildContext context) => IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => Scaffold.of(context).openEndDrawer(),
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
            child: GestureDetector(  // GestureDetector로 감싸서 드래그 이벤트 처리
              onHorizontalDragStart: (_) {},  // 드래그 이벤트 무시
              onHorizontalDragUpdate: (_) {},  // 드래그 이벤트 무시
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
                                child: const Center(  // Center로 아이콘 위치 조정
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
                          title: const Text(
                            '나의 일정',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,  
                            ),
                          ),
                          selected: true,  
                          selectedTileColor: Colors.transparent, 
                          onTap: () {
                            Navigator.pop(context);  // Drawer 닫기
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.smart_toy_outlined),  
                          title: const Text('챗봇'),
                          onTap: () {
                            Navigator.pop(context);  // Drawer 닫기
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
                          title: const Text('회고 리포트'),
                          onTap: () {
                            Navigator.pop(context);  // Drawer 닫기
                            Navigator.push(
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
                            _loadAllCalendars();
                          },
                        ),

                        ListTile(
                          leading: const Icon(Icons.logout),
                          title: const Text('로그아웃'),
                          onTap: () async {
                            try {
                              final account = await _googleSignIn.signInSilently();
                              if (account != null) {
                                final auth = await account.authentication;
                                if (auth.accessToken != null) {
                                  await _apiService.updateActiveStatus(
                                    auth.accessToken!,
                                    account.email,
                                    false
                                  );
                                }
                              }
                              await _googleSignIn.signOut();
                              if (mounted) {
                                Navigator.pushReplacement(
                                  context,
                                  MaterialPageRoute(builder: (context) => const LoginPage()),
                                );
                              }
                            } catch (e) {
                              print('로그아웃 실패: $e');
                            }
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
      drawerEdgeDragWidth: 0,  // 드래그로 열기 비활성화
      body: Column(
        children: [
          TableCalendar(
            firstDay: DateTime.utc(2020, 1, 1),
            lastDay: DateTime.utc(2030, 12, 31),
            focusedDay: _focusedDay,
            calendarFormat: _calendarFormat,
            eventLoader: _getEventsForDay,
            availableCalendarFormats: const {
              CalendarFormat.month: '월간',
              CalendarFormat.week: '주간',
            },
            selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
            onDaySelected: (selectedDay, focusedDay) {
              setState(() {
                _selectedDay = selectedDay;
                _focusedDay = focusedDay;
              });
            },
            onFormatChanged: (format) {
              setState(() {
                _calendarFormat = format;
              });
            },
            onPageChanged: (focusedDay) {
              _focusedDay = focusedDay;
            },
            calendarStyle: const CalendarStyle(
              markersMaxCount: 3,  // 최대 마커 개수
              markerSize: 4,      // 마커 크기
              markerDecoration: BoxDecoration(
                color: Colors.blue,
                shape: BoxShape.circle,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            alignment: Alignment.centerLeft,
            child: Text(
              '${(_selectedDay ?? DateTime.now()).month}월 ${(_selectedDay ?? DateTime.now()).day}일 일정',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          Expanded(
            child: _getEventsForDay(_selectedDay ?? _focusedDay).isEmpty
                ? const Center(  // 일정이 없을 때
                    child: Text(
                      '조회된 일정이 없습니다',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                  )
                : ListView(  // 일정이 있을 때
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    children: _getEventsForDay(_selectedDay ?? _focusedDay)
                        .map((event) {
                          final startTime = event['start']?['dateTime'] != null
                              ? DateTime.parse(event['start']['dateTime'])
                              : null;
                          final endTime = event['end']?['dateTime'] != null
                              ? DateTime.parse(event['end']['dateTime'])
                              : null;

                          return GestureDetector(
                            onTap: () => _showEventDetails(event),  // 일정 상세 보기
                            onLongPressStart: (LongPressStartDetails details) {
                              showMenu(
                                context: context,
                                position: RelativeRect.fromLTRB(
                                  details.globalPosition.dx,        
                                  details.globalPosition.dy - 50,   
                                  details.globalPosition.dx + 200,  // 팝업 너비
                                  details.globalPosition.dy,
                                ),
                                items: [
                                  PopupMenuItem(
                                    padding: EdgeInsets.zero,
                                    child: EmotionPicker(
                                      selectedScore: event['retrospect']?['score'],
                                      onSelected: (score) {
                                        _updateRetrospect(event, score);
                                        Navigator.pop(context);  // 메뉴 닫기
                                      },
                                    ),
                                  ),
                                ],
                              );
                            },
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 10,
                                    offset: const Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: IntrinsicHeight(
                                child: Row(
                                  children: [
                                    Container(
                                      width: 4,
                                      height: 24,
                                      margin: const EdgeInsets.only(right: 8),
                                      decoration: BoxDecoration(
                                        color: _getEventColor(event),
                                        borderRadius: BorderRadius.circular(2),
                                      ),
                                    ),
                                    Expanded(
                                      child: Padding(
                                        padding: const EdgeInsets.all(12),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              event['summary'] ?? '(제목 없음)',
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.w500,
                                              ),
                                            ),
                                            if (startTime != null) ...[
                                              const SizedBox(height: 8),
                                              Row(
                                                children: [
                                                  Icon(
                                                    Icons.access_time,
                                                    size: 14,
                                                    color: Colors.grey[600],
                                                  ),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    endTime != null
                                                        ? '${_formatTime(startTime)} - ${_formatTime(endTime)}'
                                                        : _formatTime(startTime),
                                                    style: TextStyle(
                                                      color: Colors.grey[600],
                                                      fontSize: 14,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ],
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        })
                        .toList(),
                  ),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    // UTC를 한국 시간으로 변환 (UTC+9)
    final koreaTime = time.add(const Duration(hours: 9));
    return '${koreaTime.hour.toString().padLeft(2, '0')}:${koreaTime.minute.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _updateRetrospect(Map<String, dynamic> event, int score) async {
    setState(() {
      if (event['retrospect']?['score'] == score) {
        // 같은 감정을 다시 클릭하면 버튼 누른거 취소되게 
        event.remove('retrospect');
      } else {
        // 다른 감정 선택 또는 새로운 회고
        event['retrospect'] = {
          'score': score,
          'timestamp': DateTime.now().toIso8601String(),
        };
      }
    });
    
    // 캐시 업데이트
    await CalendarCache.cacheEvents(_events, _calendarColors);
  }

  bool _isToday(Map<String, dynamic> event) {
    final eventDate = DateTime.parse(event['start']['dateTime'] ?? event['start']['date']);
    final now = DateTime.now();
    return eventDate.year == now.year && 
           eventDate.month == now.month && 
           eventDate.day == now.day;
  }

  bool _isRetrospectAvailable(Map<String, dynamic> event) {
    // 현재 시간을 한국 시간으로 가져오기
    final now = DateTime.now().add(const Duration(hours: 9));  // UTC+9
    
    final eventDate = DateTime.parse(event['start']['dateTime'] ?? event['start']['date']);
    final eventDateTime = DateTime(
      eventDate.year, 
      eventDate.month, 
      eventDate.day,
      event['start']['dateTime'] != null
          ? DateTime.parse(event['start']['dateTime']).add(const Duration(hours: 9)).hour
          : 0,
      event['start']['dateTime'] != null
          ? DateTime.parse(event['start']['dateTime']).add(const Duration(hours: 9)).minute
          : 0,
    );

    // 디버깅을 위한 로그
    print('===== 일정 회고 가능 여부 체크 =====');
    print('일정 제목: ${event['summary']}');
    print('일정 시간: $eventDateTime');
    print('현재 시간: $now');

    // 종일 일정인 경우 해당 날짜만 비교
    if (event['start']['date'] != null) {
      return DateTime(eventDateTime.year, eventDateTime.month, eventDateTime.day)
          .isBefore(DateTime(now.year, now.month, now.day + 1));
    }

    // 시간이 있는 일정의 경우 정확한 시간까지 비교
    return eventDateTime.isBefore(now);
  }

  // 일정 상세 보기 다이얼로그 함수
  void _showEventDetails(Map<String, dynamic> event) {
    // 컨텐츠 유무에 따른 높이 계산
    double calculateHeight() {
      double height = 0.2;  // 기본 높이 (제목과 시간 정보)
      
      if (event['location'] != null) {
        height += 0.05;  // 장소 정보가 있으면 높이 추가
      }
      
      if (event['attendees'] != null) {
        height += 0.08;  // 참석자 정보가 있으면 높이 추가
      }
      
      if (event['description'] != null) {
        height += 0.07;  // 설명이 있으면 높이 추가
      }
      
      if (_isRetrospectAvailable(event)) {
        height += 0.08;  // 회고 영역이 있으면 높이 추가
      }
      
      return height;  // 전체 화면 대비 비율
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        final startTime = event['start']?['dateTime'] != null
            ? DateTime.parse(event['start']['dateTime'])
            : null;
        final endTime = event['end']?['dateTime'] != null
            ? DateTime.parse(event['end']['dateTime'])
            : null;

        return GestureDetector(
          onTap: () => Navigator.pop(context),
          child: Container(
            padding: const EdgeInsets.all(20),
            height: MediaQuery.of(context).size.height * calculateHeight(),
            child: GestureDetector(
              onTap: () {},
              child: Column(
                mainAxisSize: MainAxisSize.max,  // 최대 높이 사용
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 제목 영역
                  Row(
                    children: [
                      Container(
                        width: 4,
                        height: 24,
                        margin: const EdgeInsets.only(right: 8),
                        decoration: BoxDecoration(
                          color: _getEventColor(event),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      Expanded(
                        child: Text(
                          event['summary'] ?? '(제목 없음)',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.edit),
                        onPressed: () {
                          // TODO: 일정 수정 기능 구현
                          Navigator.pop(context);
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  
                  // 시간 정보
                  if (startTime != null) ...[
                    Row(
                      children: [
                        const Icon(Icons.access_time, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          endTime != null
                              ? '${_formatTime(startTime)} - ${_formatTime(endTime)}'
                              : _formatTime(startTime),
                          style: const TextStyle(fontSize: 16),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],
                  
                  // 장소 정보
                  if (event['location'] != null) ...[
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            event['location'],
                            style: const TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],
                  
                  // 참석자 정보
                  if (event['attendees'] != null) ...[
                    Row(
                      children: [
                        const Icon(Icons.people, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Wrap(
                            spacing: 8,
                            children: (event['attendees'] as List).map((attendee) {
                              return Chip(
                                label: Text(attendee['email'] ?? ''),
                                avatar: attendee['responseStatus'] == 'accepted'
                                    ? const Icon(Icons.check_circle, size: 16, color: Colors.green)
                                    : attendee['responseStatus'] == 'declined'
                                        ? const Icon(Icons.cancel, size: 16, color: Colors.red)
                                        : const Icon(Icons.help, size: 16, color: Colors.orange),
                              );
                            }).toList(),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],
                  
                  // 설명
                  if (event['description'] != null) ...[
                    const Text(
                      '설명',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      event['description'],
                      style: const TextStyle(fontSize: 16),
                    ),
                    const SizedBox(height: 20),
                  ],
                  
                  // 회고 영역
                  if (_isRetrospectAvailable(event)) ...[
                    const Text(
                      '회고',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    EmotionPicker(
                      selectedScore: event['retrospect']?['score'],
                      onSelected: (score) {
                        _updateRetrospect(event, score);
                        Navigator.pop(context);
                      },
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }
} 