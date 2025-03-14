import 'package:flutter/material.dart';

class EmotionScore {
  static const Map<int, IconData> emotionIcons = {
    1: Icons.sentiment_very_dissatisfied,    // 매우 불만족 😫
    2: Icons.sentiment_dissatisfied,         // 불만족 😞
    3: Icons.sentiment_neutral,              // 보통 😐
    4: Icons.sentiment_satisfied,            // 만족 🙂
    5: Icons.sentiment_very_satisfied,       // 매우 만족 😊
  };

  static const Map<int, String> emotionLabels = {
    1: '매우 나쁨',
    2: '나쁨',
    3: '보통',
    4: '좋음',
    5: '매우 좋음',
  };

  static Color getEmotionColor(int score) {
    switch (score) {
      case 1:
        return Colors.red[300]!;
      case 2:
        return Colors.orange[300]!;
      case 3:
        return Colors.yellow[700]!;
      case 4:
        return Colors.lightGreen[400]!;
      case 5:
        return Colors.green[400]!;
      default:
        return Colors.grey;
    }
  }
} 