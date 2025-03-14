import 'package:flutter/material.dart';

class LumyProfileHeader extends StatelessWidget {
  final double imageSize;
  final double fontSize;

  const LumyProfileHeader({
    super.key,
    this.imageSize = 40,
    this.fontSize = 16,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        CircleAvatar(
          radius: imageSize / 2,
          backgroundImage: const AssetImage('assets/images/lumy.png'),
          backgroundColor: Colors.transparent,
        ),
        const SizedBox(width: 8),
        Text(
          '루미',
          style: TextStyle(
            fontSize: fontSize,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
      ],
    );
  }
}
