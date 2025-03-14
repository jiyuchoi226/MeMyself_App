import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:firebase_auth/firebase_auth.dart' hide UserMetadata;
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/auth_bloc.dart';
import '../bloc/auth_state.dart';
import '../bloc/auth_event.dart';
import '../../../calendar/presentation/bloc/calendar_bloc.dart';
import 'dart:async';
import 'package:dio/dio.dart';
import '../../domain/entities/user_metadata.dart' as app_metadata;
// ImageFilter를 위한 import 추가

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  int _logoTapCount = 0; // 로고 탭 횟수를 추적
  Timer? _tapResetTimer; // 탭 초기화를 위한 타이머
  bool _isLoading = false;
  String? _errorMessage;
  Timer? _loginTimeout;

  void _handleLogoTap() {
    setState(() {
      _logoTapCount++;
    });

    // 이전 타이머가 있다면 취소
    _tapResetTimer?.cancel();

    // 2초 후에 탭 카운트 리셋
    _tapResetTimer = Timer(const Duration(seconds: 2), () {
      setState(() {
        _logoTapCount = 0;
      });
    });

    // 5번 탭하면 개발자 모드로 진입
    if (_logoTapCount >= 5) {
      _tapResetTimer?.cancel();
      setState(() {
        _logoTapCount = 0;
      });
      Navigator.pushNamed(context, '/dev');
    }
  }

  @override
  void dispose() {
    _tapResetTimer?.cancel();
    _loginTimeout?.cancel();
    super.dispose();
  }

  void _handleGoogleSignIn() {
    setState(() {
      _isLoading = true;
    });

    // 로그인 요청
    context.read<AuthBloc>().add(LoginWithGoogle());

    // 타임아웃 설정 (10초 후에도 로그인이 완료되지 않으면 오류 표시)
    _loginTimeout = Timer(const Duration(seconds: 10), () {
      if (mounted && _isLoading) {
        setState(() {
          _isLoading = false;
          _errorMessage = '로그인 시간이 초과되었습니다. 다시 시도해주세요.';
        });
      }
    });
  }

  Future<void> _handleLoginSuccess(
      BuildContext context, app_metadata.UserMetadata metadata) async {
    try {
      // Firebase User 객체 가져오기
      final firebaseUser = FirebaseAuth.instance.currentUser;
      if (firebaseUser == null) {
        throw Exception('Firebase 사용자 정보를 찾을 수 없습니다');
      }

      // 로그인 성공 메시지 표시
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('로그인 성공')),
      );

      // 캘린더 동기화 시작 (Firebase User 객체 사용)
      await _syncCalendar(context, firebaseUser);

      // 홈 화면으로 이동
      Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      print('로그인 후 처리 오류: $e');
      // 오류가 발생해도 홈 화면으로 이동
      Navigator.pushReplacementNamed(context, '/home');
    }
  }

  Future<void> _syncCalendar(BuildContext context, User user) async {
    try {
      // 로딩 표시
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('캘린더 동기화 중...')),
      );

      // Google 로그인 인스턴스 생성 시 People API 요청 비활성화
      final GoogleSignIn googleSignIn = GoogleSignIn(
        scopes: [
          'email',
          'https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/calendar.events',
          'https://www.googleapis.com/auth/calendar.readonly',
        ],
        signInOption: SignInOption.standard, // 기본 로그인 옵션 사용
        hostedDomain: '', // 특정 도메인으로 제한하지 않음
        clientId: '', // 웹 클라이언트 ID (필요한 경우)
      );

      // 로그인 후 사용자 정보 가져오기
      final GoogleSignInAccount? googleUser = await googleSignIn.signIn();
      if (googleUser == null) {
        throw Exception('Google 계정 로그인이 필요합니다');
      }

      // 필요한 정보만 직접 가져오기
      final String displayName = googleUser.displayName ?? '사용자';
      final String email = googleUser.email;
      final String photoUrl = googleUser.photoUrl ?? '';

      // Google 인증 정보 가져오기
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Firebase ID 토큰 가져오기
      final idToken = await user.getIdToken();

      print('Google 계정 ID: ${googleUser.id}');
      print('액세스 토큰: ${googleAuth.accessToken?.substring(0, 10)}...');
      print('ID 토큰: ${googleAuth.idToken?.substring(0, 10)}...');

      // 캘린더 동기화 API 호출
      final dio = Dio();
      final response = await dio.post(
        'http://10.0.2.2:8000/sync-calendar',
        data: {
          'user_id': user.uid,
          'token': googleAuth.accessToken, // 서버에서 필요로 하는 token 필드 추가
          'google_account_id': googleUser.id,
          'access_token': googleAuth.accessToken,
          'email': googleUser.email,
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $idToken', // Firebase 인증용
          },
          validateStatus: (status) => true,
        ),
      );

      // 응답 로깅 추가
      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        // 동기화 성공 시 캘린더 블록에 이벤트 추가
        final calendarBloc = BlocProvider.of<CalendarBloc>(context);
        calendarBloc.add(CalendarFetchEvents());

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('캘린더 동기화 완료')),
        );
      } else {
        final errorMessage = response.data['detail'] ?? '알 수 없는 오류';
        throw Exception(
            '캘린더 동기화 실패: $errorMessage (상태 코드: ${response.statusCode})');
      }
    } catch (e) {
      print('캘린더 동기화 오류: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('캘린더 동기화 중 오류 발생: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        // 로딩 상태 처리
        setState(() {
          _isLoading = state is AuthLoading;
        });

        // 로그인 타임아웃 취소
        _loginTimeout?.cancel();

        if (state is AuthSuccess) {
          // 로그인 성공 시 홈 화면으로 이동
          if (state.metadata == null) {
            // 메타데이터가 없으면 온보딩으로 이동
            Navigator.pushReplacementNamed(context, '/onboarding');
          } else {
            // 메타데이터가 있으면 홈으로 이동
            Navigator.pushReplacementNamed(context, '/home');
          }
        } else if (state is AuthError) {
          // 오류 메시지 표시
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.message)),
          );
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFFCF4F4),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0),
            child: Column(
              children: [
                const SizedBox(height: 100), // 상단 여백 조정
                // 로고와 타이틀 섹션
                Column(
                  children: [
                    GestureDetector(
                      onTap: _handleLogoTap,
                      child: Container(
                        width: 80, // 원 크기
                        height: 80,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.black54, width: 2.5),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'MeMyself',
                      style: GoogleFonts.playfairDisplay(
                        fontSize: 36,
                        fontWeight: FontWeight.w500,
                        color: Colors.black87,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 48),
                // 설명 텍스트 섹션
                const Column(
                  children: [
                    Text(
                      '나보다 나를 더 잘 아는',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                        color: Colors.black54,
                        letterSpacing: -0.5,
                      ),
                    ),
                    SizedBox(height: 32),
                    Text(
                      '당신의 데이터로 더 나은 나를 발견하세요',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w400,
                        color: Colors.black54,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                // 구글 로그인 버튼
                Center(
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: _handleGoogleSignIn,
                      borderRadius: BorderRadius.circular(25),
                      child: Ink(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(25),
                          border: Border.all(
                            color: const Color(0xFF4285F4), // 구글 브랜드 파란색
                            width: 1,
                          ),
                        ),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 13,
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Image.network(
                                'https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png',
                                width: 22,
                                height: 22,
                              ),
                              const SizedBox(width: 12),
                              const Text(
                                'Sign in with Google',
                                style: TextStyle(
                                  color: Colors.black87,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                  letterSpacing: 0.2,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 48),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
