import 'package:firebase_auth/firebase_auth.dart';
import '../../../auth/data/repositories/firebase_user_repository.dart';
import '../../../auth/domain/entities/user_metadata.dart' as app_metadata;
import '../../domain/models/onboarding_data.dart';
import '../../domain/repositories/onboarding_repository.dart';

class OnboardingRepositoryImpl implements OnboardingRepository {
  final FirebaseUserRepository userRepository;

  OnboardingRepositoryImpl(this.userRepository);

  @override
  Future<void> saveUserData(OnboardingData data) async {
    final metadata = _mapToUserMetadata(data);
    await userRepository.saveUserMetadata(metadata);
  }

  @override
  Future<OnboardingData?> getUserData(String uid) async {
    final metadata = await userRepository.getUserMetadata(uid);
    return metadata != null ? _mapToOnboardingData(metadata) : null;
  }

  app_metadata.UserMetadata _mapToUserMetadata(OnboardingData data) {
    return app_metadata.UserMetadata(
      uid: FirebaseAuth.instance.currentUser!.uid,
      birthDate: data.birthDate ?? DateTime.now(),
      mbti: data.mbti ?? '',
      gender: data.gender ?? '',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  OnboardingData _mapToOnboardingData(app_metadata.UserMetadata metadata) {
    return OnboardingData(
      birthDate: metadata.birthDate,
      mbti: metadata.mbti,
      gender: metadata.gender,
    );
  }
}
