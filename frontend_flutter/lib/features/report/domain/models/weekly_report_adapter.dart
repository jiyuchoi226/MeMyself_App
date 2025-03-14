import 'package:hive/hive.dart';
import 'weekly_report.dart';

class WeeklyReportAdapter extends TypeAdapter<WeeklyReport> {
  @override
  final int typeId = 3;

  @override
  WeeklyReport read(BinaryReader reader) {
    return WeeklyReport(
      startDate: reader.read() as DateTime,
      endDate: reader.read() as DateTime,
      emotions: List<String>.from(reader.read() as List),
      emojis: List<String>.from(reader.read() as List),
      summary: reader.read() as String,
      lastUpdated: reader.read() as DateTime,
      eventIds: List<String>.from(reader.read() as List),
    );
  }

  @override
  void write(BinaryWriter writer, WeeklyReport obj) {
    writer.write(obj.startDate);
    writer.write(obj.endDate);
    writer.write(obj.emotions);
    writer.write(obj.emojis);
    writer.write(obj.summary);
    writer.write(obj.lastUpdated);
    writer.write(obj.eventIds);
  }
}
