import 'package:cloud_firestore/cloud_firestore.dart';

class UserMetadata {
  final String uid;
  final DateTime birthDate;
  final String mbti;
  final String gender;
  final DateTime createdAt;
  final DateTime updatedAt;

  UserMetadata({
    required this.uid,
    required this.birthDate,
    required this.mbti,
    required this.gender,
    required this.createdAt,
    required this.updatedAt,
  });

  factory UserMetadata.fromJson(Map<String, dynamic> json) {
    return UserMetadata(
      uid: json['uid'],
      birthDate: (json['birthDate'] as Timestamp).toDate(),
      mbti: json['mbti'],
      gender: json['gender'],
      createdAt: (json['createdAt'] as Timestamp).toDate(),
      updatedAt: (json['updatedAt'] as Timestamp).toDate(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'uid': uid,
      'birthDate': Timestamp.fromDate(birthDate),
      'mbti': mbti,
      'gender': gender,
      'createdAt': Timestamp.fromDate(createdAt),
      'updatedAt': Timestamp.fromDate(updatedAt),
    };
  }
}
