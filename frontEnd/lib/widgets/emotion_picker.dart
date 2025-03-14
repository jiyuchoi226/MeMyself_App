import 'package:flutter/material.dart';
import '../utils/emotion_score.dart';

class EmotionPicker extends StatelessWidget {
  final int? selectedScore;
  final Function(int) onSelected;

  const EmotionPicker({
    super.key,
    this.selectedScore,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: EmotionScore.emotionIcons.entries.map((entry) {
        final score = entry.key;
        final icon = entry.value;
        final isSelected = score == selectedScore;

        return Tooltip(
          message: EmotionScore.emotionLabels[score]!,
          child: InkWell(
            borderRadius: BorderRadius.circular(30),
            onTap: () => onSelected(score),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected 
                    ? EmotionScore.getEmotionColor(score).withOpacity(0.2)
                    : Colors.transparent,
              ),
              child: Icon(
                icon,
                size: 32,
                color: isSelected 
                    ? EmotionScore.getEmotionColor(score)
                    : Colors.grey[400],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
} 