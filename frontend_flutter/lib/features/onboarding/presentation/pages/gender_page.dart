import 'package:flutter/material.dart';
import '../../../../core/presentation/styles/app_styles.dart';

class GenderPage extends StatefulWidget {
  final Function(String) onNext;
  final bool isEditMode;

  const GenderPage({
    super.key,
    required this.onNext,
    this.isEditMode = false,
  });

  @override
  State<GenderPage> createState() => _GenderPageState();
}

class _GenderPageState extends State<GenderPage> {
  String? _selectedGender;

  void _handleGenderSelect(String gender) {
    setState(() {
      _selectedGender = gender;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!widget.isEditMode) ...[
                const CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.grey,
                  child: Text(
                    '루미',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    '아, 그렇군요! 다음으로 성별을 여쭤볼게요.',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.black87,
                    ),
                  ),
                ),
              ],
              const Spacer(),
              Column(
                children: [
                  _buildGenderButton('남자'),
                  const SizedBox(height: 12),
                  _buildGenderButton('여자'),
                  const SizedBox(height: 12),
                  _buildGenderButton('둘다 아님'),
                ],
              ),
              Padding(
                padding: const EdgeInsets.all(24),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: double.infinity,
                  height: 56,
                  decoration: BoxDecoration(
                    color: _selectedGender != null
                        ? AppColors.primary
                        : Colors.grey[300],
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: _selectedGender != null
                        ? [
                            BoxShadow(
                              color: AppColors.primary.withOpacity(0.3),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ]
                        : null,
                  ),
                  child: TextButton(
                    onPressed: _selectedGender != null
                        ? () => widget.onNext(_selectedGender!)
                        : null,
                    child: Text(
                      widget.isEditMode ? '수정 완료' : '다음',
                      style: TextStyle(
                        color: _selectedGender != null
                            ? Colors.white
                            : Colors.black38,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGenderButton(String gender) {
    bool isSelected = _selectedGender == gender;
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color:
            isSelected ? AppColors.primary.withOpacity(0.1) : Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isSelected ? AppColors.primary : Colors.transparent,
          width: 1,
        ),
      ),
      child: TextButton(
        onPressed: () => _handleGenderSelect(gender),
        style: TextButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
        child: Text(
          gender,
          style: TextStyle(
            fontSize: 16,
            color: isSelected ? AppColors.primary : Colors.black87,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}
