import 'package:hive/hive.dart';
import '../../../calendar/domain/entities/calendar_event.dart' as entities;

part 'weekly_report.g.dart';

@HiveType(typeId: 3) // typeId는 프로젝트 내에서 유니크해야 합니다
class WeeklyReport {
  @HiveField(0)
  final DateTime startDate;

  @HiveField(1)
  final DateTime endDate;

  @HiveField(2)
  final List<String> emotions; // 감정 데이터만 저장

  @HiveField(3)
  final List<String> emojis;

  @HiveField(4)
  final String summary;

  @HiveField(5)
  final DateTime lastUpdated; // 마지막 업데이트 시간

  @HiveField(6)
  final List<String> eventIds; // 포함된 이벤트 ID 목록

  WeeklyReport({
    required this.startDate,
    required this.endDate,
    required this.emotions,
    required this.emojis,
    required this.summary,
    required this.lastUpdated,
    required this.eventIds,
  });

  // 이벤트 변경 시 리포트 업데이트
  WeeklyReport copyWithUpdatedEvents({
    required List<entities.CalendarEvent> currentEvents,
    required List<String> currentEmotions,
    required List<String> currentEmojis,
  }) {
    return WeeklyReport(
      startDate: startDate,
      endDate: endDate,
      emotions: currentEmotions,
      emojis: currentEmojis,
      summary: _generateUpdatedSummary(currentEmotions),
      lastUpdated: DateTime.now(),
      eventIds: currentEvents.map((e) => e.id).toList(),
    );
  }

  String _generateUpdatedSummary(List<String> currentEmotions) {
    if (currentEmotions.isEmpty) return '이번 주 감정 기록이 없습니다.';

    final emotionCount = <String, int>{};
    for (var emotion in currentEmotions) {
      emotionCount[emotion] = (emotionCount[emotion] ?? 0) + 1;
    }

    final mostFrequent =
        emotionCount.entries.reduce((a, b) => a.value > b.value ? a : b).key;

    return '이번 주는 "$mostFrequent" 감정이 가장 많았어요.';
  }
}
