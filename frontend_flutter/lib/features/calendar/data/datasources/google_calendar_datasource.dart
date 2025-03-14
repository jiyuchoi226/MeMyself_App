import 'package:googleapis/calendar/v3.dart' as calendar;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:extension_google_sign_in_as_googleapis_auth/extension_google_sign_in_as_googleapis_auth.dart';
import '../models/calendar_event_model.dart';
import 'calendar_cache_manager.dart';
import 'dart:async'; // Timer를 위한 import 수정
import '../../domain/entities/calendar_event.dart';
import 'package:dio/dio.dart';

abstract class GoogleCalendarDataSource {
  Future<List<CalendarEventModel>> getEvents(DateTime date);
  Future<List<CalendarEventModel>> getEventsForRange(
      DateTime start, DateTime end);
  Future<void> deleteEvent(String eventId);
  Future<void> updateEvent(CalendarEvent event);
}

class GoogleCalendarDataSourceImpl implements GoogleCalendarDataSource {
  final GoogleSignIn _googleSignIn;
  final CalendarCacheManager _cacheManager;
  calendar.CalendarApi? _calendarApi;
  Timer? _syncTimer;

  GoogleCalendarDataSourceImpl(this._googleSignIn, this._cacheManager) {
    _startPeriodicSync();
  }

  void _startPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(const Duration(minutes: 5), (_) {
      _syncCalendarData();
    });
  }

  Future<void> _syncCalendarData() async {
    try {
      final now = DateTime.now();
      final startOfMonth = DateTime(now.year, now.month - 1, 1); // 이전 달부터
      final endOfMonth = DateTime(now.year, now.month + 2, 0); // 다음 달까지

      final events = await _fetchEventsFromGoogle(startOfMonth, endOfMonth);
      await _cacheManager.cacheEvents(events);
    } catch (e) {
      print('Calendar sync failed: $e');
    }
  }

  Future<List<CalendarEventModel>> _fetchEventsFromGoogle(
    DateTime start,
    DateTime end,
  ) async {
    final calendarApi = await _getCalendarApi();
    final events = await calendarApi.events.list(
      'primary',
      timeMin: start.toUtc(),
      timeMax: end.toUtc(),
      singleEvents: true,
      orderBy: 'startTime',
    );

    return events.items
            ?.map((event) => CalendarEventModel.fromGoogleEvent(event))
            .toList() ??
        [];
  }

  Future<calendar.CalendarApi> _getCalendarApi() async {
    if (_calendarApi != null) return _calendarApi!;

    final httpClient = await _googleSignIn.authenticatedClient();
    if (httpClient == null) {
      throw Exception('Failed to get authenticated client');
    }

    _calendarApi = calendar.CalendarApi(httpClient);
    return _calendarApi!;
  }

  @override
  Future<List<CalendarEventModel>> getEvents(DateTime date) async {
    try {
      final calendarApi = await _getCalendarApi();

      final startOfDay = DateTime(date.year, date.month, date.day);
      final endOfDay = startOfDay.add(const Duration(days: 1));

      final events = await calendarApi.events.list(
        'primary',
        timeMin: startOfDay.toUtc(),
        timeMax: endOfDay.toUtc(),
        singleEvents: true,
        orderBy: 'startTime',
      );

      return events.items?.map((event) {
            return CalendarEventModel.fromGoogleEvent(event);
          }).toList() ??
          [];
    } catch (e) {
      print('Failed to fetch calendar events: $e');
      throw Exception('Failed to fetch calendar events');
    }
  }

  @override
  Future<List<CalendarEventModel>> getEventsForRange(
    DateTime start,
    DateTime end,
  ) async {
    try {
      // 1. 캐시 확인
      final cachedEvents = await _cacheManager.getEventsForRange(start, end);
      if (cachedEvents.isNotEmpty) {
        return cachedEvents;
      }

      // 2. API 호출 준비
      final client = await _googleSignIn.authenticatedClient();
      if (client == null) {
        throw Exception('인증된 클라이언트를 가져올 수 없습니다');
      }

      // 대신 Dio를 사용하여 타임아웃 설정
      final dio = Dio();
      dio.options.connectTimeout = const Duration(seconds: 10);
      dio.options.receiveTimeout = const Duration(seconds: 15);

      // 3. API 호출
      final calendarApi = calendar.CalendarApi(client);

      // API 호출에 타임아웃 설정
      final events = await calendarApi.events
          .list(
        'primary',
        timeMin: start.toUtc(),
        timeMax: end.toUtc(),
        singleEvents: true,
        orderBy: 'startTime',
      )
          .timeout(const Duration(seconds: 15), onTimeout: () {
        // 타임아웃 발생 시 빈 응답 반환
        print('Google Calendar API 호출 타임아웃');
        return calendar.Events();
      });

      // 4. 결과 처리 및 캐싱
      final List<CalendarEventModel> result = [];
      if (events.items != null) {
        for (var event in events.items!) {
          if (event.status != 'cancelled') {
            result.add(CalendarEventModel.fromGoogleEvent(event));
          }
        }
      }

      // 캐시에 저장
      await _cacheManager.cacheEvents(result);

      return result;
    } catch (e) {
      print('Google Calendar API 호출 오류: $e');
      // 오류 발생 시 빈 목록 반환
      return [];
    }
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
  }

  @override
  Future<void> deleteEvent(String eventId) async {
    // Google Calendar API를 통한 이벤트 삭제 구현
  }

  @override
  Future<void> updateEvent(CalendarEvent event) async {
    final calendarApi = await _getCalendarApi();
    final googleEvent = calendar.Event()
      ..summary = event.title
      ..start = calendar.EventDateTime(dateTime: event.startTime)
      ..end = calendar.EventDateTime(dateTime: event.endTime)
      ..description = event.description;

    await calendarApi.events.update(
      googleEvent,
      'primary',
      event.id,
    );
  }
}

extension on CalendarEventModel {
  static CalendarEventModel fromGoogleEvent(calendar.Event event) {
    final startTime = event.start?.dateTime ?? DateTime.now();
    final endTime =
        event.end?.dateTime ?? startTime.add(const Duration(hours: 1));

    return CalendarEventModel(
      id: event.id ?? '',
      googleEventId: event.id ?? '',
      title: event.summary ?? '(제목 없음)',
      description: event.description ?? '',
      startTime: startTime,
      endTime: endTime,
    );
  }
}
