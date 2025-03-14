import 'package:flutter/material.dart';
import '../features/calendar/presentation/widgets/calendar_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  DateTime selectedDate = DateTime.now();
  bool isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // 상단 프로필 아이콘 영역
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  CircleAvatar(child: Text('홈')),
                  CircleAvatar(child: Text('AI')),
                  CircleAvatar(child: Text('리포트')),
                  CircleAvatar(child: Text('설정')),
                ],
              ),
            ),

            // 월 선택 헤더
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        isExpanded = !isExpanded;
                      });
                    },
                    child: Row(
                      children: [
                        Text(
                          '${selectedDate.month}월',
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Icon(
                          isExpanded
                              ? Icons.keyboard_arrow_up
                              : Icons.keyboard_arrow_down,
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      setState(() {
                        selectedDate = DateTime.now();
                      });
                    },
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white, // primary is deprecated
                    ),
                    child: const Text('오늘'),
                  ),
                ],
              ),
            ),

            // 캘린더 위젯
            if (isExpanded)
              CalendarWidget(
                selectedDate: selectedDate,
                onDateSelected: (date) {
                  setState(() {
                    selectedDate = date;
                    isExpanded = false;
                  });
                },
              ),

            // 일정 목록
            Expanded(
              child: ListView.builder(
                itemCount: 5, // 실제 일정 개수로 대체
                itemBuilder: (context, index) {
                  return const EventListItem(
                    title: '[패캠] 프로젝트 3',
                    time: '17:30 - 21:00',
                    emoji: '😊',
                  );
                },
              ),
            ),

            // 회고하러가기 버튼
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: ElevatedButton.icon(
                onPressed: () {
                  // 회고 작성 페이지로 이동
                },
                icon: const Icon(Icons.star, color: Colors.yellow),
                label: const Text('회고하러가기'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black, // primary is deprecated
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// 일정 아이템 위젯
class EventListItem extends StatelessWidget {
  final String title;
  final String time;
  final String emoji;

  const EventListItem({
    super.key,
    required this.title,
    required this.time,
    required this.emoji,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(title),
      subtitle: Text(time),
      trailing: Text(emoji, style: const TextStyle(fontSize: 24)),
    );
  }
}
