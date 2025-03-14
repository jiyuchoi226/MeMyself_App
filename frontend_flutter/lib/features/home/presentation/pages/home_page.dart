import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/presentation/widgets/gnb.dart';
import '../../../calendar/presentation/bloc/calendar_bloc.dart';
import '../../../calendar/presentation/widgets/calendar_view.dart';
import '../../../calendar/presentation/widgets/event_list.dart';
import '../../../calendar/presentation/widgets/emotion_selector_sheet.dart';
import '../../../calendar/domain/entities/calendar_event.dart' as entities;
import '../../../calendar/domain/entities/emotion.dart';
// isSameDay 함수를 위한 import
import '../../../chat/presentation/pages/reflection_chat_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedNavIndex = 0;
  bool _isEventListExpanded = false;

  @override
  void initState() {
    super.initState();
    // 초기 이벤트 로드
    final now = DateTime.now();
    context.read<CalendarBloc>().add(FetchCalendarEvents(now));
  }

  void _handleEventListExpand(bool expanded) {
    setState(() {
      _isEventListExpanded = expanded;
    });
  }

  void _handleTodayButtonPress() {
    final now = DateTime.now();
    context.read<CalendarBloc>().add(FetchCalendarEvents(now));
  }

  void _handleDaySelected(DateTime selected, DateTime focused) {
    print('Selected date: $selected');
    context.read<CalendarBloc>().add(FetchCalendarEvents(selected));
  }

  bool _areAllEventsMarked(List<entities.CalendarEvent> events) {
    if (events.isEmpty) return false;

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);

    final todayEvents = events.where((event) {
      final eventDate = DateTime(
        event.startTime.year,
        event.startTime.month,
        event.startTime.day,
      );
      return eventDate.isAtSameMomentAs(today);
    }).toList();

    if (todayEvents.isEmpty) return false;

    return todayEvents.every((event) => event.emotion != null);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAFAFA),
      body: SafeArea(
        child: BlocBuilder<CalendarBloc, CalendarState>(
          builder: (context, state) {
            final selectedDate = state.selectedDay;
            final events = state.events[selectedDate] ?? [];

            print('Selected date: $selectedDate');
            print('Events for selected date: ${events.length}');
            print('All events: ${state.events}');

            final allEventsMarked =
                events.every((event) => event.emotion != null);

            return Column(
              children: [
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border(
                      bottom: BorderSide(
                        color: Colors.grey[200]!,
                        width: 1,
                      ),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.03),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: GNB(
                    selectedIndex: _selectedNavIndex,
                    onItemSelected: (index) {
                      setState(() {
                        _selectedNavIndex = index;
                      });
                    },
                  ),
                ),
                Expanded(
                  child: Stack(
                    children: [
                      CalendarView(
                        events: state.events,
                        selectedDay: selectedDate,
                        onDaySelected: _handleDaySelected,
                        onTodayPressed: _handleTodayButtonPress,
                      ),
                      if (state.isLoading)
                        const Center(
                          child: CircularProgressIndicator(),
                        ),
                      Positioned(
                        left: 0,
                        right: 0,
                        bottom: 0,
                        child: EventList(
                          events: events,
                          onEventTap: (event) {
                            showModalBottomSheet(
                              context: context,
                              builder: (context) => EmotionSelectorSheet(
                                event: event,
                                onEmotionSelected: (emotion) {
                                  _handleEmotionSelect(event, emotion);
                                },
                              ),
                            );
                          },
                          isExpanded: _isEventListExpanded,
                          onExpandChanged: _handleEventListExpand,
                          allEventsMarked: allEventsMarked,
                          onReflectPressed: allEventsMarked
                              ? () {
                                  final firstEvent = events.first;
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => ReflectionChatPage(
                                        eventTitle: firstEvent.title,
                                        emotion: firstEvent.emotion ?? '미정',
                                        eventDate: firstEvent.startTime,
                                        eventId: firstEvent.id,
                                      ),
                                    ),
                                  );
                                }
                              : null,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  void _handleEmotionSelect(entities.CalendarEvent event, Emotion emotion) {
    // CalendarBloc에 이벤트 전달
    context.read<CalendarBloc>().add(UpdateEventEmotion(event.id, emotion));

    // 선택 후 필요한 UI 업데이트 (예: 스낵바 표시)
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('${event.title}에 ${emotion.emoji} 감정이 기록되었습니다.'),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}

class _MenuButton extends StatelessWidget {
  final IconData icon;
  final String label;

  const _MenuButton({
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white,
          ),
          child: Icon(icon),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.black54,
          ),
        ),
      ],
    );
  }
}
