import 'package:hive/hive.dart';
import '../models/calendar_event_model.dart';
import '../../domain/entities/emotion.dart';
import '../../domain/entities/emotion_adapter.dart';
import 'dart:async';
import 'package:shared_preferences/shared_preferences.dart';

class CalendarCacheManager {
  static const String eventsBoxName = 'calendar_events';
  static const String emotionsBoxName = 'event_emotions';
  late Box<CalendarEventModel> _eventsBox;
  late Box<int> _emotionsBox;
  Timer? _cleanupTimer;
  Duration validityDuration = const Duration(days: 1);

  CalendarCacheManager() {
    // 주기적으로 오래된 캐시 정리
    _cleanupTimer =
        Timer.periodic(const Duration(days: 1), (_) => _cleanOldCache());
  }

  Future<void> init() async {
    if (!Hive.isAdapterRegistered(0)) {
      Hive.registerAdapter(CalendarEventModelAdapter());
    }
    if (!Hive.isAdapterRegistered(1)) {
      Hive.registerAdapter(EmotionAdapter());
    }

    _eventsBox = await Hive.openBox<CalendarEventModel>(eventsBoxName);
    _emotionsBox = await Hive.openBox<int>(emotionsBoxName);
  }

  Future<void> cacheEvents(List<CalendarEventModel> events) async {
    try {
      final Map<String, CalendarEventModel> eventMap = {
        for (var event in events) event.id: event
      };
      await _eventsBox.putAll(eventMap);
      print('Cached ${events.length} events');
    } catch (e) {
      print('Error caching events: $e');
      rethrow;
    }
  }

  Future<void> cacheEventEmotion(String eventId, Emotion emotion) async {
    try {
      // 1. 이벤트 가져오기
      final event = _eventsBox.get(eventId);
      if (event != null) {
        // 2. 새로운 이벤트 모델 생성
        final updatedEvent = CalendarEventModel(
          id: event.id,
          title: event.title,
          startTime: event.startTime,
          endTime: event.endTime,
          description: event.description,
          emotion: emotion.toString(),
          googleEventId: event.googleEventId,
        );

        // 3. Hive에 영구 저장
        await _eventsBox.put(eventId, updatedEvent);

        // 4. 감정 상태도 따로 저장
        await _emotionsBox.put(eventId, emotion.index);

        print('Emotion cached successfully: $eventId -> $emotion');
      } else {
        print('Event not found in cache or invalid type: $eventId');
      }
    } catch (e) {
      print('Error caching emotion: $e');
      rethrow;
    }
  }

  Emotion? getEventEmotion(String eventId) {
    try {
      // 1. 먼저 이벤트에서 감정 확인
      final event = _eventsBox.get(eventId);
      if (event?.emotion != null) {
        return Emotion.values.firstWhere(
          (e) => e.toString() == event!.emotion,
          orElse: () => Emotion.neutral,
        );
      }

      // 2. 감정 상태 박스에서 확인
      final emotionIndex = _emotionsBox.get(eventId);
      if (emotionIndex != null) {
        return Emotion.values[emotionIndex];
      }
    } catch (e) {
      print('Error getting emotion: $e');
    }
    return null;
  }

  List<CalendarEventModel> getEventsForRange(DateTime start, DateTime end) {
    try {
      final events = _eventsBox.values.where((event) {
        return event.startTime
                .isAfter(start.subtract(const Duration(days: 1))) &&
            event.startTime.isBefore(end.add(const Duration(days: 1)));
      }).toList();

      return events.map((event) {
        final cachedEmotion = getEventEmotion(event.id);
        if (cachedEmotion != null) {
          return (event.copyWith(
            emotion: cachedEmotion.toString(),
          ) as CalendarEventModel);
        }
        return event;
      }).toList();
    } catch (e) {
      print('Error getting events: $e');
      return [];
    }
  }

  Future<void> _cleanOldCache() async {
    final thirtyDaysAgo = DateTime.now().subtract(const Duration(days: 30));
    final oldEvents = _eventsBox.values.where(
      (event) => event.startTime.isBefore(thirtyDaysAgo),
    );

    for (var event in oldEvents) {
      await _eventsBox.delete(event.id);
      await _emotionsBox.delete(event.id);
    }
  }

  Future<void> clear() async {
    await _eventsBox.clear();
    await _emotionsBox.clear();
  }

  Future<void> dispose() async {
    _cleanupTimer?.cancel();
    await _eventsBox.close();
    await _emotionsBox.close();
  }

  Future<void> removeEvent(String eventId) async {
    final box = await Hive.openBox<CalendarEventModel>('calendar_events');
    await box.delete(eventId);
  }

  Future<void> updateEvent(CalendarEventModel event) async {
    final box = await Hive.openBox<CalendarEventModel>('calendar_events');
    await box.put(event.id, event);
  }

  String? emotionToString(Emotion? emotion) {
    return emotion?.name;
  }

  Future<bool> isValid() async {
    try {
      final now = DateTime.now();
      final lastUpdate = await getLastUpdate();

      // lastUpdate가 null이면 캐시가 유효하지 않음
      if (lastUpdate == null) {
        return false;
      }

      // 캐시 유효 기간 확인
      return now.difference(lastUpdate) < validityDuration;
    } catch (e) {
      print('캐시 유효성 확인 오류: $e');
      return false;
    }
  }

  // 마지막 업데이트 시간을 가져오는 메서드 추가
  Future<DateTime?> getLastUpdate() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastUpdateStr = prefs.getString('last_update_key');

      if (lastUpdateStr == null) {
        return null;
      }

      return DateTime.parse(lastUpdateStr);
    } catch (e) {
      print('마지막 업데이트 시간 조회 오류: $e');
      return null;
    }
  }
}
