import 'package:flutter/material.dart';

class CalendarWidget extends StatelessWidget {
  final DateTime selectedDate;
  final Function(DateTime) onDateSelected;

  const CalendarWidget({
    super.key,
    required this.selectedDate,
    required this.onDateSelected,
  });

  @override
  Widget build(BuildContext context) {
    // 임시 캘린더 UI
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 여기에 실제 캘린더 구현
          // 임시로 간단한 UI만 표시
          GridView.builder(
            shrinkWrap: true,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
            ),
            itemCount: 31, // 임시로 31일
            itemBuilder: (context, index) {
              return InkWell(
                onTap: () {
                  final selectedDay = DateTime(
                    selectedDate.year,
                    selectedDate.month,
                    index + 1,
                  );
                  onDateSelected(selectedDay);
                },
                child: Center(
                  child: Text(
                    '${index + 1}',
                    style: TextStyle(
                      color: selectedDate.day == (index + 1)
                          ? Colors.blue
                          : Colors.black,
                      fontWeight: selectedDate.day == (index + 1)
                          ? FontWeight.bold
                          : FontWeight.normal,
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
