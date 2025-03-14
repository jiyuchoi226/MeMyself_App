import 'emotion.dart';
import 'package:flutter/painting.dart';

class CalendarEvent {
  final String id;
  final DateTime date;
  final String? emoji;
  final String? emotion;
  final String title;
  final DateTime startTime;
  final DateTime endTime;
  final String? description;
  final Emotion? emotionObj;
  final bool isAllDay;
  final Color color;

  const CalendarEvent({
    required this.id,
    required this.date,
    this.emoji,
    this.emotion,
    required this.title,
    required this.startTime,
    required this.endTime,
    this.description,
    this.emotionObj,
    this.isAllDay = false,
    this.color = const Color(0xFF4285F4),
  });

  CalendarEvent copyWith({
    String? id,
    DateTime? date,
    String? emoji,
    String? emotion,
    String? title,
    DateTime? startTime,
    DateTime? endTime,
    String? description,
    Emotion? emotionObj,
    bool? isAllDay,
    Color? color,
  }) {
    return CalendarEvent(
      id: id ?? this.id,
      date: date ?? this.date,
      emoji: emoji ?? this.emoji,
      emotion: emotion ?? this.emotion,
      title: title ?? this.title,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      description: description ?? this.description,
      emotionObj: emotionObj ?? this.emotionObj,
      isAllDay: isAllDay ?? this.isAllDay,
      color: color ?? this.color,
    );
  }

  // 서버 응답에서 CalendarEvent 객체 생성
  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    return CalendarEvent(
      id: json['id'] ?? '',
      date: DateTime.parse(json['date'] ?? DateTime.now().toIso8601String()),
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      startTime: DateTime.parse(json['start_time']),
      endTime: DateTime.parse(json['end_time']),
      isAllDay: json['is_all_day'] ?? false,
      color: Color(int.parse(json['color'] ?? '0xFF4285F4')),
    );
  }

  DateTime get start => startTime;
}
