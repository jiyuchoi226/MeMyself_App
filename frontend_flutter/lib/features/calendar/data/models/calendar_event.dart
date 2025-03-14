class CalendarEvent {
  final String id;
  final String title;
  final DateTime start;
  final DateTime end;
  final String? description;

  CalendarEvent({
    required this.id,
    required this.title,
    required this.start,
    required this.end,
    this.description,
  });

  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    return CalendarEvent(
      id: json['id'] as String,
      title: json['summary'] as String,
      start: DateTime.parse(json['start']['dateTime'] as String),
      end: DateTime.parse(json['end']['dateTime'] as String),
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'summary': title,
      'start': {'dateTime': start.toIso8601String()},
      'end': {'dateTime': end.toIso8601String()},
      if (description != null) 'description': description,
    };
  }
}
