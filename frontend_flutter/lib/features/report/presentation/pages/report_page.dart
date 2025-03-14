import 'package:flutter/material.dart';
import '../../../chat/data/datasources/openai_service.dart';
import 'package:intl/intl.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:async';
import '../../../chat/presentation/pages/reflection_chat_page.dart';
import '../../../calendar/presentation/bloc/calendar_bloc.dart';
import '../../../calendar/domain/entities/calendar_event.dart' as entities;
import '../../../../injection.dart';
import 'package:hive/hive.dart';
import '../../../report/data/repositories/report_repository.dart';
import '../../../calendar/domain/repositories/calendar_repository.dart';
import '../../domain/models/weekly_report.dart';
import '../../../report/presentation/pages/report_detail_page.dart';

class ReportPage extends StatefulWidget {
  const ReportPage({super.key});

  @override
  State<ReportPage> createState() => _ReportPageState();
}

class _ReportPageState extends State<ReportPage>
    with SingleTickerProviderStateMixin {
  static const String _cacheBoxName = 'weekly_reports';
  late Box<WeeklyReport> _reportsBox;
  late TabController _tabController;
  final OpenAIService _openAIService = OpenAIService();
  Timer? _timer;
  String _remainingTime = '';
  final CalendarBloc _calendarBloc = getIt<CalendarBloc>();
  late final ReportRepository _reportRepository;
  List<WeeklyReport>? _cachedReports;
  bool _isInitialized = false; // 초기화 상태 추적

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _initializeData();
  }

  Future<void> _initializeData() async {
    try {
      await _initRepositories();
      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
        _updateRemainingTime();
        _timer = Timer.periodic(const Duration(seconds: 1), (_) {
          if (mounted) {
            _updateRemainingTime();
          }
        });
        await _loadReports();
      }
    } catch (e) {
      print('Error initializing data: $e');
    }
  }

  Future<void> _initRepositories() async {
    _reportsBox = await Hive.openBox<WeeklyReport>(_cacheBoxName);
    _reportRepository = ReportRepository(
      reportsBox: _reportsBox,
      calendarRepository: getIt<CalendarRepository>(),
    );
  }

  Future<void> _updateWeeklyReports() async {
    final now = DateTime.now();
    final startDate = DateTime(2025, 1, 1);
    final events = _calendarBloc.state.events;

    DateTime weekStart = startDate;
    while (weekStart.isBefore(now)) {
      final weekEnd = weekStart.add(const Duration(days: 6));
      final weekEvents = events.entries
          .where((entry) =>
              entry.key.isAfter(weekStart.subtract(const Duration(days: 1))) &&
              entry.key.isBefore(weekEnd.add(const Duration(days: 1))))
          .expand((entry) => entry.value)
          .toList();

      if (weekEvents.isNotEmpty) {
        final emotions = weekEvents
            .map((e) => e.emotion)
            .where((e) => e != null)
            .cast<String>()
            .toList();

        final emojis = weekEvents
            .map((e) => e.emoji)
            .where((e) => e != null)
            .cast<String>()
            .toList();

        final summary = _generateWeeklySummary(weekEvents);

        final report = WeeklyReport(
          startDate: weekStart,
          endDate: weekEnd,
          emotions: emotions,
          summary: summary,
          emojis: emojis,
          lastUpdated: DateTime.now(),
          eventIds: weekEvents.map((e) => e.id).toList(),
        );

        // Hive와 Firestore에 동시에 저장
        await _reportRepository.saveWeeklyReport(report);
      }

      weekStart = weekStart.add(const Duration(days: 7));
    }
  }

  String _getUserName() {
    final user = FirebaseAuth.instance.currentUser;
    return user?.displayName?.split(' ').first ?? '준석';
  }

  bool _isReflectionAvailable() {
    final now = DateTime.now();
    final dayOfWeek = now.weekday; // 1 = 월요일
    final hour = now.hour;

    // 월요일 9시 이후부터 가능
    return dayOfWeek == 1 && hour >= 9;
  }

  String _getTimeUntilAvailable() {
    final now = DateTime.now();
    final nextMonday = now
        .add(
          Duration(days: (8 - now.weekday) % 7),
        )
        .copyWith(hour: 9, minute: 0);

    final remainingTime = nextMonday.difference(now);
    final days = remainingTime.inDays;
    final hours = remainingTime.inHours % 24;

    return '리포트 받기까지\n$days일 $hours시간 남음';
  }

  Future<List<WeeklyReport>> _getWeeklyReports() async {
    return _reportRepository.getWeeklyReports();
  }

  void _updateRemainingTime() {
    final now = DateTime.now();
    final nextMonday = _getNextMonday(now);
    final remainingTime = nextMonday.difference(now);

    final days = remainingTime.inDays;
    final hours = (remainingTime.inHours % 24);
    final minutes = (remainingTime.inMinutes % 60);
    final seconds = (remainingTime.inSeconds % 60);

    setState(() {
      _remainingTime = '리포트 받기까지\n$days일 $hours시간 $minutes분 $seconds초 남음';
    });
  }

  DateTime _getNextMonday(DateTime now) {
    // 다음 월요일 9시를 계산
    final daysUntilMonday = (DateTime.monday - now.weekday + 7) % 7;
    var nextMonday = DateTime(
      now.year,
      now.month,
      now.day + daysUntilMonday,
      9, // 오전 9시
      0, // 0분
      0, // 0초
    );

    // 현재가 월요일이고 9시 이전이면 오늘을 반환
    if (now.weekday == DateTime.monday && now.hour < 9) {
      return DateTime(now.year, now.month, now.day, 9, 0, 0);
    }

    // 현재가 월요일이고 9시 이후면 다음 주 월요일을 반환
    if (now.weekday == DateTime.monday && now.hour >= 9) {
      nextMonday = nextMonday.add(const Duration(days: 7));
    }

    return nextMonday;
  }

  Future<void> _loadReports() async {
    try {
      if (!mounted) return;
      final reports = await _reportRepository.getWeeklyReports();
      setState(() {
        _cachedReports = reports;
      });
    } catch (e) {
      print('Error loading reports: $e');
      if (mounted) {
        setState(() {
          _cachedReports = [];
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    final userName = _getUserName();
    return WillPopScope(
      onWillPop: () async {
        Navigator.pushReplacementNamed(context, '/home');
        return false;
      },
      child: Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          title: const Text('리포트'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pushReplacementNamed(context, '/home'),
          ),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(50),
            child: TabBar(
              controller: _tabController,
              tabs: const [
                Tab(
                  child: Text(
                    '새 리포트',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                Tab(
                  child: Text(
                    '지난 리포트',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
              labelColor: Colors.blue,
              unselectedLabelColor: Colors.grey,
              indicatorColor: Colors.blue,
              indicatorWeight: 3,
            ),
          ),
        ),
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildNewReportTab(),
            _buildPastReportsTab(),
          ],
        ),
      ),
    );
  }

  Widget _buildNewReportTab() {
    final userName = _getUserName();
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24.0),
      child: Column(
        children: [
          const SizedBox(height: 80),
          Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  shape: BoxShape.circle,
                ),
              ),
              const Image(
                image: AssetImage('assets/images/img_timer.png'),
                width: 50,
                height: 50,
              ),
            ],
          ),
          const SizedBox(height: 40),
          Text(
            '이번 주 $userName님의 일정+회고를 통해\n리포트가 생성됐어요!',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(
              vertical: 16,
              horizontal: 16,
            ),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              _remainingTime,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.blue.shade700,
                fontWeight: FontWeight.w600,
                height: 1.4,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            '일정과 감정을 기록할수록 $userName님만의\n맞춤형 인사이트를 얻을 수 있어요.\n지금 회고를 해보세요!',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 14,
              color: Colors.grey,
              height: 1.6,
            ),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.only(bottom: 40.0), // 버튼 위치 위로 조정
            child: SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ReflectionChatPage(
                        eventTitle: "오늘의 회고",
                        emotion: "행복",
                        eventDate: DateTime.now(),
                        eventId:
                            "report_reflection_${DateTime.now().millisecondsSinceEpoch}",
                      ),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  elevation: 0,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  '회고하러 가기',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildPastReportsTab() {
    if (_cachedReports == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_cachedReports!.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history, size: 48, color: Colors.grey[300]),
            const SizedBox(height: 16),
            const Text(
              '아직 생성된 리포트가 없습니다',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _cachedReports!.length,
      itemBuilder: (context, index) {
        final report = _cachedReports![index];
        final startDate = report.startDate;
        final endDate = report.endDate;

        final dateRange = '${_formatDate(startDate)} - ${_formatDate(endDate)}';

        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 2,
          child: InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ReportDetailPage(report: report),
                ),
              );
            },
            borderRadius: BorderRadius.circular(16),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '${startDate.month}월 ${_getWeekOfMonth(startDate)}주',
                          style: TextStyle(
                            color: Colors.blue.shade700,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        dateRange,
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    report.summary,
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.5,
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

  String _formatDate(DateTime date) {
    return DateFormat('M/d (E)', 'ko_KR').format(date);
  }

  int _getWeekOfMonth(DateTime date) {
    final firstDayOfMonth = DateTime(date.year, date.month, 1);
    final firstWeekday = firstDayOfMonth.weekday;
    final offsetDate = date.day + firstWeekday - 1;
    return ((offsetDate - 1) ~/ 7) + 1;
  }

  String _generateWeeklySummary(List<entities.CalendarEvent> events) {
    if (events.isEmpty) return '이번 주 기록된 일정이 없습니다.';

    final emotions = events
        .map((e) => e.emotion)
        .where((e) => e != null)
        .cast<String>()
        .toList();

    if (emotions.isEmpty) return '이번 주 감정 기록이 없습니다.';

    final emotionCount = <String, int>{};
    for (var emotion in emotions) {
      emotionCount[emotion] = (emotionCount[emotion] ?? 0) + 1;
    }

    final mostFrequent =
        emotionCount.entries.reduce((a, b) => a.value > b.value ? a : b).key;

    return '이번 주는 "$mostFrequent" 감정이 가장 많았어요.';
  }

  @override
  void dispose() {
    _timer?.cancel();
    _tabController.dispose();
    // Hive box가 초기화된 경우에만 close 호출
    if (_isInitialized) {
      _reportsBox.close();
    }
    super.dispose();
  }
}
