class OnboardingData {
  final DateTime? birthDate;
  final String? mbti;
  final String? gender;

  OnboardingData({
    this.birthDate,
    this.mbti,
    this.gender,
  });

  OnboardingData copyWith({
    DateTime? birthDate,
    String? mbti,
    String? gender,
  }) {
    return OnboardingData(
      birthDate: birthDate ?? this.birthDate,
      mbti: mbti ?? this.mbti,
      gender: gender ?? this.gender,
    );
  }
}
