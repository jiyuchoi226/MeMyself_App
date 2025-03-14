import 'package:flutter/material.dart';

class EmotionSelector extends StatelessWidget {
  final Function(int) onEmotionSelected;
  final int? selectedEmotion;

  const EmotionSelector({
    super.key,
    required this.onEmotionSelected,
    this.selectedEmotion,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: List.generate(5, (index) {
        final emotionIndex = index + 1;
        return GestureDetector(
          onTap: () => onEmotionSelected(emotionIndex),
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: selectedEmotion == emotionIndex
                  ? Theme.of(context).primaryColor
                  : Colors.grey[200],
            ),
            child: Text(
              _getEmotionEmoji(emotionIndex),
              style: const TextStyle(fontSize: 32),
            ),
          ),
        );
      }),
    );
  }

  String _getEmotionEmoji(int emotion) {
    switch (emotion) {
      case 1:
        return '😢'; // 매우 나쁨
      case 2:
        return '😕'; // 나쁨
      case 3:
        return '😐'; // 보통
      case 4:
        return '🙂'; // 좋음
      case 5:
        return '😄'; // 매우 좋음
      default:
        return '😐';
    }
  }
}
