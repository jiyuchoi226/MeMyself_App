import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/save_onboarding_data.dart';
import 'onboarding_event.dart';
import 'onboarding_state.dart';

class OnboardingBloc extends Bloc<OnboardingEvent, OnboardingState> {
  final SaveOnboardingData saveOnboardingData;

  OnboardingBloc({required this.saveOnboardingData})
      : super(OnboardingInitial()) {
    on<SaveOnboardingDataEvent>(_onSaveData);
  }

  Future<void> _onSaveData(
    SaveOnboardingDataEvent event,
    Emitter<OnboardingState> emit,
  ) async {
    emit(OnboardingSaving());
    try {
      await saveOnboardingData(event.data);
      emit(OnboardingSaveSuccess());
    } catch (e) {
      emit(OnboardingSaveFailure(e.toString()));
    }
  }
}
