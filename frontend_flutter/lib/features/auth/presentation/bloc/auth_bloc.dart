import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/login.dart';
import 'auth_event.dart';
import 'auth_state.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../../calendar/presentation/bloc/calendar_bloc.dart';
import '../../../calendar/domain/entities/load_priority.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import '../../data/repositories/firebase_user_repository.dart';
import '../../domain/entities/user_metadata.dart';
import 'package:get_it/get_it.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final Login login;
  final GoogleSignIn _googleSignIn;
  final CalendarBloc _calendarBloc;
  final firebase_auth.FirebaseAuth _auth = firebase_auth.FirebaseAuth.instance;
  final FirebaseUserRepository _userRepository;

  AuthBloc(
    this.login,
    this._googleSignIn,
    this._calendarBloc,
    this._userRepository,
  ) : super(AuthInitial()) {
    on<LoginRequested>((event, emit) async {
      emit(AuthLoading());
      try {
        final firebaseUser = _auth.currentUser;
        if (firebaseUser != null) {
          final metadata =
              await _userRepository.getUserMetadata(firebaseUser.uid);
          emit(AuthSuccess(user: firebaseUser, metadata: metadata));
        } else {
          emit(AuthError(message: 'Firebase user not found'));
        }
      } catch (e) {
        emit(AuthError(message: e.toString()));
      }
    });
    on<LoginWithGoogle>(_onLoginWithGoogle);
    on<SignOutEvent>((event, emit) async {
      try {
        await _auth.signOut();
        await _googleSignIn.signOut();
        emit(UnauthenticatedState());
      } catch (e) {
        emit(AuthError(message: e.toString()));
      }
    });
    on<RefreshUserData>((event, emit) async {
      try {
        final firebaseUser = _auth.currentUser;
        if (firebaseUser != null) {
          emit(AuthLoading());

          final metadata =
              await _userRepository.getUserMetadata(firebaseUser.uid);

          emit(AuthSuccess(user: firebaseUser, metadata: metadata));

          _startCalendarDataLoading();
        }
      } catch (e) {
        print('Error refreshing user data: $e');
        emit(AuthError(message: e.toString()));
      }
    });
  }

  Future<void> _onLoginWithGoogle(
    LoginWithGoogle event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      // 1. Google 로그인 시도
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        emit(AuthError(message: '로그인이 취소되었습니다.'));
        return;
      }

      // 2. Firebase 인증
      final googleAuth = await googleUser.authentication;
      final credential = firebase_auth.GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Firebase 인증
      final userCredential = await _auth.signInWithCredential(credential);
      final firebaseUser = userCredential.user;

      if (firebaseUser == null) {
        emit(AuthError(message: '인증에 실패했습니다.'));
        return;
      }

      // 3. 사용자 메타데이터 가져오기
      final metadata = await _userRepository.getUserMetadata(firebaseUser.uid);

      // 4. 캘린더 데이터 로드 시작 (백그라운드에서)
      Future.microtask(() => _startCalendarDataLoading());

      // 5. 성공 상태 전환
      emit(AuthSuccess(user: firebaseUser, metadata: metadata));

      // 캘린더 동기화 호출 - 올바른 이벤트 사용
      _calendarBloc.add(LoadCalendarEvents(DateTime.now()));
    } catch (e) {
      print('로그인 오류: $e');
      emit(AuthError(message: '로그인 중 오류가 발생했습니다: $e'));
    }
  }

  void _startCalendarDataLoading() {
    // 현재 달만 우선 로드하고 나머지는 지연 로드
    final now = DateTime.now();
    _calendarBloc.add(LoadMonthEvents(now, priority: LoadPriority.high));

    // 이전 달과 다음 달은 지연 로드 (시간 간격 추가)
    Future.delayed(const Duration(milliseconds: 500), () {
      final previousMonth = DateTime(now.year, now.month - 1, 1);
      _calendarBloc
          .add(LoadMonthEvents(previousMonth, priority: LoadPriority.low));
    });

    Future.delayed(const Duration(milliseconds: 1000), () {
      final nextMonth = DateTime(now.year, now.month + 1, 1);
      _calendarBloc.add(LoadMonthEvents(nextMonth, priority: LoadPriority.low));
    });

    // 더 이전 달은 더 낮은 우선순위로 로드
    Future.delayed(const Duration(milliseconds: 2000), () {
      for (int i = 2; i <= 3; i++) {
        final olderMonth = DateTime(now.year, now.month - i, 1);
        _calendarBloc
            .add(LoadMonthEvents(olderMonth, priority: LoadPriority.low));
      }
    });
  }
}
