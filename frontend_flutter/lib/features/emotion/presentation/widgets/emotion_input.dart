import 'package:flutter/material.dart';

class EmotionInput extends StatelessWidget {
  final TextEditingController controller;
  final Function(String) onChanged;

  const EmotionInput({
    super.key,
    required this.controller,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '오늘 있었던 일을 기록해주세요',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          onChanged: onChanged,
          maxLines: 5,
          decoration: InputDecoration(
            hintText: '오늘 하루는 어떠셨나요?',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            filled: true,
            fillColor: Colors.grey[100],
          ),
        ),
      ],
    );
  }
}
