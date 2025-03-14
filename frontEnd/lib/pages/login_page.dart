import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../services/api_service.dart';
import 'calendar_page.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'https://www.googleapis.com/auth/calendar.readonly',
      'https://www.googleapis.com/auth/userinfo.profile',
      'https://www.googleapis.com/auth/userinfo.email'
    ],
  );
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  Future<void> _handleSignIn() async {
    setState(() => _isLoading = true);

    try {
      final GoogleSignInAccount? account = await _googleSignIn.signIn();
      if (account != null) {
        print('로그인 시도: ${account.email}');
        
        final GoogleSignInAuthentication auth = await account.authentication;
        final token = auth.accessToken;
        final userId = account.email;

        if (token != null) {
          try {
            // 페이지 전환을 먼저 수행
            if (mounted) {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => const CalendarPage(),
                ),
              );
            }

            // 백그라운드에서 API 호출 수행
            print('활성 상태 업데이트 시도...');
            await _apiService.updateActiveStatus(token, userId, true);
            print('활성 상태 업데이트 성공');

            print('캘린더 동기화 시도...');
            await _apiService.syncCalendar(token, userId);
            print('캘린더 동기화 성공');

            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('로그인 성공!')),
              );
            }
          } catch (e) {
            print('백엔드 통신 실패: $e');
            // 에러가 발생해도 페이지 전환은 유지
          }
        }
      }
    } catch (e) {
      print('로그인 실패: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('로그인 실패: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'DODAY',
              style: TextStyle(
                fontSize: 40,
                fontWeight: FontWeight.bold,
                color: Colors.blue,
              ),
            ),
            const SizedBox(height: 30),
            if (_isLoading)
              const CircularProgressIndicator()
            else
              ElevatedButton(
                onPressed: _handleSignIn,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
                child: const Text(
                  'Google 로그인',
                  style: TextStyle(fontSize: 18),
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    super.dispose();
  }
}