import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/entities/message.dart';

/// 로컬 저장소를 이용한 채팅 기록 관리 클래스
class ChatLocalStorage {
  static const String _keyPrefix = 'chat_history_';

  /// 대화 메시지 저장
  ///
  /// [chatId] 대화 ID
  /// [message] 저장할 메시지 정보
  Future<void> saveMessage(String chatId, Message message) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // 기존 메시지 목록 가져오기
      final List<Message> messages = await _getMessagesInternal(chatId);

      // 새 메시지 추가
      messages.add(message);

      // JSON으로 변환
      final jsonMessages = messages.map((msg) => msg.toJson()).toList();

      // 저장
      await prefs.setString('chat_$chatId', jsonEncode(jsonMessages));
      print(
          '메시지 저장 완료: ${message.text.substring(0, min(20, message.text.length))}...');
    } catch (e) {
      print('메시지 저장 오류: $e');
    }
  }

  /// 내부용 대화 기록 불러오기 메서드
  Future<List<Message>> _getMessagesInternal(String chatId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? jsonData = prefs.getString('chat_$chatId');

      if (jsonData == null || jsonData.isEmpty) {
        return [];
      }

      final List<dynamic> decodedData = jsonDecode(jsonData);
      return decodedData.map((item) => Message.fromJson(item)).toList();
    } catch (e) {
      print('메시지 조회 오류: $e');
      return [];
    }
  }

  /// 대화 기록 불러오기 (인스턴스 메서드)
  Future<List<Message>> getMessages(String chatId) async {
    return _getMessagesInternal(chatId);
  }

  /// 대화 기록 불러오기 (정적 메서드)
  static Future<List<Message>> getMessagesStatic(String chatId) async {
    final instance = ChatLocalStorage();
    return await instance._getMessagesInternal(chatId);
  }

  /// 대화 기록 초기화
  ///
  /// [chatId] 대화 ID
  static Future<void> clearMessages(String chatId) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _keyPrefix + chatId;
    await prefs.remove(key);
  }
}

// min 함수 정의
int min(int a, int b) => a < b ? a : b;
