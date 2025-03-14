import 'package:cloud_firestore/cloud_firestore.dart';
import '../../domain/entities/user_metadata.dart';

class FirebaseUserRepository {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<UserMetadata?> getUserMetadata(String uid) async {
    try {
      final doc = await _firestore.collection('users').doc(uid).get();

      // 문서가 존재하지 않는 경우 null 반환
      if (!doc.exists) {
        print('User metadata not found for uid: $uid');
        return null;
      }

      final data = doc.data();
      if (data != null) {
        return UserMetadata(
          uid: uid,
          birthDate: (data['birthDate'] as Timestamp).toDate(),
          mbti: data['mbti'] ?? 'INFP',
          gender: data['gender'] ?? '미정',
          createdAt: (data['createdAt'] as Timestamp).toDate(),
          updatedAt: (data['updatedAt'] as Timestamp).toDate(),
        );
      }
      return null;
    } catch (e) {
      print('Error getting user metadata: $e');
      return null; // 에러 발생 시 null 반환
    }
  }

  Future<void> saveUserMetadata(UserMetadata metadata) async {
    try {
      await _firestore.collection('users').doc(metadata.uid).set(
            metadata.toJson(),
            SetOptions(merge: true),
          );
    } catch (e) {
      print('Error saving user metadata: $e');
      throw Exception('Failed to save user metadata');
    }
  }
}
