import 'package:flutter/material.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/home/presentation/pages/home_page.dart';
import '../../features/settings/presentation/pages/settings_page.dart';
import '../../features/chat/presentation/pages/chat_page.dart';
import '../../features/report/presentation/pages/report_page.dart';
import '../../features/onboarding/presentation/pages/onboarding_page.dart';
import '../../features/chat/presentation/pages/reflection_chat_page.dart';
import '../../features/dev/presentation/pages/dev_test_page.dart';

class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/':
        return MaterialPageRoute(builder: (_) => const LoginPage());
      case '/onboarding':
        return MaterialPageRoute(builder: (_) => const OnboardingPage());
      case '/home':
        return MaterialPageRoute(builder: (_) => const HomePage());
      case '/chat':
        return MaterialPageRoute(builder: (_) => const ChatPage());
      case '/reflection_chat':
        return MaterialPageRoute(
          builder: (_) => ReflectionChatPage(
            eventTitle: '오늘의 회고',
            emotion: '기쁨',
            eventDate: DateTime.now(),
            eventId: 'default_event_${DateTime.now().millisecondsSinceEpoch}',
          ),
        );
      case '/report':
        return MaterialPageRoute(builder: (_) => const ReportPage());
      case '/settings':
        return MaterialPageRoute(builder: (_) => const SettingsPage());
      case '/dev':
        return MaterialPageRoute(builder: (_) => const DevTestPage());
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            appBar: AppBar(
              title: const Text('오류'),
            ),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 48,
                    color: Colors.red,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '페이지를 찾을 수 없습니다: ${settings.name}',
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => Navigator.pushReplacementNamed(_, '/home'),
                    child: const Text('홈으로 돌아가기'),
                  ),
                ],
              ),
            ),
          ),
        );
    }
  }
}
