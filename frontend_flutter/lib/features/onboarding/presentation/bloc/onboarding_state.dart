abstract class OnboardingState {}

class OnboardingInitial extends OnboardingState {}

class OnboardingSaving extends OnboardingState {}

class OnboardingSaveSuccess extends OnboardingState {}

class OnboardingSaveFailure extends OnboardingState {
  final String error;
  OnboardingSaveFailure(this.error);
}
