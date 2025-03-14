import 'package:flutter/material.dart';

class ResultCard extends StatelessWidget {
  final TextEditingController controller;
  final bool isLoading;

  const ResultCard({
    super.key,
    required this.controller,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '테스트 결과',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (isLoading)
                  const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: controller,
              maxLines: 8,
              readOnly: true,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Color(0xFFF5F5F5),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
