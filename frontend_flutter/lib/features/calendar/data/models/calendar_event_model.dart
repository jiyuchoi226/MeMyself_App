import 'package:hive/hive.dart';
import '../../domain/entities/calendar_event.dart' hide Emotion;

part 'calendar_event_model.g.dart';

@HiveType(typeId: 0)
class CalendarEventModel extends CalendarEvent {
  @HiveField(0)
  @override
  final String id;

  @HiveField(1)
  @override
  final String title;

  @HiveField(2)
  @override
  final DateTime startTime;

  @HiveField(3)
  @override
  final DateTime endTime;

  @HiveField(4)
  @override
  final String? description;

  @HiveField(5)
  @override
  final String? emotion;

  @HiveField(6)
  final String googleEventId;

  CalendarEventModel({
    required this.id,
    required this.title,
    required this.startTime,
    required this.endTime,
    this.description,
    this.emotion,
    required this.googleEventId,
  }) : super(
          id: id,
          date: startTime,
          title: title,
          startTime: startTime,
          endTime: endTime,
          description: description,
          emotion: emotion,
          emoji: null,
        );

  factory CalendarEventModel.fromGoogleEvent(dynamic event) {
    final start = event.start.dateTime ?? DateTime.parse(event.start.date);
    final end = event.end.dateTime ?? DateTime.parse(event.end.date);

    return CalendarEventModel(
      id: event.id,
      googleEventId: event.id,
      title: event.summary ?? '',
      startTime: start,
      endTime: end,
      description: event.description,
    );
  }
}
