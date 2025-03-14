import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/calendar_bloc.dart';
import '../../domain/entities/load_priority.dart';
import '../../data/datasources/calendar_cache.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  @override
  void initState() {
    super.initState();

    // 캐시된 데이터 먼저 표시 (UI 빠르게 로드)
    _loadCachedData();

    // 현재 월 로드 (높은 우선순위)
    final now = DateTime.now();
    final currentMonth = DateTime(now.year, now.month, 1);

    // 약간의 지연을 두고 현재 월 데이터 요청 (UI가 먼저 렌더링되도록)
    Future.microtask(() {
      context
          .read<CalendarBloc>()
          .add(LoadMonthEvents(currentMonth, priority: LoadPriority.high));
    });

    // 인접 월 백그라운드 로드 (낮은 우선순위)
    Future.delayed(const Duration(seconds: 2), () {
      final prevMonth = DateTime(now.year, now.month - 1, 1);
      final nextMonth = DateTime(now.year, now.month + 1, 1);

      context
          .read<CalendarBloc>()
          .add(LoadMonthEvents(prevMonth, priority: LoadPriority.low));

      // 약간의 시간차를 두고 다음 달 로드
      Future.delayed(const Duration(milliseconds: 500), () {
        context
            .read<CalendarBloc>()
            .add(LoadMonthEvents(nextMonth, priority: LoadPriority.low));
      });
    });

    // 사용자 활성 상태 업데이트
    _updateActiveStatus();
  }

  // 사용자 활성 상태 업데이트 메서드 수정
  Future<void> _updateActiveStatus() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return;

      final googleSignIn = GoogleSignIn();
      final googleUser = await googleSignIn.signInSilently();
      if (googleUser == null) return;

      final googleAuth = await googleUser.authentication;
      final token = googleAuth.accessToken;
      if (token == null) return;

      final userId = user.email;
      const baseUrl = 'http://10.0.2.2:8000';

      // 현재 날짜와 한 달 후 날짜 계산
      final now = DateTime.now();
      final startDate = DateTime(now.year, now.month, 1).toIso8601String();
      final endDate = DateTime(now.year, now.month + 1, 0).toIso8601String();

      print('사용자 활성 상태 업데이트 시작');
      print('API 요청 데이터: ${jsonEncode({
            'user_id': userId,
            'token': token,
            'start_date': startDate,
            'end_date': endDate,
          })}');

      final response = await http.post(
        Uri.parse('$baseUrl/update-active-status'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'user_id': userId,
          'token': token,
          'start_date': startDate,
          'end_date': endDate,
        }),
      );

      if (response.statusCode == 200) {
        print('사용자 활성 상태 업데이트 성공');
      } else {
        print('사용자 활성 상태 업데이트 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('사용자 활성 상태 업데이트 오류: $e');
      // 3초 후 재시도
      Future.delayed(const Duration(seconds: 3), () {
        _updateActiveStatus();
      });
    }
  }

  Future<void> _loadCachedData() async {
    final shouldRefresh = await CalendarCache.shouldRefresh();
    if (!shouldRefresh) {
      final cachedEvents = await CalendarCache.getEvents();
      final cachedColors = await CalendarCache.getColors();

      if (cachedEvents.isNotEmpty) {
        context
            .read<CalendarBloc>()
            .add(UpdateCachedEvents(cachedEvents, cachedColors));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // 기존 build 메서드 내용 유지
    return Container(); // 실제 UI 구현으로 대체
  }
}
