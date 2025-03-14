import 'package:flutter/material.dart';

class GNB extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onItemSelected;
  final bool isTop; // 상단/하단 구분을 위한 플래그 추가

  const GNB({
    super.key,
    required this.selectedIndex,
    required this.onItemSelected,
    this.isTop = false, // 기본값은 하단
  });

  void _handleNavigation(BuildContext context, int index) {
    onItemSelected(index);
    switch (index) {
      case 0:
        Navigator.pushReplacementNamed(context, '/home');
        break;
      case 1:
        Navigator.pushReplacementNamed(context, '/reflection_chat');
        break;
      case 2:
        Navigator.pushReplacementNamed(context, '/report');
        break;
      case 3:
        Navigator.pushReplacementNamed(context, '/settings');
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isTop) {
      // 상단 GNB UI
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildNavItem(context, 0, Icons.home_outlined, '홈'),
            _buildNavItem(context, 1, Icons.psychology_outlined, 'AI'),
            _buildNavItem(context, 2, Icons.article_outlined, '리포트'),
            _buildNavItem(context, 3, Icons.settings_outlined, '설정'),
          ],
        ),
      );
    } else {
      // 하단 BottomNavigationBar UI
      return BottomNavigationBar(
        currentIndex: selectedIndex,
        onTap: (index) => _handleNavigation(context, index),
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: '홈',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_outlined),
            activeIcon: Icon(Icons.chat),
            label: 'AI',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.bar_chart_outlined),
            activeIcon: Icon(Icons.bar_chart),
            label: '리포트',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings_outlined),
            activeIcon: Icon(Icons.settings),
            label: '설정',
          ),
        ],
        selectedItemColor: Colors.deepPurple,
        unselectedItemColor: Colors.grey,
      );
    }
  }

  Widget _buildNavItem(
      BuildContext context, int index, IconData icon, String label) {
    final isSelected = selectedIndex == index;
    return InkWell(
      onTap: () => _handleNavigation(context, index),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 8,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.black : Colors.grey,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w500 : FontWeight.normal,
                color: isSelected ? Colors.black : Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
