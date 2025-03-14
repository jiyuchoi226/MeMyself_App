import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io';

class ApiService {
  final Dio _dio = Dio();
  final String baseUrl;

  ApiService() : baseUrl = dotenv.env['API_URL'] ?? 'http://10.0.2.2:8000';

  // 캘린더 동기화
  Future<void> syncCalendar(String token, String userId) async {
    try {
      print('캘린더 동기화 요청 시작: $userId');
      final response = await _dio.post(
        '$baseUrl/sync-calendar',
        data: {
          'token': token,
          'user_id': userId,
        }
      );
      
      if (response.statusCode == 200) {
        print('동기화 성공: ${response.data}');
      } else {
        throw Exception('캘린더 동기화 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('동기화 실패: $e');
      rethrow;
    }
  }

  // 활성 상태 업데이트
  Future<void> updateActiveStatus(String token, String userId, bool isActive) async {
    try {
      print('활성 상태 업데이트 요청: userId=$userId, isActive=$isActive');
      final response = await _dio.post(
        '$baseUrl/update-active-status',
        data: {
          'token': token,
          'user_id': userId,
          'is_active': isActive,
        }
      );
      
      print('활성 상태 업데이트 응답: ${response.data}');
      
      if (response.statusCode != 200) {
        throw Exception('활성 상태 업데이트 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('활성 상태 업데이트 실패: $e');
      rethrow;
    }
  }

  // services/api_service.dart에 추가할 메서드
  Future<void> testFaiss(String userId, String question) async {
    try {
      final response = await _dio.post(
        '$baseUrl/test-faiss',
        data: {
          'user_id': userId,
          'question': question,
        },
      );
      print('FAISS 테스트 응답: ${response.data}');
    } catch (e) {
      print('FAISS 테스트 실패: $e');
      rethrow;
    }
  }

  // 에러 처리를 위한 헬퍼 메서드
  void _handleError(dynamic error) {
    if (error is DioException) {
      print('네트워크 에러: ${error.message}');
      if (error.response != null) {
        print('서버 응답: ${error.response?.data}');
      }
    } else {
      print('알 수 없는 에러: $error');
    }
    throw error;
  }
}