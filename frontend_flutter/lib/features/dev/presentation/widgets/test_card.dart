import 'package:flutter/material.dart';

class TestCard extends StatelessWidget {
  final String title;
  final String? content;
  final Widget? child;
  final VoidCallback? onCopyPressed;

  const TestCard({
    super.key,
    required this.title,
    this.content,
    this.child,
    this.onCopyPressed,
  }) : assert(content != null || child != null);

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
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (onCopyPressed != null)
                  IconButton(
                    icon: const Icon(Icons.copy),
                    onPressed: onCopyPressed,
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (content != null) Text(content!) else if (child != null) child!,
          ],
        ),
      ),
    );
  }
}
