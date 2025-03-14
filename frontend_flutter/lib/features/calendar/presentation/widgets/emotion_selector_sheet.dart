import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/entities/calendar_event.dart' as entities;
import '../../domain/entities/emotion.dart';
import '../bloc/calendar_bloc.dart';

class EmotionSelectorSheet extends StatelessWidget {
  final entities.CalendarEvent event;
  final Function(Emotion) onEmotionSelected;

  const EmotionSelectorSheet({
    super.key,
    required this.event,
    required this.onEmotionSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '오늘 이 일정은 어떠셨나요?',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            event.title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.grey[600],
                ),
          ),
          const SizedBox(height: 24),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildEmotionButton(
                    context,
                    Emotion.veryBad,
                    event.emotionObj == Emotion.veryBad,
                  ),
                  _buildEmotionButton(
                    context,
                    Emotion.bad,
                    event.emotionObj == Emotion.bad,
                  ),
                  _buildEmotionButton(
                    context,
                    Emotion.neutral,
                    event.emotionObj == Emotion.neutral,
                  ),
                  _buildEmotionButton(
                    context,
                    Emotion.good,
                    event.emotionObj == Emotion.good,
                  ),
                  _buildEmotionButton(
                    context,
                    Emotion.veryGood,
                    event.emotionObj == Emotion.veryGood,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.deepPurple,
              minimumSize: const Size(double.infinity, 48),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text(
              '닫기',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmotionButton(
    BuildContext context,
    Emotion emotion,
    bool isSelected,
  ) {
    return GestureDetector(
      onTap: () {
        // 감정 선택 시 CalendarBloc에 이벤트 전달
        context.read<CalendarBloc>().add(UpdateEventEmotion(event.id, emotion));

        // 콜백 함수 호출
        onEmotionSelected(emotion);

        // 바텀시트 닫기
        Navigator.pop(context);
      },
      child: SizedBox(
        width: 64, // 고정 너비 사용
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: isSelected
                    ? Colors.deepPurple.withOpacity(0.1)
                    : Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
                border: isSelected
                    ? Border.all(color: Colors.deepPurple, width: 2)
                    : null,
              ),
              child: Center(
                child: Text(
                  emotion.emoji,
                  style: const TextStyle(fontSize: 26),
                ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              emotion.description,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 11,
                height: 1.2,
                color: isSelected ? Colors.deepPurple : Colors.grey[600],
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }
}
