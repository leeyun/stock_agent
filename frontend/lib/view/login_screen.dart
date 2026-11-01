import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../view_model/auth_view_model.dart';
import 'main_screen.dart'; 
import 'signup_screen.dart';
import '../widgets/google_login_button.dart';
import '../widgets/responsive_center.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isObscured = true;

  @override
  Widget build(BuildContext context) {
    final authViewModel = context.watch<AuthViewModel>();

    return Scaffold(
      backgroundColor: const Color(0xFFEFEEFF),
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
                  const SizedBox(height: 40),
                  
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
                        GoogleLoginButton(
                          onSuccess: () => Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(builder: (context) => const MainTabScreen()),
                          ),
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 20.0),
                          child: Text('Or', style: TextStyle(color: Colors.grey)),
                        ),
                        
                        // 💡 입력 글자색 검정색(Colors.black) 지정
                        TextField(
                          controller: _emailController,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '이메일을 입력해주세요',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14, fontWeight: FontWeight.w400),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                          ),
                        ),
                        const SizedBox(height: 16),
                        
                        // 💡 비밀번호 입력 글자색 검정색(Colors.black) 지정
                        TextField(
                          controller: _passwordController,
                          obscureText: _isObscured,
                          style: const TextStyle(color: Colors.black, fontSize: 14, fontWeight: FontWeight.w500),
                          decoration: InputDecoration(
                            hintText: '비밀번호를 입력해주세요',
                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14, fontWeight: FontWeight.w400),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                            suffixIcon: IconButton(
                              icon: Icon(_isObscured ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                              onPressed: () {
                                setState(() {
                                  _isObscured = !_isObscured;
                                });
                              },
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Checkbox(value: false, onChanged: (value) {}),
                                const Text('Remember me', style: TextStyle(fontSize: 12, color: Colors.grey)),
                              ],
                            ),
                            const Text('Forgot Password?', style: TextStyle(fontSize: 12, color: Colors.blue)),
                          ],
                        ),
                        const SizedBox(height: 16),
                        
                        ElevatedButton(
                          onPressed: authViewModel.isLoading
                              ? null
                              : () async {
                                  bool isSuccess = await context.read<AuthViewModel>().login(
                                    _emailController.text.trim(),
                                    _passwordController.text.trim(),
                                  );
                                  
                                  if (isSuccess && context.mounted) {
                                    Navigator.pushReplacement(
                                      context,
                                      MaterialPageRoute(builder: (context) => const MainTabScreen()),
                                    );
                                  } else if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text('이메일 또는 비밀번호를 확인해주세요.')),
                                    );
                                  }
                                },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF5C5CFF),
                            minimumSize: const Size(double.infinity, 50),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          child: authViewModel.isLoading
                              ? const CircularProgressIndicator(color: Colors.white)
                              : const Text('Log In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                        ),
                        const SizedBox(height: 16),
                        
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text("Don't have an account? ", style: TextStyle(fontSize: 12, color: Colors.grey)),
                            GestureDetector(
                              onTap: () {
                                Navigator.push(context, MaterialPageRoute(builder: (context) => const SignupScreen()));
                              },
                              child: const Text("Sign Up", style: TextStyle(fontSize: 12, color: Colors.blue, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 40),
                  const Text('made by runners', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}