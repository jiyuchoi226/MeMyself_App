import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../../domain/entities/calendar_event.dart';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

class CalendarCache {
  static const String _eventsKey = 'calendar_events';
  static const String _colorsKey = 'calendar_colors';
  static const String _lastUpdateKey = 'calendar_last_update';
  static const String _userIdKey = 'calendar_user_id';

  // 캐시 유효 시간 (6시간)
  static const Duration _cacheValidity = Duration(hours: 6);

  // 이벤트 캐싱
  static Future<void> cacheEvents(
    Map<DateTime, List<CalendarEvent>> events,
    Map<String, Color> colors,
  ) async {
    final prefs = await SharedPreferences.getInstance();

    // 이벤트를 JSON으로 변환
    final Map<String, List<String>> serializedEvents = {};
    events.forEach((date, eventList) {
      serializedEvents[date.toIso8601String()] =
          eventList.map((e) => jsonEncode(_eventToJson(e))).toList();
    });

    // 색상을 JSON으로 변환
    final Map<String, String> serializedColors = {};
    colors.forEach((id, color) {
      serializedColors[id] = color.value.toString();
    });

    // 캐시에 저장
    await prefs.setString(_eventsKey, jsonEncode(serializedEvents));
    await prefs.setString(_colorsKey, jsonEncode(serializedColors));
    await prefs.setString(_lastUpdateKey, DateTime.now().toIso8601String());
    await prefs.setString(
        _userIdKey, FirebaseAuth.instance.currentUser?.uid ?? '');
  }

  // CalendarEvent를 JSON으로 변환하는 헬퍼 메소드
  static Map<String, dynamic> _eventToJson(CalendarEvent event) {
    return {
      'id': event.id,
      'title': event.title,
      'description': event.description,
      'date': event.date.toIso8601String(),
      'startTime': event.startTime.toIso8601String(),
      'endTime': event.endTime.toIso8601String(),
      'emotion': event.emotion,
      'isAllDay': event.isAllDay,
    };
  }

  // JSON에서 CalendarEvent로 변환하는 헬퍼 메소드
  static CalendarEvent _eventFromJson(Map<String, dynamic> json) {
    // 날짜 파싱
    final date = DateTime.parse(json['date']);

    // startTime과 endTime 기본값 설정
    final DateTime defaultStart =
        DateTime(date.year, date.month, date.day, 9, 0, 0); // 오전 9시
    final DateTime defaultEnd =
        DateTime(date.year, date.month, date.day, 10, 0, 0); // 오전 10시

    return CalendarEvent(
      id: json['id'],
      title: json['title'],
      description: json['description'] ?? '',
      date: date,
      startTime: json['startTime'] != null
          ? DateTime.parse(json['startTime'])
          : defaultStart,
      endTime: json['endTime'] != null
          ? DateTime.parse(json['endTime'])
          : defaultEnd,
      emotion: json['emotion'],
      isAllDay: json['isAllDay'] ?? false,
    );
  }

  // 캐시에서 이벤트 가져오기
  static Future<Map<DateTime, List<CalendarEvent>>> getEvents() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? eventsJson = prefs.getString(_eventsKey);

      if (eventsJson == null) return {};

      final Map<String, dynamic> serializedEvents =
          jsonDecode(eventsJson) as Map<String, dynamic>;

      final Map<DateTime, List<CalendarEvent>> events = {};
      serializedEvents.forEach((dateStr, eventListJson) {
        final date = DateTime.parse(dateStr);
        final List<dynamic> eventList = eventListJson as List<dynamic>;
        events[date] = eventList
            .map((e) => _eventFromJson(jsonDecode(e as String)))
            .toList();
      });

      return events;
    } catch (e) {
      print('캐시에서 이벤트 로드 오류: $e');
      return {};
    }
  }

  // 캐시 갱신 필요 여부 확인
  static Future<bool> shouldRefresh() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? lastUpdateStr = prefs.getString(_lastUpdateKey);
      final String? cachedUserId = prefs.getString(_userIdKey);
      final String? currentUserId = FirebaseAuth.instance.currentUser?.uid;

      // 사용자가 변경되었거나 캐시가 없는 경우
      if (lastUpdateStr == null || cachedUserId != currentUserId) {
        return true;
      }

      // 캐시 유효 시간 확인
      final lastUpdate = DateTime.parse(lastUpdateStr);
      return DateTime.now().difference(lastUpdate) > _cacheValidity;
    } catch (e) {
      return true;
    }
  }

  // 색상 가져오기 메소드 추가
  static Future<Map<String, Color>> getColors() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? colorsJson = prefs.getString(_colorsKey);

      if (colorsJson == null) return {};

      final Map<String, dynamic> serializedColors =
          jsonDecode(colorsJson) as Map<String, dynamic>;

      final Map<String, Color> colors = {};
      serializedColors.forEach((id, colorValue) {
        colors[id] = Color(int.parse(colorValue));
      });

      return colors;
    } catch (e) {
      print('캐시에서 색상 로드 오류: $e');
      return {};
    }
  }
}
