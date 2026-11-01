import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'view/splash_screen.dart';
import 'view_model/auth_view_model.dart';
import 'view_model/favorite_stocks.dart';
import 'view_model/main_view_model.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthViewModel()),
        ChangeNotifierProvider(create: (_) => MainViewModel()),
        ChangeNotifierProvider(create: (_) => FavoriteStocksViewModel()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final mainVM = context.watch<MainViewModel>();

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      themeMode: mainVM.themeMode,
      // 💡 라이트 모드 (전체 배경 #EFEEFF, 카드 흰색)
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFEFEEFF),
        canvasColor: const Color(0xFFEFEEFF),
        cardColor: Colors.white,
        primaryColor: const Color(0xFF5C5CFF),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          elevation: 0,
          iconTheme: IconThemeData(color: Colors.black),
          titleTextStyle: TextStyle(
            color: Color(0xFF5C5CFF),
            fontWeight: FontWeight.bold,
            fontSize: 24,
          ),
        ),
      ),
      // 💡 다크 모드 (전체 배경 #12131C, 카드 #1F202F)
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF12131C),
        canvasColor: const Color(0xFF12131C),
        cardColor: const Color(0xFF1F202F),
        primaryColor: const Color(0xFF6E6EFF),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1B1D2C),
          elevation: 0,
          iconTheme: IconThemeData(color: Colors.white),
          titleTextStyle: TextStyle(
            color: Color(0xFF6E6EFF),
            fontWeight: FontWeight.bold,
            fontSize: 24,
          ),
        ),
      ),
      home: const SplashScreen(),
    );
  }
}