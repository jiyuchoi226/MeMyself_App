import 'package:flutter/material.dart';
import '../../domain/entities/calendar_event.dart';
import '../../domain/entities/emotion.dart';
import '../../../../features/chat/presentation/pages/reflection_chat_page.dart';

class EventList extends StatefulWidget {
  final List<CalendarEvent> events;
  final Function(CalendarEvent) onEventTap;
  final bool isExpanded;
  final Function(bool) onExpandChanged;
  final bool allEventsMarked;
  final VoidCallback? onReflectPressed;

  const EventList({
    super.key,
    required this.events,
    required this.onEventTap,
    required this.isExpanded,
    required this.onExpandChanged,
    required this.allEventsMarked,
    this.onReflectPressed,
  });

  @override
  State<EventList> createState() => _EventListState();
}

class _EventListState extends State<EventList> {
  late ScrollController _scrollController;
  bool _isDragging = false;
  double _dragStartPosition = 0;
  static const double _defaultHeight = 0.3; // 기본 높이
  static const double _expandedHeight = 0.7; // 확장 높이

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onVerticalDragStart: (details) {
        _isDragging = true;
        _dragStartPosition = details.globalPosition.dy;
      },
      onVerticalDragUpdate: (details) {
        if (!_isDragging) return;

        final delta = details.globalPosition.dy - _dragStartPosition;
        if (delta < -50 && !widget.isExpanded) {
          widget.onExpandChanged(true);
          _isDragging = false;
        } else if (delta > 50 && widget.isExpanded) {
          widget.onExpandChanged(false);
          _isDragging = false;
        }
      },
      onVerticalDragEnd: (_) {
        _isDragging = false;
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        height: MediaQuery.of(context).size.height *
            (widget.isExpanded ? _expandedHeight : _defaultHeight),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: Column(
          children: [
            // 스와이프 인디케이터
            Column(
              children: [
                Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                if (!widget.isExpanded && widget.events.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.keyboard_arrow_up, color: Colors.grey[400]),
                        Text(
                          '위로 스와이프하여 더 보기',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            // 이벤트 리스트
            Expanded(
              child: widget.events.isEmpty
                  ? const Center(
                      child: Text(
                        '오늘은 일정이 없습니다.',
                        style: TextStyle(
                          color: Colors.grey,
                          fontSize: 16,
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      // 최소화 상태일 때는 스크롤 비활성화
                      physics: widget.isExpanded
                          ? const AlwaysScrollableScrollPhysics()
                          : const NeverScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      itemCount: widget.events.length,
                      itemBuilder: (context, index) {
                        final event = widget.events[index];
                        return _EventItem(
                          event: event,
                          onTap: () => widget.onEventTap(event),
                        );
                      },
                    ),
            ),
            // 회고하기 버튼
            if (widget.events.isNotEmpty && widget.allEventsMarked)
              Padding(
                padding: const EdgeInsets.all(16),
                child: ElevatedButton(
                  onPressed: () {
                    final firstEvent = widget.events.first;
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
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 48),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(24),
                    ),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.star, color: Colors.yellow),
                      SizedBox(width: 8),
                      Text(
                        '회고하러가기',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}

class _EventItem extends StatelessWidget {
  final CalendarEvent event;
  final VoidCallback onTap;

  const _EventItem({
    required this.event,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: Colors.grey[50],
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    event.title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${_formatTime(event.startTime)} - ${_formatTime(event.endTime)}',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: event.emotion != null
                    ? Colors.transparent
                    : Colors.grey[200],
                border: event.emotion == null
                    ? Border.all(color: Colors.grey[400]!, width: 1)
                    : null,
              ),
              child: event.emotion != null
                  ? Center(
                      child: Text(
                        event.emotionObj?.emoji ?? '😊',
                        style: const TextStyle(fontSize: 24),
                      ),
                    )
                  : const Icon(
                      Icons.add,
                      color: Colors.grey,
                      size: 20,
                    ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}
