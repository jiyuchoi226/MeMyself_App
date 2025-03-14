import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'core/routes/app_router.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'features/calendar/presentation/bloc/calendar_bloc.dart';
import 'injection.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() async {
  try {
    WidgetsFlutterBinding.ensureInitialized();

    // 1. Hive 초기화
    await Hive.initFlutter();

    // 2. Firebase 초기화
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );

    // 3. 의존성 주입 설정
    configureDependencies();

    // 4. 모든 비동기 의존성이 초기화될 때까지 대기
    await getIt.allReady().timeout(
      const Duration(seconds: 10),
      onTimeout: () {
        print('Dependency initialization timed out');
        throw Exception('Dependency initialization timed out');
      },
    );

    print('All dependencies initialized successfully');

    runApp(const MyApp());
  } catch (e, stackTrace) {
    print('Initialization error: $e');
    print('Stack trace: $stackTrace');
    rethrow;
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (context) => getIt<CalendarBloc>(),
        ),
        BlocProvider(
          create: (context) => getIt<AuthBloc>(),
        ),
      ],
      child: MaterialApp(
        title: 'MeMyself App',
        theme: ThemeData(
          primarySwatch: Colors.deepPurple,
          useMaterial3: true,
        ),
        initialRoute: '/',
        onGenerateRoute: AppRouter.generateRoute,
        debugShowCheckedModeBanner: false,
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('ko', 'KR'),
        ],
      ),
    );
  }
}
