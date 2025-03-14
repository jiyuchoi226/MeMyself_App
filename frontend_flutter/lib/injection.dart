import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:frontend_flutter/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:frontend_flutter/features/auth/domain/repositories/auth_repository.dart';
import 'package:frontend_flutter/features/auth/domain/usecases/login.dart';
import 'package:frontend_flutter/features/auth/presentation/bloc/auth_bloc.dart';
import 'features/calendar/data/datasources/google_calendar_datasource.dart';
import 'features/calendar/data/repositories/calendar_repository_impl.dart';
import 'features/calendar/domain/repositories/calendar_repository.dart';
import 'features/calendar/domain/usecases/get_events.dart';
import 'features/calendar/presentation/bloc/calendar_bloc.dart';
import 'features/calendar/data/datasources/calendar_cache_manager.dart';
import 'features/auth/data/repositories/firebase_user_repository.dart';
import 'features/onboarding/domain/repositories/onboarding_repository.dart';
import 'features/onboarding/data/repositories/onboarding_repository_impl.dart';
import 'features/onboarding/domain/usecases/save_onboarding_data.dart';
import 'features/onboarding/presentation/bloc/onboarding_bloc.dart';
import 'features/report/data/repositories/report_repository.dart';
import 'package:hive/hive.dart';
import 'features/report/domain/models/weekly_report_adapter.dart'
    show WeeklyReportAdapter;
import 'features/report/domain/models/weekly_report.dart' show WeeklyReport;
import 'features/chat/data/datasources/chat_service.dart';

final getIt = GetIt.instance;

@InjectableInit()
void configureDependencies() {
  // 1. Hive Boxes 먼저 등록
  getIt.registerSingletonAsync<Box<WeeklyReport>>(() async {
    if (!Hive.isAdapterRegistered(3)) {
      Hive.registerAdapter(WeeklyReportAdapter());
    }
    return await Hive.openBox<WeeklyReport>('weekly_reports');
  });

  // 2. 기본 서비스들 등록
  final googleSignIn = GoogleSignIn(scopes: [
    'email',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
  ]);
  getIt.registerLazySingleton(() => googleSignIn);

  // 3. CalendarCacheManager 등록 및 초기화
  getIt.registerSingletonAsync<CalendarCacheManager>(() async {
    final manager = CalendarCacheManager();
    await manager.init();
    return manager;
  });

  // 4. CalendarCacheManager에 의존하는 서비스들 등록
  getIt.registerSingletonWithDependencies<GoogleCalendarDataSource>(
    () => GoogleCalendarDataSourceImpl(
      getIt<GoogleSignIn>(),
      getIt<CalendarCacheManager>(),
    ),
    dependsOn: [CalendarCacheManager],
  );

  getIt.registerSingletonWithDependencies<CalendarRepository>(
    () => CalendarRepositoryImpl(
      getIt<GoogleCalendarDataSource>(),
      getIt<CalendarCacheManager>(),
    ),
    dependsOn: [GoogleCalendarDataSource, CalendarCacheManager],
  );

  // 5. ReportRepository 등록
  getIt.registerSingletonWithDependencies<ReportRepository>(
    () => ReportRepository(
      reportsBox: getIt<Box<WeeklyReport>>(),
      calendarRepository: getIt<CalendarRepository>(),
    ),
    dependsOn: [Box<WeeklyReport>, CalendarRepository],
  );

  // GetEvents 등록 추가
  getIt.registerSingletonWithDependencies<GetEvents>(
    () => GetEvents(getIt<CalendarRepository>()),
    dependsOn: [CalendarRepository],
  );

  // 6. CalendarBloc 등록 (GetEvents 의존성 추가됨)
  getIt.registerSingletonWithDependencies<CalendarBloc>(
    () => CalendarBloc(
      getIt<GetEvents>(),
      getIt<CalendarRepository>(),
      getIt<ReportRepository>(),
    ),
    dependsOn: [GetEvents, CalendarRepository, ReportRepository],
  );

  // Auth 관련 의존성
  getIt.registerLazySingleton<AuthRepository>(() => AuthRepositoryImpl());
  getIt.registerLazySingleton(() => Login(getIt<AuthRepository>()));

  // FirebaseUserRepository 등록
  getIt.registerLazySingleton<FirebaseUserRepository>(
    () => FirebaseUserRepository(),
  );

  getIt.registerFactory(() => AuthBloc(
        getIt<Login>(),
        getIt<GoogleSignIn>(),
        getIt<CalendarBloc>(),
        getIt<FirebaseUserRepository>(),
      ));

  // Onboarding 관련 의존성
  getIt.registerLazySingleton<OnboardingRepository>(
    () => OnboardingRepositoryImpl(getIt()),
  );

  // Use Cases
  getIt.registerLazySingleton(() => SaveOnboardingData(getIt()));

  // Blocs
  getIt.registerFactory(
    () => OnboardingBloc(saveOnboardingData: getIt()),
  );

  // OpenAIService 대신 ChatService 등록
  getIt.registerLazySingleton<ChatService>(
    () => ChatService(),
  );
}
