import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'mypage.dart';
import 'tabs/favorite_tabs/favorite_stocks.dart';
import 'tabs/news_tab.dart';
import 'tabs/search_tab.dart';
import 'tabs/chatbot_tab.dart';

class MainTabScreen extends StatefulWidget {
  const MainTabScreen({super.key});

  @override
  State<MainTabScreen> createState() => _MainTabScreenState();
}

class _MainTabScreenState extends State<MainTabScreen> {
  int _selectedIndex = 0;

  static const _pages = [
    FavoriteStocksTab(),
    NewsTab(),
    SearchTab(),
    ChatbotTab(),
    MyPageScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        systemNavigationBarColor: isDark ? const Color(0xFF1B1D2C) : Colors.white,
        systemNavigationBarIconBrightness: isDark ? Brightness.light : Brightness.dark,
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: isDark ? Brightness.light : Brightness.dark,
      ),
      child: Scaffold(
        // 💡 하드코딩 제거: 테마에 맞는 배경색 적용
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        
        appBar: AppBar(
          backgroundColor: isDark ? const Color(0xFF1B1D2C) : Colors.white,
          elevation: 0,
          centerTitle: true,
          title: const Text(
            'Trender',
            style: TextStyle(
              color: Color(0xFF5C5CFF),
              fontWeight: FontWeight.bold,
              fontSize: 25,
            ),
          ),
        ),

        body: SafeArea(
          child: IndexedStack(
            index: _selectedIndex,
            children: _pages,
          ),
        ),

        bottomNavigationBar: Container(
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1B1D2C) : Colors.white,
            border: Border(
              top: BorderSide(
                color: isDark ? Colors.white10 : Colors.grey.shade300, 
                width: 0.5,
              ),
            ),
          ),
          child: Theme(
            data: Theme.of(context).copyWith(
              splashFactory: NoSplash.splashFactory,
              highlightColor: Colors.transparent,
            ),
            child: BottomNavigationBar(
              currentIndex: _selectedIndex,
              onTap: (index) => setState(() => _selectedIndex = index),
              type: BottomNavigationBarType.fixed,
              backgroundColor: isDark ? const Color(0xFF1B1D2C) : Colors.white,
              elevation: 0,
              enableFeedback: false,
              selectedItemColor: isDark ? Colors.white : Colors.black,
              unselectedItemColor: isDark ? Colors.white38 : const Color(0xFFC2C2C2),
              selectedFontSize: 12,
              unselectedFontSize: 12,
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.favorite_border),
                  activeIcon: Icon(Icons.favorite),
                  label: '관심 주식',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.filter_none),
                  activeIcon: Icon(Icons.library_books),
                  label: '뉴스',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.add_circle_outline),
                  activeIcon: Icon(Icons.add_circle),
                  label: '탐색',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.chat_bubble_outline),
                  activeIcon: Icon(Icons.chat),
                  label: '챗봇',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.person_outline),
                  activeIcon: Icon(Icons.person),
                  label: '설정',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}