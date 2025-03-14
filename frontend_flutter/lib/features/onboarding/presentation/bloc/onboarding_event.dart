import '../../domain/models/onboarding_data.dart';

abstract class OnboardingEvent {}

class SaveOnboardingDataEvent extends OnboardingEvent {
  final OnboardingData data;
  SaveOnboardingDataEvent(this.data);
}
