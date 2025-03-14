abstract class AuthEvent {
  const AuthEvent();
}

class SignInEvent extends AuthEvent {}

class SignOutEvent extends AuthEvent {}

class CheckAuthStatusEvent extends AuthEvent {}

class LoginRequested extends AuthEvent {
  final String email;
  final String password;

  LoginRequested({required this.email, required this.password});
}

class LoginWithGoogle extends AuthEvent {}

class LogoutRequested extends AuthEvent {}

class RefreshUserData extends AuthEvent {
  const RefreshUserData();
}
