import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:hive/hive.dart';
import '../../domain/models/weekly_report.dart';
import '../../../calendar/domain/entities/calendar_event.dart';
import '../../../calendar/domain/repositories/calendar_repository.dart';

class ReportRepository {
  final FirebaseFirestore _firestore;
  final Box<WeeklyReport> _reportsBox;
  final String _userId;
  final CalendarRepository _calendarRepository;

  ReportRepository({
    FirebaseFirestore? firestore,
    required Box<WeeklyReport> reportsBox,
    required CalendarRepository calendarRepository,
  })  : _firestore = firestore ?? FirebaseFirestore.instance,
        _reportsBox = reportsBox,
        _userId = FirebaseAuth.instance.currentUser?.uid ?? '',
        _calendarRepository = calendarRepository;

  // 리포트 저장 (Hive + Firestore)
  Future<void> saveWeeklyReport(WeeklyReport report) async {
    final cacheKey = _getCacheKey(report.startDate);

    final reportToSave = WeeklyReport(
      startDate: report.startDate,
      endDate: report.endDate,
      emotions: report.emotions,
      emojis: report.emojis,
      summary: report.summary,
      lastUpdated: DateTime.now(),
      eventIds: report.eventIds,
    );

    // Hive에 저장
    await _reportsBox.put(cacheKey, reportToSave);

    // Firestore에 저장
    await _firestore
        .collection('users')
        .doc(_userId)
        .collection('weekly_reports')
        .doc(cacheKey)
        .set({
      'startDate': reportToSave.startDate,
      'endDate': reportToSave.endDate,
      'emotions': reportToSave.emotions,
      'emojis': reportToSave.emojis,
      'summary': reportToSave.summary,
      'lastUpdated': reportToSave.lastUpdated,
      'eventIds': reportToSave.eventIds,
    });
  }

  // 리포트 조회 (캐시 우선, 없으면 Firestore)
  Future<List<WeeklyReport>> getWeeklyReports() async {
    try {
      // 실제 저장된 리포트 가져오기
      final reports = _reportsBox.values.toList();

      // 더미 데이터가 없을 경우에만 추가
      if (reports.isEmpty) {
        final dummyReports = _generateDummyReports();
        // 더미 데이터 저장
        for (var report in dummyReports) {
          await _reportsBox.put(report.startDate.toString(), report);
        }
        return dummyReports..sort((a, b) => b.startDate.compareTo(a.startDate));
      }

      return reports..sort((a, b) => b.startDate.compareTo(a.startDate));
    } catch (e) {
      print('Error getting weekly reports: $e');
      // 에러 발생 시 더미 데이터라도 보여주기
      return _generateDummyReports()
        ..sort((a, b) => b.startDate.compareTo(a.startDate));
    }
  }

  List<WeeklyReport> _generateDummyReports() {
    final now = DateTime.now();
    return [
      WeeklyReport(
        startDate: DateTime(2024, 1, 12),
        endDate: DateTime(2024, 1, 18),
        emotions: ['매우 긍정적', '긍정적', '보통'],
        emojis: ['😊', '🙂', '😐'],
        summary: '달리기로 생산성을 높였어요',
        lastUpdated: now,
        eventIds: ['1', '2', '3'],
      ),
      WeeklyReport(
        startDate: DateTime(2024, 1, 5),
        endDate: DateTime(2024, 1, 11),
        emotions: ['긍정적', '보통', '부정적'],
        emojis: ['🙂', '😐', '😟'],
        summary: '페캠 프로젝트로 일상의 여유가 없었어요',
        lastUpdated: now,
        eventIds: ['4', '5', '6'],
      ),
      WeeklyReport(
        startDate: DateTime(2023, 12, 30),
        endDate: DateTime(2024, 1, 5),
        emotions: ['매우 긍정적', '긍정적', '긍정적'],
        emojis: ['😊', '🙂', '🙂'],
        summary: '새해 목표 5개를 설정하고 첫 주 모두 시작했어요',
        lastUpdated: now,
        eventIds: ['7', '8', '9'],
      ),
    ];
  }

  // 캐시 키 생성
  String _getCacheKey(DateTime date) {
    return '${date.year}-${date.month}-${date.day}';
  }

  // 캐시 삭제
  Future<void> clearCache() async {
    await _reportsBox.clear();
  }

  // 이벤트 변경 감지 및 리포트 업데이트
  Future<void> handleEventChanges(
    DateTime weekStart,
    List<CalendarEvent> currentEvents,
  ) async {
    final cacheKey = _getCacheKey(weekStart);
    final existingReport = _reportsBox.get(cacheKey);

    if (existingReport != null) {
      // 현재 이벤트들의 감정과 이모지 추출
      final currentEmotions = currentEvents
          .map((e) => e.emotion)
          .where((e) => e != null)
          .cast<String>()
          .toList();

      final currentEmojis = currentEvents
          .map((e) => e.emoji)
          .where((e) => e != null)
          .cast<String>()
          .toList();

      // 리포트 업데이트
      final updatedReport = existingReport.copyWithUpdatedEvents(
        currentEvents: currentEvents,
        currentEmotions: currentEmotions,
        currentEmojis: currentEmojis,
      );

      // 저장
      await saveWeeklyReport(updatedReport);
    }
  }

  // 주간 데이터 새로고침
  Future<void> refreshWeeklyData(DateTime date) async {
    final weekStart = _getWeekStart(date);
    final weekEnd = weekStart.add(const Duration(days: 6));

    // 해당 주의 현재 이벤트 가져오기
    final result = await _calendarRepository.getEventsForRange(
      weekStart,
      weekEnd,
    );

    result.fold(
      (failure) => print('Failed to get events: $failure'),
      (events) async => await handleEventChanges(weekStart, events),
    );
  }

  DateTime _getWeekStart(DateTime date) {
    final diff = date.weekday - DateTime.monday;
    return DateTime(date.year, date.month, date.day - diff);
  }
}
