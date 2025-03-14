import 'package:flutter/material.dart';

class LumyProfileImage extends StatelessWidget {
  final double radius;
  final Color? backgroundColor;
  final Color? textColor;

  const LumyProfileImage({
    super.key,
    this.radius = 20,
    this.backgroundColor = const Color(0xFFE8E8FD),
    this.textColor = const Color(0xFF6B4EFF),
  });

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: radius,
      backgroundColor: backgroundColor,
      child: Text(
        '루미',
        style: TextStyle(
          color: textColor,
          fontSize: radius * 0.7,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
