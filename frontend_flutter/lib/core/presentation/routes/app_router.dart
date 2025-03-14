import 'package:flutter/material.dart';
import '../../../features/onboarding/presentation/pages/onboarding_page.dart';
import '../../../features/auth/presentation/bloc/auth_state.dart';
import '../../../features/home/presentation/pages/home_page.dart';
import '../../../features/chat/presentation/pages/chat_page.dart';
import '../../../features/report/presentation/pages/report_page.dart';
import '../../../features/settings/presentation/pages/settings_page.dart';

class AppRouter {
  Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/onboarding':
        final args = settings.arguments as Map<String, dynamic>?;
        return MaterialPageRoute(
          builder: (context) => OnboardingPage(
            editField: args?['editField'] as String?,
            currentState: args?['currentData'] as AuthState?,
          ),
        );

      case '/home':
        return MaterialPageRoute(builder: (context) => const HomePage());

      case '/chat':
        return MaterialPageRoute(builder: (context) => const ChatPage());

      case '/report':
        return MaterialPageRoute(builder: (context) => const ReportPage());

      case '/settings':
        return MaterialPageRoute(builder: (context) => const SettingsPage());

      default:
        return MaterialPageRoute(
          builder: (context) => const Scaffold(
            body: Center(child: Text('404 - Page Not Found')),
          ),
        );
    }
  }
}
