import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../repositories/calendar_repository.dart';
import '../entities/emotion.dart';

class UpdateEventEmotion implements UseCase<void, UpdateEventEmotionParams> {
  final CalendarRepository repository;

  UpdateEventEmotion(this.repository);

  @override
  Future<Either<Failure, void>> call(UpdateEventEmotionParams params) async {
    return await repository.updateEventEmotion(params.eventId, params.emotion);
  }
}

class UpdateEventEmotionParams {
  final String eventId;
  final Emotion emotion;

  UpdateEventEmotionParams({
    required this.eventId,
    required this.emotion,
  });
}
