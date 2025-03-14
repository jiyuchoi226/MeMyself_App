import 'package:flutter/material.dart';
import '../widgets/emotion_selector.dart';
import '../widgets/emotion_input.dart';

class EmotionPage extends StatefulWidget {
  const EmotionPage({super.key});

  @override
  State<EmotionPage> createState() => _EmotionPageState();
}

class _EmotionPageState extends State<EmotionPage> {
  int? selectedEmotion;
  final TextEditingController _contentController = TextEditingController();

  @override
  void dispose() {
    _contentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('감정 회고'),
        actions: [
          TextButton(
            onPressed: _saveEmotion,
            child: const Text('저장'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '오늘 하루는 어땠나요?',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            EmotionSelector(
              selectedEmotion: selectedEmotion,
              onEmotionSelected: (emotion) {
                setState(() {
                  selectedEmotion = emotion;
                });
              },
            ),
            const SizedBox(height: 32),
            EmotionInput(
              controller: _contentController,
              onChanged: (value) {
                // 필요한 경우 상태 업데이트
              },
            ),
          ],
        ),
      ),
    );
  }

  void _saveEmotion() {
    if (selectedEmotion == null || _contentController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('감정과 내용을 모두 입력해주세요')),
      );
      return;
    }

    // TODO: 감정 회고 저장 로직 구현
    Navigator.pop(context);
  }
}
