import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../entities/calendar_event.dart';
import '../entities/emotion.dart';

abstract class CalendarRepository {
  Future<Either<Failure, List<CalendarEvent>>> getEvents(DateTime date);
  Future<Either<Failure, List<CalendarEvent>>> getEventsForRange(
    DateTime start,
    DateTime end,
  );
  Future<Either<Failure, void>> updateEventEmotion(
      String eventId, Emotion emotion);
  Future<void> deleteEvent(String eventId);
  Future<void> updateEvent(CalendarEvent event);
}
