import '../../domain/entities/emotion.dart';

abstract class CalendarEvent {}

class UpdateEventEmotion extends CalendarEvent {
  final String eventId;
  final Emotion emotion;

  UpdateEventEmotion(this.eventId, this.emotion);
}
