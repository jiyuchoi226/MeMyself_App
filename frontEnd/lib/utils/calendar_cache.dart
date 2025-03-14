import 'package:flutter/material.dart';  // Color 클래스를 위해 필요
import 'package:hive_flutter/hive_flutter.dart';

class CalendarCache {
  static const String boxName = 'calendar_events';
  static String? _currentUserId;  // 현재 사용자 ID 저장

  // 사용자 ID 설정
  static void setUserId(String userId) {
    _currentUserId = userId;
  }

  static Future<void> initialize() async {
    await Hive.initFlutter();
    await Hive.openBox(boxName);
  }

  // 사용자별 키 생성
  static String _getUserKey(String key) {
    return '${_currentUserId ?? "default"}_$key';
  }

  static Future<void> cacheEvents(Map<DateTime, List<Map<String, dynamic>>> events, Map<String, Color> colors) async {
    if (_currentUserId == null) return;  // 사용자 ID가 없으면 저장하지 않음
    
    final box = Hive.box(boxName);
    final normalizedEvents = events.map((key, value) {
      final normalizedDate = DateTime(key.year, key.month, key.day);
      return MapEntry(
        normalizedDate.toIso8601String(),
        value.map((e) => Map<String, dynamic>.from(e)).toList(),
      );
    });

    await box.putAll({
      _getUserKey('events'): normalizedEvents,
      _getUserKey('colors'): colors.map((key, value) => MapEntry(key, value.value)),
      _getUserKey('last_updated'): DateTime.now().toIso8601String(),
    });
  }

  static Map<DateTime, List<Map<String, dynamic>>> getEvents() {
    if (_currentUserId == null) return {};  
    
    final box = Hive.box(boxName);
    final encodedEvents = box.get(_getUserKey('events')) as Map?;
    
    if (encodedEvents == null) return {};
    
    final decodedEvents = <DateTime, List<Map<String, dynamic>>>{};
    int totalEvents = 0;  // 전체 이벤트 개수를 세기 위한 변수

    encodedEvents.forEach((key, value) {
      try {
        final date = DateTime.parse(key as String);
        final normalizedDate = DateTime(date.year, date.month, date.day);
        decodedEvents[normalizedDate] = (value as List)
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
        totalEvents += (value as List).length;  // 해당 날짜의 이벤트 개수 추가
      } catch (e) {
        print('날짜 파싱 에러: $key - $e');
      }
    });
    
    print('캐시된 총 이벤트 개수: $totalEvents');  // 총 이벤트 개수 로그
    print('캐시된 날짜 수: ${decodedEvents.length}');  // 이벤트가 있는 날짜 수
    
    return decodedEvents;
  }

  static Map<String, Color> getColors() {
    if (_currentUserId == null) return {};
    
    final box = Hive.box(boxName);
    final encodedColors = box.get(_getUserKey('colors')) as Map?;
    
    if (encodedColors == null) return {};
    
    return encodedColors.map((key, value) => MapEntry(
      key.toString(),
      Color(value as int),
    ));
  }

  static bool shouldRefresh() {
    if (_currentUserId == null) return true;
    
    final box = Hive.box(boxName);
    final lastUpdated = box.get(_getUserKey('last_updated'));
    if (lastUpdated == null) return true;
    
    final lastUpdateTime = DateTime.parse(lastUpdated);
    // 마지막 업데이트로부터 5분이 지났는지 확인
    return DateTime.now().difference(lastUpdateTime).inMinutes >= 5;
  }

  static Future<void> clear() async {
    if (_currentUserId == null) return;
    
    final box = Hive.box(boxName);
    await box.delete(_getUserKey('events'));
    await box.delete(_getUserKey('colors'));
    await box.delete(_getUserKey('last_updated'));
  }

  // 효율적인 데이터 업데이트를 위한 메서드 추가
  static Future<void> updateEvents(Map<DateTime, List<Map<String, dynamic>>> newEvents, Map<String, Color> newColors) async {
    if (_currentUserId == null) return;

    final currentEvents = getEvents();
    final updatedEvents = Map<DateTime, List<Map<String, dynamic>>>.from(currentEvents);

    // 새로운 이벤트와 기존 이벤트 비교하여 업데이트
    newEvents.forEach((date, events) {
      if (!currentEvents.containsKey(date) || 
          !_areEventsEqual(currentEvents[date]!, events)) {
        updatedEvents[date] = events;
      }
    });

    // 삭제된 이벤트 처리
    currentEvents.keys.where((date) => !newEvents.containsKey(date))
        .forEach(updatedEvents.remove);

    // 변경된 데이터만 캐시 업데이트
    await cacheEvents(updatedEvents, newColors);
  }

  // 이벤트 리스트 비교 헬퍼 메서드
  static bool _areEventsEqual(List<Map<String, dynamic>> list1, List<Map<String, dynamic>> list2) {
    if (list1.length != list2.length) return false;
    
    for (var i = 0; i < list1.length; i++) {
      if (list1[i]['id'] != list2[i]['id'] ||
          list1[i]['updated'] != list2[i]['updated']) {
        return false;
      }
    }
    return true;
  }
} 