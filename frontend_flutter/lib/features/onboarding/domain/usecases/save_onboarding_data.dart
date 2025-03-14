import '../repositories/onboarding_repository.dart';
import '../models/onboarding_data.dart';

class SaveOnboardingData {
  final OnboardingRepository repository;

  SaveOnboardingData(this.repository);

  Future<void> call(OnboardingData data) {
    return repository.saveUserData(data);
  }
}
