import 'package:flutter/material.dart';
import '../../../../core/presentation/styles/app_styles.dart';

class BirthDatePage extends StatefulWidget {
  final Function(DateTime) onNext;
  final bool isEditMode; // 수정 모드 여부

  const BirthDatePage({
    super.key,
    required this.onNext,
    this.isEditMode = false, // 기본값은 false
  });

  @override
  State<BirthDatePage> createState() => _BirthDatePageState();
}

class _BirthDatePageState extends State<BirthDatePage> {
  final List<String> _inputNumbers = ['', '', '', '', '', ''];
  int _currentIndex = 0;

  void _handleNumberInput(String number) {
    if (_currentIndex >= 6) return;

    setState(() {
      _inputNumbers[_currentIndex] = number;
      _currentIndex++;
    });
  }

  void _handleBackspace() {
    if (_currentIndex <= 0) return;

    setState(() {
      _currentIndex--;
      _inputNumbers[_currentIndex] = '';
    });
  }

  bool _isValidDate() {
    if (_currentIndex < 6) return false;

    try {
      final year = int.parse('19${_inputNumbers[0]}${_inputNumbers[1]}');
      final month = int.parse('${_inputNumbers[2]}${_inputNumbers[3]}');
      final day = int.parse('${_inputNumbers[4]}${_inputNumbers[5]}');

      if (month < 1 || month > 12) return false;
      if (day < 1 || day > 31) return false;

      final date = DateTime(year, month, day);
      return date.isBefore(DateTime.now());
    } catch (e) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // 수정 모드가 아닐 때만 프로필 아이콘과 메시지 표시
            if (!widget.isEditMode) ...[
              Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 프로필 아이콘
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.grey[200],
                            shape: BoxShape.circle,
                          ),
                          child: const Text(
                            '루미',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.black54,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // 메시지 박스들
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        '안녕하세요! 저는 당신을 더 잘 알고 싶어요.\n간단한 질문 몇 가지 드려도 될까요?',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        '먼저, 언제 태어나셨나요?',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ],
            // 생년월일 입력 UI 수정
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 입력 필드 컨테이너
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.grey[50],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // YY
                        Container(
                          width: 60,
                          height: 48,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey[200]!),
                          ),
                          child: Center(
                            child: Text(
                              (_inputNumbers[0] + _inputNumbers[1]).isEmpty
                                  ? 'YY'
                                  : _inputNumbers[0] + _inputNumbers[1],
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w500,
                                color: (_inputNumbers[0] + _inputNumbers[1])
                                        .isEmpty
                                    ? Colors.grey[400]
                                    : Colors.black,
                              ),
                            ),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Text(
                            '/',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey[400],
                            ),
                          ),
                        ),
                        // MM
                        Container(
                          width: 60,
                          height: 48,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey[200]!),
                          ),
                          child: Center(
                            child: Text(
                              (_inputNumbers[2] + _inputNumbers[3]).isEmpty
                                  ? 'MM'
                                  : _inputNumbers[2] + _inputNumbers[3],
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w500,
                                color: (_inputNumbers[2] + _inputNumbers[3])
                                        .isEmpty
                                    ? Colors.grey[400]
                                    : Colors.black,
                              ),
                            ),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Text(
                            '/',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey[400],
                            ),
                          ),
                        ),
                        // DD
                        Container(
                          width: 60,
                          height: 48,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey[200]!),
                          ),
                          child: Center(
                            child: Text(
                              (_inputNumbers[4] + _inputNumbers[5]).isEmpty
                                  ? 'DD'
                                  : _inputNumbers[4] + _inputNumbers[5],
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w500,
                                color: (_inputNumbers[4] + _inputNumbers[5])
                                        .isEmpty
                                    ? Colors.grey[400]
                                    : Colors.black,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  // 예시 텍스트
                  Padding(
                    padding: const EdgeInsets.only(left: 16),
                    child: Text(
                      '예시) 98/03/21',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const Spacer(),
            // 확인 버튼
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: double.infinity,
                height: 56,
                decoration: BoxDecoration(
                  color: _isValidDate() ? AppColors.primary : Colors.grey[300],
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: _isValidDate()
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
                  onPressed: _isValidDate()
                      ? () {
                          final year = int.parse(
                              '19${_inputNumbers[0]}${_inputNumbers[1]}');
                          final month = int.parse(
                              '${_inputNumbers[2]}${_inputNumbers[3]}');
                          final day = int.parse(
                              '${_inputNumbers[4]}${_inputNumbers[5]}');
                          widget.onNext(DateTime(year, month, day));
                        }
                      : null,
                  child: Text(
                    widget.isEditMode ? '수정 완료' : '다음',
                    style: TextStyle(
                      color: _isValidDate() ? Colors.white : Colors.black38,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // 숫자 키패드
            Container(
              color: Colors.grey[200],
              padding: const EdgeInsets.symmetric(vertical: 20),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildKeypadButton('1'),
                      _buildKeypadButton('2', subText: 'abc'),
                      _buildKeypadButton('3', subText: 'def'),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildKeypadButton('4', subText: 'ghi'),
                      _buildKeypadButton('5', subText: 'jkl'),
                      _buildKeypadButton('6', subText: 'mno'),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildKeypadButton('7', subText: 'pqrs'),
                      _buildKeypadButton('8', subText: 'tuv'),
                      _buildKeypadButton('9', subText: 'wxyz'),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      const SizedBox(width: 80),
                      _buildKeypadButton('0'),
                      _buildBackspaceButton(),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKeypadButton(String text, {String? subText}) {
    return SizedBox(
      width: 80,
      child: TextButton(
        onPressed: () => _handleNumberInput(text),
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              text,
              style: const TextStyle(
                fontSize: 24,
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
            if (subText != null)
              Text(
                subText,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildBackspaceButton() {
    return SizedBox(
      width: 80,
      child: TextButton(
        onPressed: _handleBackspace,
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero,
        ),
        child: const Icon(
          Icons.backspace_outlined,
          color: Colors.black87,
          size: 24,
        ),
      ),
    );
  }
}
