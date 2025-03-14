import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../domain/entities/calendar_event.dart' as entities;
import '../bloc/calendar_bloc.dart';

class CalendarView extends StatelessWidget {
  final Map<DateTime, List<entities.CalendarEvent>> events;
  final DateTime selectedDay;
  final Function(DateTime, DateTime) onDaySelected;
  final VoidCallback? onTodayPressed;

  const CalendarView({
    super.key,
    required this.events,
    required this.selectedDay,
    required this.onDaySelected,
    this.onTodayPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: () {
                      final previousMonth = DateTime(
                        selectedDay.year,
                        selectedDay.month - 1,
                        1,
                      );
                      context
                          .read<CalendarBloc>()
                          .add(LoadMonthEvents(previousMonth));
                      onDaySelected(previousMonth, previousMonth);
                    },
                  ),
                  Text(
                    _formatYearMonth(selectedDay),
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: () {
                      final nextMonth = DateTime(
                        selectedDay.year,
                        selectedDay.month + 1,
                        1,
                      );
                      context
                          .read<CalendarBloc>()
                          .add(LoadMonthEvents(nextMonth));
                      onDaySelected(nextMonth, nextMonth);
                    },
                  ),
                ],
              ),
              ElevatedButton(
                onPressed: () {
                  onDaySelected(DateTime.now(), DateTime.now());
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(60, 32),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(50),
                  ),
                  elevation: 0,
                ),
                child: const Text(
                  '오늘',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ),
        TableCalendar<entities.CalendarEvent>(
          firstDay: DateTime(2023, 1, 1),
          lastDay: DateTime(2025, 12, 31),
          focusedDay: selectedDay,
          calendarFormat: CalendarFormat.month,
          selectedDayPredicate: (day) => isSameDay(selectedDay, day),
          eventLoader: (day) {
            final normalizedDay = DateTime(day.year, day.month, day.day);
            return events[normalizedDay] ?? [];
          },
          onDaySelected: (selected, focused) =>
              onDaySelected(selected, focused),
          calendarStyle: CalendarStyle(
            markersMaxCount: 4,
            markerSize: 4,
            markerDecoration: const BoxDecoration(
              color: Colors.blue,
              shape: BoxShape.circle,
            ),
            weekendTextStyle: const TextStyle(color: Colors.red),
            selectedDecoration: const BoxDecoration(
              color: Colors.black,
              shape: BoxShape.circle,
            ),
            todayDecoration: BoxDecoration(
              color: Colors.grey[300],
              shape: BoxShape.circle,
            ),
            cellMargin: const EdgeInsets.all(4),
            cellPadding: const EdgeInsets.all(4),
          ),
          headerVisible: false,
          locale: 'ko_KR',
          daysOfWeekHeight: 40,
          daysOfWeekStyle: const DaysOfWeekStyle(
            weekdayStyle: TextStyle(
              color: Colors.black,
              fontSize: 14,
            ),
            weekendStyle: TextStyle(
              color: Colors.red,
              fontSize: 14,
            ),
          ),
          onPageChanged: (focusedDay) {
            onDaySelected(focusedDay, focusedDay);
          },
          calendarBuilders: CalendarBuilders(
            markerBuilder: (context, date, events) {
              if (events.isEmpty) return null;

              return Positioned(
                bottom: 1,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '${events.length}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.blue[700],
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  String _formatYearMonth(DateTime date) {
    return '${date.year}년 ${date.month}월';
  }
}
