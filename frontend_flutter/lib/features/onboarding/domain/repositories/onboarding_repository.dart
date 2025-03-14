import '../models/onboarding_data.dart';

abstract class OnboardingRepository {
  Future<void> saveUserData(OnboardingData data);
  Future<OnboardingData?> getUserData(String uid);
}
