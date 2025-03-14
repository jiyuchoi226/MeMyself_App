import 'package:flutter/material.dart';

class AppColors {
  static const primary = Color(0xFF4285F4);
  static const background = Color(0xFFFCF2F4);
  static const textPrimary = Color(0xFF212121);
  static const textSecondary = Color(0xFF757575);
  static const surface = Color(0xFFFFFFFF);
}

class AppStyles {
  static final buttonDecoration = BoxDecoration(
    color: AppColors.surface,
    borderRadius: BorderRadius.circular(12),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.05),
        blurRadius: 10,
        offset: const Offset(0, 2),
      ),
    ],
  );

  static const messageBoxDecoration = BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.all(Radius.circular(16)),
    boxShadow: [
      BoxShadow(
        color: Color(0x0A000000),
        blurRadius: 8,
        offset: Offset(0, 2),
      ),
    ],
  );

  static ButtonStyle get elevatedButtonStyle => ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      );
}
