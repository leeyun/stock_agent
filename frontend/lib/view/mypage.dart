import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../view_model/auth_view_model.dart';
import '../view_model/main_view_model.dart';
import 'login_screen.dart';
import 'tabs/favorite_tabs/group_edit_screen.dart';

class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  void _showThemeDialog(BuildContext context) {
    final mainVM = context.read<MainViewModel>();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('디스플레이 설정', style: TextStyle(fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<ThemeMode>(
              title: const Text('시스템 설정'),
              value: ThemeMode.system,
              groupValue: mainVM.themeMode,
              onChanged: (mode) {
                if (mode != null) mainVM.setThemeMode(mode);
                Navigator.pop(ctx);
              },
            ),
            RadioListTile<ThemeMode>(
              title: const Text('라이트 모드'),
              value: ThemeMode.light,
              groupValue: mainVM.themeMode,
              onChanged: (mode) {
                if (mode != null) mainVM.setThemeMode(mode);
                Navigator.pop(ctx);
              },
            ),
            RadioListTile<ThemeMode>(
              title: const Text('다크 모드'),
              value: ThemeMode.dark,
              groupValue: mainVM.themeMode,
              onChanged: (mode) {
                if (mode != null) mainVM.setThemeMode(mode);
                Navigator.pop(ctx);
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authViewModel = context.watch<AuthViewModel>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 20.0),
            child: Column(
              children: [
                const Align(
                  alignment: Alignment.topLeft,
                  child: Text('Trender', style: TextStyle(color: Color(0xFF5C5CFF), fontWeight: FontWeight.bold, fontSize: 16)),
                ),
                const SizedBox(height: 12),

                CircleAvatar(
                  radius: 40,
                  backgroundColor: isDark ? const Color(0xFF2B2D42) : Colors.grey.shade100,
                  child: const Icon(Icons.person_outline, size: 48, color: Colors.grey),
                ),
                const SizedBox(height: 12),

                Text(
                  authViewModel.nickname.isEmpty ? '사용자 이름' : authViewModel.nickname,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  authViewModel.email.isEmpty ? 'ghdwndks123@naver.com' : authViewModel.email,
                  style: const TextStyle(color: Colors.grey, fontSize: 13),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
            child: Column(
              children: [
                _buildMenuItem(context, '관심종목 관리', () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const GroupEditScreen()));
                }),
                Divider(height: 1, color: isDark ? Colors.white10 : Colors.grey.shade200),
                _buildMenuItem(context, '프로필 수정', () {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('프로필 수정 준비 중')));
                }),
                Divider(height: 1, color: isDark ? Colors.white10 : Colors.grey.shade200),
                _buildMenuItem(context, '디스플레이 설정', () => _showThemeDialog(context)),
                Divider(height: 1, color: isDark ? Colors.white10 : Colors.grey.shade200),
                _buildMenuItem(context, '로그아웃', () async {
                  await context.read<AuthViewModel>().logout();
                  if (context.mounted) {
                    Navigator.pushAndRemoveUntil(
                      context,
                      MaterialPageRoute(builder: (_) => const LoginScreen()),
                      (route) => false,
                    );
                  }
                }, textColor: Colors.red),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, String title, VoidCallback onTap, {Color? textColor}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 18.0, horizontal: 8.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: textColor)),
            const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}