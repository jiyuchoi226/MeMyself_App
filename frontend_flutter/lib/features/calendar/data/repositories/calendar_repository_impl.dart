import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/calendar_event.dart';
import '../../domain/entities/emotion.dart';
import '../../domain/repositories/calendar_repository.dart';
import '../datasources/google_calendar_datasource.dart';
import '../datasources/calendar_cache_manager.dart';
import '../models/calendar_event_model.dart';

class CalendarRepositoryImpl implements CalendarRepository {
  final GoogleCalendarDataSource dataSource;
  final CalendarCacheManager cacheManager;

  CalendarRepositoryImpl(this.dataSource, this.cacheManager);

  @override
  Future<Either<Failure, List<CalendarEvent>>> getEvents(DateTime date) async {
    try {
      final events = await dataSource.getEvents(date);
      final eventsWithEmotions = events.map((event) {
        final cachedEmotion = cacheManager.getEventEmotion(event.id);
        if (cachedEmotion != null) {
          return event.copyWith(
            emotion: cachedEmotion.toString(),
          );
        }
        return event;
      }).toList();
      return Right(eventsWithEmotions);
    } catch (e) {
      print('Calendar error: $e');
      return Left(ServerFailure());
    }
  }

  @override
  Future<Either<Failure, List<CalendarEvent>>> getEventsForRange(
    DateTime start,
    DateTime end,
  ) async {
    try {
      // 1. 먼저 캐시에서 이벤트 가져오기
      final cachedEvents = cacheManager.getEventsForRange(start, end);
      if (cachedEvents.isNotEmpty) {
        return Right(cachedEvents);
      }

      // 2. 캐시에 없으면 API에서 가져오기
      final events = await dataSource.getEventsForRange(start, end);
      await cacheManager.cacheEvents(events);

      // 3. 감정 상태 적용
      final eventsWithEmotions = events.map((event) {
        final cachedEmotion = cacheManager.getEventEmotion(event.id);
        if (cachedEmotion != null) {
          return event.copyWith(
            emotion: cachedEmotion.toString(),
            emotionObj: cachedEmotion,
          );
        }
        return event;
      }).toList();

      return Right(eventsWithEmotions);
    } catch (e) {
      return Left(ServerFailure());
    }
  }

  @override
  Future<Either<Failure, void>> updateEventEmotion(
    String eventId,
    Emotion emotion,
  ) async {
    try {
      // 1. 캐시에 감정 저장
      await cacheManager.cacheEventEmotion(eventId, emotion);

      // 2. 이벤트 목록 업데이트
      final events = await dataSource.getEventsForRange(
        DateTime.now().subtract(const Duration(days: 30)),
        DateTime.now().add(const Duration(days: 30)),
      );

      // 3. 업데이트된 이벤트들 캐시에 저장
      await cacheManager.cacheEvents(events);

      print('Emotion saved to cache for event: $eventId, emotion: $emotion');
      return const Right(null);
    } catch (e) {
      print('Error saving emotion: $e');
      return Left(ServerFailure());
    }
  }

  @override
  Future<void> deleteEvent(String eventId) async {
    await dataSource.deleteEvent(eventId);
    await cacheManager.removeEvent(eventId);
  }

  @override
  Future<void> updateEvent(CalendarEvent event) async {
    await dataSource.updateEvent(event);
    if (event is CalendarEventModel) {
      await cacheManager.updateEvent(event);
    }
  }
}
