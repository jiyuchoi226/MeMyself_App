import '../models/calendar_event.dart';

class CalendarApiService {
  // 캘린더 API 서비스 구현

  Future<List<CalendarEvent>> fetchEvents(DateTime start, DateTime end) async {
    try {
      // Google Calendar API 호출 구현
      // TODO: 실제 API 호출 로직 구현
      return [];
    } catch (e) {
      print('Error fetching events: $e');
      rethrow;
    }
  }
}
