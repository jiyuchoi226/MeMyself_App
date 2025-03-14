import 'package:hive/hive.dart';
import '../models/calendar_event_model.dart';
import '../../domain/entities/emotion.dart';
import '../../domain/entities/emotion_adapter.dart';

class CalendarCacheManager {
  static const String eventsBoxName = 'calendar_events';
  static const String emotionsBoxName = 'event_emotions';
  late Box<CalendarEventModel> _eventsBox;
  late Box<int> _emotionsBox; // Emotion enum의 index를 저장

  Future<void> init() async {
    try {
      if (!Hive.isAdapterRegistered(0)) {
        Hive.registerAdapter(CalendarEventModelAdapter());
      }
      if (!Hive.isAdapterRegistered(1)) {
        Hive.registerAdapter(EmotionAdapter());
      }

      _eventsBox = await Hive.openBox<CalendarEventModel>(eventsBoxName);
      _emotionsBox = await Hive.openBox<int>(emotionsBoxName);

      print('CalendarCacheManager initialized successfully');
    } catch (e) {
      print('Error initializing CalendarCacheManager: $e');
      rethrow;
    }
  }

  Future<void> cacheEvents(List<CalendarEventModel> events) async {
    final Map<String, CalendarEventModel> eventMap = {
      for (var event in events) event.id: event
    };
    await _eventsBox.putAll(eventMap);
  }

  Future<void> cacheEventEmotion(String eventId, Emotion emotion) async {
    final event = _eventsBox.get(eventId);
    if (event != null) {
      final updatedEvent = CalendarEventModel(
        id: event.id,
        title: event.title,
        startTime: event.startTime,
        endTime: event.endTime,
        description: event.description,
        emotion: emotion.toString(), // Emotion을 String으로 변환
        googleEventId: event.googleEventId,
      );
      await _eventsBox.put(eventId, updatedEvent);
    }
  }

  Emotion? getEventEmotion(String eventId) {
    final emotionIndex = _emotionsBox.get(eventId);
    if (emotionIndex == null) return null;
    return Emotion.values[emotionIndex];
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
          return CalendarEventModel(
            id: event.id,
            title: event.title,
            startTime: event.startTime,
            endTime: event.endTime,
            description: event.description,
            emotion: cachedEmotion.toString(), // Emotion을 String으로 변환
            googleEventId: event.googleEventId,
          );
        }
        return event;
      }).toList();
    } catch (e) {
      print('Error getting events: $e');
      return [];
    }
  }

  Future<void> clear() async {
    await _eventsBox.clear();
    await _emotionsBox.clear();
  }

  Future<void> dispose() async {
    await _eventsBox.close();
    await _emotionsBox.close();
  }
}
