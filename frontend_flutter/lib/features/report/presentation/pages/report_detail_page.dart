import 'package:flutter/material.dart';
import '../../domain/models/weekly_report.dart';

class ReportDetailPage extends StatelessWidget {
  final WeeklyReport report;

  const ReportDetailPage({super.key, required this.report});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text('${report.startDate.month}주차 리포트'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            _buildEmotionAnalysis(),
            _buildDetailedStats(),
            _buildWeeklyInsights(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      color: Colors.blue.shade50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '지난주 돌아보기',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.blue.shade700,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            report.summary,
            style: const TextStyle(
              fontSize: 16,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmotionAnalysis() {
    final emotionCount = <String, int>{};
    for (var emotion in report.emotions) {
      emotionCount[emotion] = (emotionCount[emotion] ?? 0) + 1;
    }

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '감정 분석',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          ...emotionCount.entries.map((entry) {
            final percentage =
                (entry.value / report.emotions.length * 100).round();
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${entry.key} ($percentage%)',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: entry.value / report.emotions.length,
                    backgroundColor: Colors.grey.shade200,
                    valueColor: AlwaysStoppedAnimation(Colors.blue.shade300),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildDetailedStats() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '상세 통계',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          _buildStatItem('총 기록된 일정', '${report.eventIds.length}개'),
          _buildStatItem('가장 많은 감정', _getMostFrequentEmotion()),
          _buildStatItem('감정 기록률',
              '${(report.emotions.length / report.eventIds.length * 100).round()}%'),
        ],
      ),
    );
  }

  Widget _buildWeeklyInsights() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '주간 인사이트',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          _buildInsightCard(
            '이번 주는 전반적으로 긍정적인 감정이 많았어요. 특히 운동과 독서 활동에서 높은 만족감을 보였습니다.',
            Icons.trending_up,
          ),
          const SizedBox(height: 12),
          _buildInsightCard(
            '스트레스 관리를 위해 충분한 휴식을 취하는 것이 도움이 될 것 같아요.',
            Icons.psychology,
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 14),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInsightCard(String text, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.blue.shade700),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getMostFrequentEmotion() {
    final emotionCount = <String, int>{};
    for (var emotion in report.emotions) {
      emotionCount[emotion] = (emotionCount[emotion] ?? 0) + 1;
    }
    final mostFrequent =
        emotionCount.entries.reduce((a, b) => a.value > b.value ? a : b);
    return mostFrequent.key;
  }

  int _getWeekOfMonth(DateTime date) {
    final firstDayOfMonth = DateTime(date.year, date.month, 1);
    final firstWeekday = firstDayOfMonth.weekday;
    final offsetDate = date.day + firstWeekday - 1;
    return ((offsetDate - 1) ~/ 7) + 1;
  }
}
