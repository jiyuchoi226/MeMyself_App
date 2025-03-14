import '../entities/calendar_event.dart';
import '../../data/models/calendar_event_model.dart';

extension CalendarEventExtension on CalendarEvent {
  CalendarEventModel toModel() {
    return CalendarEventModel(
      id: id,
      title: title,
      startTime: startTime,
      endTime: endTime,
      description: description ?? '',
      googleEventId: id, // 임시로 id를 사용, 실제로는 적절한 값으로 대체 필요
    );
  }
}
