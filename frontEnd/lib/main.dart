import 'package:flutter/material.dart';
import 'pages/login_page.dart';
import 'utils/calendar_cache.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await CalendarCache.initialize();
  await dotenv.load(fileName: ".env");
  // HTTP 인증서 검증 무시 (개발 환경용)
  HttpOverrides.global = _MyHttpOverrides();
  runApp(const MyApp());
}

// 개발 환경에서 인증서 검증 무시
class _MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback = (_, __, ___) => true;
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Doday',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: OpenUpwardsPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
        drawerTheme: DrawerThemeData(
          scrimColor: Colors.black.withOpacity(0.2),
        ),
      ),
      home: const LoginPage(),
    );
  }
}
