import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';

class CalendarView extends StatefulWidget {
  const CalendarView({super.key});

  @override
  State<CalendarView> createState() => _CalendarViewState();
}

class _CalendarViewState extends State<CalendarView> {
  CalendarFormat _calendarFormat = CalendarFormat.month;
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: TableCalendar(
        firstDay: DateTime(2023, 1, 1),
        lastDay: DateTime(2025, 12, 31),
        focusedDay: _focusedDay,
        calendarFormat: _calendarFormat,
        selectedDayPredicate: (day) {
          return isSameDay(_selectedDay, day);
        },
        onDaySelected: (selectedDay, focusedDay) {
          if (!isSameDay(_selectedDay, selectedDay)) {
            setState(() {
              _selectedDay = selectedDay;
              _focusedDay = focusedDay;
            });
          }
        },
        onFormatChanged: (format) {
          if (_calendarFormat != format) {
            setState(() {
              _calendarFormat = format;
            });
          }
        },
        headerStyle: const HeaderStyle(
          titleCentered: true,
          formatButtonVisible: false,
          leftChevronIcon: Icon(Icons.chevron_left, color: Colors.black54),
          rightChevronIcon: Icon(Icons.chevron_right, color: Colors.black54),
        ),
        calendarStyle: CalendarStyle(
          selectedDecoration: const BoxDecoration(
            color: Colors.black87,
            shape: BoxShape.circle,
          ),
          todayDecoration: BoxDecoration(
            color: Colors.grey[300],
            shape: BoxShape.circle,
          ),
          markersMaxCount: 3,
          markerDecoration: const BoxDecoration(
            color: Colors.blue,
            shape: BoxShape.circle,
          ),
          weekendTextStyle: const TextStyle(color: Colors.red),
          outsideDaysVisible: false,
        ),
        daysOfWeekStyle: const DaysOfWeekStyle(
          weekdayStyle: TextStyle(color: Colors.black87),
          weekendStyle: TextStyle(color: Colors.red),
        ),
        headerVisible: true,
        locale: 'ko_KR',
      ),
    );
  }
}
