import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import '../../domain/entities/user_metadata.dart';

abstract class AuthState {}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class AuthSuccess extends AuthState {
  final firebase_auth.User user;
  final UserMetadata? metadata;

  AuthSuccess({
    required this.user,
    this.metadata,
  });
}

class AuthError extends AuthState {
  final String message;
  AuthError({required this.message});
}

class UnauthenticatedState extends AuthState {}
