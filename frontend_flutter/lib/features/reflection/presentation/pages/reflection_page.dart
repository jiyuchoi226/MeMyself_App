import 'package:flutter/material.dart';

class ReflectionPage extends StatelessWidget {
  const ReflectionPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 회고'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: 0, // TODO: 실제 채팅 메시지 개수로 변경
              itemBuilder: (context, index) {
                return const SizedBox(); // TODO: 채팅 메시지 위젯 추가
              },
            ),
          ),
          // 입력 영역
          Container(
            padding: const EdgeInsets.all(8.0),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                ),
              ],
            ),
            child: Row(
              children: [
                const Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: '메시지를 입력하세요',
                      border: InputBorder.none,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () {
                    // TODO: 메시지 전송 구현
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
