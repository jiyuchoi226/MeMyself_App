import 'package:flutter/material.dart';

class MbtiPage extends StatefulWidget {
  final Function(String) onNext;
  final bool isEditMode;

  const MbtiPage({
    super.key,
    required this.onNext,
    this.isEditMode = false,
  });

  @override
  State<MbtiPage> createState() => _MbtiPageState();
}

class _MbtiPageState extends State<MbtiPage> {
  final Map<int, String> _selectedLetters = {};

  // MBTI 옵션 정의 - 한 줄에 4개씩 배치
  final List<List<String>> mbtiGroups = [
    ['E', 'N', 'T', 'P'], // 첫 번째 줄
    ['I', 'S', 'F', 'J'], // 두 번째 줄
  ];

  void _handleLetterSelect(String letter, int position) {
    setState(() {
      // position을 그룹 인덱스로 변환
      int groupIndex = position % 4; // 0,1,2,3 위치에 따른 그룹

      // 같은 그룹의 다른 문자 선택 시 이전 선택 해제
      if (_selectedLetters[groupIndex] == letter) {
        _selectedLetters.remove(groupIndex); // 같은 문자 다시 클릭하면 선택 해제
      } else {
        _selectedLetters[groupIndex] = letter; // 새로운 문자 선택
      }
    });
  }

  bool _isLetterSelected(String letter) {
    return _selectedLetters.values.contains(letter);
  }

  bool _canProceed() {
    return _selectedLetters.length == 4;
  }

  String get _selectedMbti {
    final List<String> mbti = [];
    for (int i = 0; i < 4; i++) {
      mbti.add(_selectedLetters[i] ?? '');
    }
    return mbti.join();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
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
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        '마지막으로, MBTI 유형을 알려주실 수 있나요?',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const Spacer(),
            // MBTI 선택 버튼들 - 새로운 배치
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                children: [
                  // 첫 번째 줄 (E, N, T, P)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: List.generate(4, (index) {
                      String letter = mbtiGroups[0][index];
                      return _buildMbtiButton(letter, index);
                    }),
                  ),
                  const SizedBox(height: 16),
                  // 두 번째 줄 (I, S, F, J)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: List.generate(4, (index) {
                      String letter = mbtiGroups[1][index];
                      return _buildMbtiButton(letter, index);
                    }),
                  ),
                ],
              ),
            ),
            const Spacer(),
            // 확인 버튼
            Padding(
              padding: const EdgeInsets.all(24),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: double.infinity,
                height: 56,
                decoration: BoxDecoration(
                  color: _canProceed() ? Colors.blue : Colors.grey[300],
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: _canProceed()
                      ? [
                          BoxShadow(
                            color: Colors.blue.withOpacity(0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 4),
                          ),
                        ]
                      : null,
                ),
                child: TextButton(
                  onPressed:
                      _canProceed() ? () => widget.onNext(_selectedMbti) : null,
                  child: Text(
                    widget.isEditMode ? '수정 완료' : '다음',
                    style: TextStyle(
                      color: _canProceed() ? Colors.white : Colors.black38,
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
    );
  }

  Widget _buildMbtiButton(String letter, int position) {
    bool isSelected = _isLetterSelected(letter);
    int groupIndex = position % 4;
    bool isOppositeSelected = _selectedLetters.containsKey(groupIndex) &&
        _selectedLetters[groupIndex] != letter;

    return GestureDetector(
      onTap: () => _handleLetterSelect(letter, position),
      child: Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
          color: isSelected ? Colors.blue[100] : Colors.grey[100],
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            letter,
            style: TextStyle(
              fontSize: 24,
              color: isSelected ? Colors.blue : Colors.black87,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }
}
