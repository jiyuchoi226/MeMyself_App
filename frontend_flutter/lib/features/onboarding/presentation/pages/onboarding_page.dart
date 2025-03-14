import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../onboarding/domain/models/onboarding_data.dart';
import 'birth_date_page.dart';
import 'gender_page.dart';
import 'mbti_page.dart';
import '../../../calendar/presentation/bloc/calendar_bloc.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/bloc/auth_state.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../../auth/data/repositories/firebase_user_repository.dart';
import '../../../auth/domain/entities/user_metadata.dart' as app_metadata;
import '../../../../injection.dart';
import '../../../../core/presentation/widgets/lumy_profile_header.dart';
import '../../../auth/presentation/bloc/auth_event.dart';
import '../../../calendar/domain/entities/load_priority.dart';

class OnboardingPage extends StatefulWidget {
  final String? editField;
  final AuthState? currentState;

  const OnboardingPage({
    super.key,
    this.editField,
    this.currentState,
  });

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  late OnboardingData _onboardingData;
  final FirebaseUserRepository _userRepository =
      getIt<FirebaseUserRepository>();
  late PageController _pageController;

  @override
  void initState() {
    super.initState();
    _initializeData();
    // PageController는 전체 온보딩 모드에서만 필요
    if (widget.editField == null) {
      _pageController = PageController();
    }
  }

  void _initializeData() {
    if (widget.currentState is AuthSuccess) {
      final metadata = (widget.currentState as AuthSuccess).metadata;
      _onboardingData = OnboardingData(
        birthDate: metadata?.birthDate,
        mbti: metadata?.mbti,
        gender: metadata?.gender,
      );
    } else {
      _onboardingData = OnboardingData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(24.0),
              child: const LumyProfileHeader(),
            ),
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: Column(
                  children: [
                    if (widget.editField != null)
                      Expanded(child: _buildEditField())
                    else
                      Expanded(
                        child: PageView(
                          controller: _pageController,
                          physics: const NeverScrollableScrollPhysics(),
                          children: _buildOnboardingPages(),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getEditTitle(String field) {
    switch (field) {
      case 'birthDate':
        return '생년월일 수정';
      case 'gender':
        return '성별 수정';
      case 'mbti':
        return 'MBTI 수정';
      default:
        return '정보 수정';
    }
  }

  List<Widget> _buildOnboardingPages() {
    return [
      BirthDatePage(
        onNext: (date) {
          setState(() {
            _onboardingData = _onboardingData.copyWith(birthDate: date);
          });
          _pageController.nextPage(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
        },
      ),
      GenderPage(
        onNext: (gender) {
          setState(() {
            _onboardingData = _onboardingData.copyWith(gender: gender);
          });
          _pageController.nextPage(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
        },
      ),
      MbtiPage(
        onNext: (mbti) {
          setState(() {
            _onboardingData = _onboardingData.copyWith(mbti: mbti);
          });
          _saveFullOnboardingData();
        },
      ),
    ];
  }

  Widget _buildEditField() {
    switch (widget.editField) {
      case 'birthDate':
        return BirthDatePage(
          isEditMode: true,
          onNext: (date) {
            _onboardingData = _onboardingData.copyWith(birthDate: date);
            _saveSingleField();
          },
        );
      case 'gender':
        return GenderPage(
          isEditMode: true,
          onNext: (gender) {
            _onboardingData = _onboardingData.copyWith(gender: gender);
            _saveSingleField();
          },
        );
      case 'mbti':
        return MbtiPage(
          isEditMode: true,
          onNext: (mbti) {
            _onboardingData = _onboardingData.copyWith(mbti: mbti);
            _saveSingleField();
          },
        );
      default:
        return const Center(child: Text('잘못된 접근입니다.'));
    }
  }

  // 단일 필드 저장 및 설정 페이지로 돌아가기
  Future<void> _saveSingleField() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        final currentMetadata = await _userRepository.getUserMetadata(user.uid);

        // 현재 수정 중인 필드만 업데이트
        final updatedMetadata = app_metadata.UserMetadata(
          uid: user.uid,
          birthDate: widget.editField == 'birthDate'
              ? _onboardingData.birthDate ?? DateTime.now()
              : currentMetadata?.birthDate ?? DateTime.now(),
          mbti: widget.editField == 'mbti'
              ? _onboardingData.mbti ?? ''
              : currentMetadata?.mbti ?? '',
          gender: widget.editField == 'gender'
              ? _onboardingData.gender ?? ''
              : currentMetadata?.gender ?? '',
          createdAt: currentMetadata?.createdAt ?? DateTime.now(),
          updatedAt: DateTime.now(),
        );

        await _userRepository.saveUserMetadata(updatedMetadata);
        if (context.mounted) {
          Navigator.pop(context, true);
        }
      }
    } catch (e) {
      print('Error saving field: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('데이터 저장 중 오류가 발생했습니다.')),
        );
      }
    }
  }

  // 전체 온보딩 데이터 저장
  Future<void> _saveFullOnboardingData() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        // 메타데이터 생성
        final metadata = app_metadata.UserMetadata(
          uid: user.uid,
          birthDate: _onboardingData.birthDate!,
          mbti: _onboardingData.mbti!,
          gender: _onboardingData.gender!,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        // 메타데이터 저장
        await _userRepository.saveUserMetadata(metadata);

        if (context.mounted) {
          // AuthBloc 상태 즉시 업데이트
          context.read<AuthBloc>().add(const RefreshUserData());

          // CalendarBloc 데이터 즉시 로드
          final calendarBloc = context.read<CalendarBloc>();
          final now = DateTime.now();

          // 현재 달과 이전 3개월 데이터 즉시 로드
          calendarBloc.add(LoadMonthEvents(now, priority: LoadPriority.high));
          for (int i = 1; i <= 3; i++) {
            final previousMonth = DateTime(now.year, now.month - i, 1);
            calendarBloc.add(
                LoadMonthEvents(previousMonth, priority: LoadPriority.high));
          }

          // 홈 화면으로 이동
          Navigator.of(context).pushReplacementNamed('/home');
        }
      }
    } catch (e) {
      print('Error saving full onboarding data: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('데이터 저장 중 오류가 발생했습니다.')),
        );
      }
    }
  }

  @override
  void dispose() {
    if (widget.editField == null) {
      _pageController.dispose();
    }
    super.dispose();
  }
}
