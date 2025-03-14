import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AnimatedMbtiButton extends StatelessWidget {
  final String letter;
  final bool isSelected;
  final VoidCallback onTap;

  const AnimatedMbtiButton({
    super.key,
    required this.letter,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      width: 64,
      height: 64,
      decoration: BoxDecoration(
        color: isSelected ? Colors.blue[100] : Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
        boxShadow: isSelected
            ? [
                BoxShadow(
                  color: Colors.blue.withOpacity(0.2),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            HapticFeedback.selectionClick();
            onTap();
          },
          borderRadius: BorderRadius.circular(8),
          child: Center(
            child: AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: TextStyle(
                fontSize: 24,
                color: isSelected ? Colors.blue : Colors.black87,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
              child: Text(letter),
            ),
          ),
        ),
      ),
    );
  }
}
