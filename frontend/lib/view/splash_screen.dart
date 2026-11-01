import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../view_model/auth_view_model.dart';
import '../view_model/favorite_stocks.dart';
import 'login_screen.dart';
import 'main_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(milliseconds: 1200));
    if (!mounted) return;

    final authVM = context.read<AuthViewModel>();
    final isLoggedIn = await authVM.tryAutoLogin();

    if (!mounted) return;
    if (isLoggedIn) {
      await context.read<FavoriteStocksViewModel>().fetchFavoriteStocks();
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const MainTabScreen()),
      );
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color.fromARGB(255, 239, 238, 255),
      body: Center(
        child: Text(
          'Trender',
          style: TextStyle(
            color: Color(0xFF5C5CFF),
            fontSize: 48,
            fontWeight: FontWeight.w900,
            letterSpacing: -1.0,
          ),
        ),
      ),
    );
  }
}