import 'package:flutter/material.dart';
import '../styles/app_styles.dart';

class MessageBubble extends StatelessWidget {
  final String message;
  final bool isUser;

  const MessageBubble({
    super.key,
    required this.message,
    this.isUser = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isUser ? AppColors.primary.withOpacity(0.1) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Text(
        message,
        style: TextStyle(
          fontSize: 16,
          color: isUser ? AppColors.primary : AppColors.textPrimary,
        ),
      ),
    );
  }
}
