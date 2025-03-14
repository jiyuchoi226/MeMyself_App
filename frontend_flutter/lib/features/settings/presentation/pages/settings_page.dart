import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/presentation/widgets/gnb.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/bloc/auth_state.dart';
import '../../../auth/presentation/bloc/auth_event.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:intl/intl.dart';
import '../../../onboarding/presentation/pages/onboarding_page.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  int _selectedNavIndex = 3;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAFAFA),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(
                  bottom: BorderSide(
                    color: Colors.grey[200]!,
                    width: 1,
                  ),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: GNB(
                selectedIndex: _selectedNavIndex,
                onItemSelected: (index) {
                  setState(() {
                    _selectedNavIndex = index;
                  });
                  switch (index) {
                    case 0:
                      Navigator.pushReplacementNamed(context, '/home');
                      break;
                    case 1:
                      Navigator.pushReplacementNamed(context, '/chat');
                      break;
                    case 2:
                      Navigator.pushReplacementNamed(context, '/report');
                      break;
                  }
                },
              ),
            ),
            Expanded(
              child: BlocBuilder<AuthBloc, AuthState>(
                builder: (context, state) {
                  if (state is AuthSuccess) {
                    return ListView(
                      shrinkWrap: true,
                      children: [
                        // 프로필 섹션
                        Container(
                          color: Colors.white,
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            children: [
                              CircleAvatar(
                                radius: 40,
                                backgroundImage:
                                    NetworkImage(state.user.photoURL ?? ''),
                              ),
                              const SizedBox(height: 16),
                              Text(
                                state.user.displayName ?? '도르미',
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                state.user.email ?? '',
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),

                        // 개인 정보 섹션
                        Container(
                          color: Colors.white,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Padding(
                                padding: const EdgeInsets.all(16),
                                child: Text(
                                  '개인 정보',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ),
                              ListTile(
                                leading: const Icon(Icons.cake_outlined),
                                title: const Text('생년월일'),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      state.metadata?.birthDate != null
                                          ? DateFormat('yyyy-MM-dd')
                                              .format(state.metadata!.birthDate)
                                          : '-',
                                      style: TextStyle(color: Colors.grey[600]),
                                    ),
                                    const Icon(Icons.chevron_right),
                                  ],
                                ),
                                onTap: () =>
                                    _navigateToOnboarding(context, 'birthDate'),
                              ),
                              ListTile(
                                leading: const Icon(Icons.psychology_outlined),
                                title: const Text('MBTI'),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      state.metadata?.mbti ?? '-',
                                      style: TextStyle(color: Colors.grey[600]),
                                    ),
                                    const Icon(Icons.chevron_right),
                                  ],
                                ),
                                onTap: () =>
                                    _navigateToOnboarding(context, 'mbti'),
                              ),
                              ListTile(
                                leading: const Icon(Icons.person_outline),
                                title: const Text('성별'),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      state.metadata?.gender ?? '-',
                                      style: TextStyle(color: Colors.grey[600]),
                                    ),
                                    const Icon(Icons.chevron_right),
                                  ],
                                ),
                                onTap: () =>
                                    _navigateToOnboarding(context, 'gender'),
                              ),
                              const Divider(height: 1),
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),

                        // 계정 관리 섹션
                        Container(
                          color: Colors.white,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Padding(
                                padding: const EdgeInsets.all(16),
                                child: Text(
                                  '계정 관리',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ),
                              ListTile(
                                leading: const Icon(Icons.switch_account),
                                title: const Text('다른 계정으로 로그인'),
                                trailing: const Icon(Icons.chevron_right),
                                onTap: () async {
                                  await GoogleSignIn().signOut();
                                  if (context.mounted) {
                                    context
                                        .read<AuthBloc>()
                                        .add(SignOutEvent());
                                    Navigator.pushReplacementNamed(
                                        context, '/');
                                  }
                                },
                              ),
                              const Divider(height: 1),
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),

                        // 개발자 모드 섹션
                        ListTile(
                          title: const Text('개발자 모드'),
                          subtitle: const Text('백엔드 통신 테스트'),
                          trailing: const Icon(Icons.developer_mode),
                          onTap: () {
                            Navigator.pushNamed(context, '/dev');
                          },
                        ),
                      ],
                    );
                  }
                  return const Center(child: CircularProgressIndicator());
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToOnboarding(BuildContext context, String field) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => OnboardingPage(
          editField: field,
          currentState: context.read<AuthBloc>().state,
        ),
      ),
    );

    if (result == true && context.mounted) {
      context.read<AuthBloc>().add(const RefreshUserData());
    }
  }
}
