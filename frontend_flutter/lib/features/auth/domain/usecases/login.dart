import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/user.dart';
import '../repositories/auth_repository.dart';
import 'package:google_sign_in/google_sign_in.dart';

class LoginParams {
  final String email;
  final String password;
  final GoogleSignInAccount? googleUser;

  LoginParams({
    required this.email,
    required this.password,
    this.googleUser,
  });
}

class Login implements UseCase<User, LoginParams> {
  final AuthRepository repository;

  Login(this.repository);

  @override
  Future<Either<Failure, User>> call(LoginParams params) async {
    return await repository.login(params.email, params.password);
  }
}
