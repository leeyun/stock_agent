import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../view_model/auth_view_model.dart';
import '../widgets/responsive_center.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _password2Controller = TextEditingController();

  bool _isPasswordObscured = true;
  bool _isPassword2Obscured = true;

  // 💡 실패 원인 상세 팝업 표시
  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.error_outline, color: Color(0xFFE54B4B)),
            SizedBox(width: 8),
            Text('회원가입 안내', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message, style: const TextStyle(fontSize: 14, height: 1.5, color: Colors.black87)),
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 6),
            const Text(
              '※ 비밀번호 규칙 안내\n• 최소 8자 이상\n• 숫자로만 구성 불가\n• 아이디와 유사한 비밀번호 불가',
              style: TextStyle(fontSize: 12, color: Colors.grey, height: 1.4),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF5C5CFF)),
            child: const Text('확인', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authViewModel = context.watch<AuthViewModel>();

    return Scaffold(
      backgroundColor: const Color(0xFFEFEEFF),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: ResponsiveCenter(
        maxWidth: 440,
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    'Trender',
                    style: TextStyle(color: Color(0xFF5C5CFF), fontSize: 40, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 10),
                  const Text('Create an account', style: TextStyle(fontSize: 16, color: Colors.grey)),
                  const SizedBox(height: 30),
                  
                  Container(
                    padding: const EdgeInsets.all(24.0),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 5)),
                      ],
                    ),
                    child: Column(
                      children: [
                        // 아이디
                        TextField(
                          controller: _usernameController,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '이름(Username)을 입력해주세요',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                          ),
                        ),
                        const SizedBox(height: 16),
  
                        // 이메일
                        TextField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '이메일을 입력해주세요',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                          ),
                        ),
                        const SizedBox(height: 16),
                        
                        // 비밀번호
                        TextField(
                          controller: _passwordController,
                          obscureText: _isPasswordObscured,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '비밀번호 (8자 이상)',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                            suffixIcon: IconButton(
                              icon: Icon(_isPasswordObscured ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                              onPressed: () {
                                setState(() { _isPasswordObscured = !_isPasswordObscured; });
                              },
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
  
                        // 비밀번호 확인
                        TextField(
                          controller: _password2Controller,
                          obscureText: _isPassword2Obscured,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '비밀번호를 다시 입력해주세요',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                            suffixIcon: IconButton(
                              icon: Icon(_isPassword2Obscured ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                              onPressed: () {
                                setState(() { _isPassword2Obscured = !_isPassword2Obscured; });
                              },
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        
                        ElevatedButton(
                          onPressed: authViewModel.isLoading
                              ? null
                              : () async {
                                  final username = _usernameController.text.trim();
                                  final email = _emailController.text.trim();
                                  final pw = _passwordController.text.trim();
                                  final pw2 = _password2Controller.text.trim();
  
                                  if (username.isEmpty || email.isEmpty || pw.isEmpty) {
                                    _showErrorDialog('모든 필드를 입력해주세요.');
                                    return;
                                  }
  
                                  if (pw != pw2) {
                                    _showErrorDialog('비밀번호와 비밀번호 확인이 일치하지 않습니다.');
                                    return;
                                  }
  
                                  final result = await context.read<AuthViewModel>().signUp(
                                    username,
                                    email,
                                    pw,
                                    pw2,
                                  );
                                  
                                  if (result.success && context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text('회원가입이 완료되었습니다!')),
                                    );
                                    Navigator.pop(context);
                                  } else if (context.mounted) {
                                    _showErrorDialog(result.errorMessage ?? '회원가입에 실패했습니다.');
                                  }
                                },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF5C5CFF),
                            minimumSize: const Size(double.infinity, 50),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          child: authViewModel.isLoading
                              ? const CircularProgressIndicator(color: Colors.white)
                              : const Text('Sign Up', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}