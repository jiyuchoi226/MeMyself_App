import 'package:dartz/dartz.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:google_sign_in/google_sign_in.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  final firebase_auth.FirebaseAuth _firebaseAuth;
  final GoogleSignIn _googleSignIn;

  AuthRepositoryImpl({
    firebase_auth.FirebaseAuth? firebaseAuth,
    GoogleSignIn? googleSignIn,
  })  : _firebaseAuth = firebaseAuth ?? firebase_auth.FirebaseAuth.instance,
        _googleSignIn = googleSignIn ?? GoogleSignIn();

  @override
  Future<Either<Failure, User>> login(String email, String password) async {
    try {
      // 이미 로그인된 사용자가 있는지 확인
      final currentUser = _firebaseAuth.currentUser;
      if (currentUser != null) {
        return Right(User(
          id: currentUser.uid,
          email: currentUser.email ?? '',
          name: currentUser.displayName ?? '',
        ));
      }

      // 로그인 시도
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return Left(ServerFailure());

      final googleAuth = await googleUser.authentication;
      final credential = firebase_auth.GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential =
          await _firebaseAuth.signInWithCredential(credential);
      final user = userCredential.user;

      if (user == null) return Left(ServerFailure());

      return Right(User(
        id: user.uid,
        email: user.email ?? '',
        name: user.displayName ?? '',
      ));
    } catch (e) {
      print('로그인 오류: $e');
      return Left(ServerFailure());
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      await Future.wait([
        _firebaseAuth.signOut(),
        _googleSignIn.signOut(),
      ]);
      return const Right(null);
    } catch (e) {
      return Left(ServerFailure());
    }
  }
}
