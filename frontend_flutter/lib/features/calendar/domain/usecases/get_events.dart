import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../entities/calendar_event.dart';
import '../repositories/calendar_repository.dart';

class GetEvents {
  final CalendarRepository repository;

  GetEvents(this.repository);

  Future<Either<Failure, List<CalendarEvent>>> call(DateTime date) async {
    try {
      // 하루 전체 범위 설정
      final startOfDay = DateTime(date.year, date.month, date.day);
      final endOfDay = startOfDay.add(const Duration(days: 1));

      return await repository.getEventsForRange(startOfDay, endOfDay);
    } catch (e) {
      print('GetEvents error: $e');
      return Left(ServerFailure());
    }
  }

  Future<Either<Failure, List<CalendarEvent>>> getMonthEvents(
      DateTime month) async {
    try {
      final startOfMonth = DateTime(month.year, month.month, 1);
      final endOfMonth = DateTime(month.year, month.month + 1, 0);

      return await repository.getEventsForRange(startOfMonth, endOfMonth);
    } catch (e) {
      print('GetMonthEvents error: $e');
      return Left(ServerFailure());
    }
  }
}
