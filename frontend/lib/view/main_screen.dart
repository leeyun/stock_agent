import 'package:flutter/material.dart';
import 'mypage.dart';
import 'tabs/favorite_tabs/favorite_stocks.dart';
import 'tabs/news_tab.dart';
import 'tabs/search_tab.dart';
import 'tabs/chatbot_tab.dart';
import '../widgets/responsive_center.dart';

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

  // 이 폭 이상이면 하단 탭바 대신 좌측 NavigationRail 사용 (데스크톱 브라우저)
  static const double _wideBreakpoint = 840;

  static const _destinations = [
    (icon: Icons.favorite_border, activeIcon: Icons.favorite, label: '관심 주식'),
    (icon: Icons.filter_none, activeIcon: Icons.library_books, label: '뉴스'),
    (icon: Icons.add_circle_outline, activeIcon: Icons.add_circle, label: '탐색'),
    (icon: Icons.chat_bubble_outline, activeIcon: Icons.chat, label: '챗봇'),
    (icon: Icons.person_outline, activeIcon: Icons.person, label: '설정'),
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final barColor = isDark ? const Color(0xFF1B1D2C) : Colors.white;
    final dividerColor = isDark ? Colors.white10 : Colors.grey.shade300;
    final selectedColor = isDark ? Colors.white : Colors.black;
    final unselectedColor = isDark ? Colors.white38 : const Color(0xFFC2C2C2);
    final isWide = MediaQuery.sizeOf(context).width >= _wideBreakpoint;

    final pages = SafeArea(
      child: ResponsiveCenter(
        child: IndexedStack(
          index: _selectedIndex,
          children: _pages,
        ),
      ),
    );

    return Scaffold(
      // 💡 하드코딩 제거: 테마에 맞는 배경색 적용
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,

      appBar: AppBar(
        backgroundColor: barColor,
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

      body: isWide
          ? Row(
              children: [
                NavigationRail(
                  selectedIndex: _selectedIndex,
                  onDestinationSelected: (index) => setState(() => _selectedIndex = index),
                  backgroundColor: barColor,
                  labelType: NavigationRailLabelType.all,
                  indicatorColor: Colors.transparent,
                  selectedIconTheme: IconThemeData(color: selectedColor),
                  unselectedIconTheme: IconThemeData(color: unselectedColor),
                  selectedLabelTextStyle: TextStyle(color: selectedColor, fontSize: 12),
                  unselectedLabelTextStyle: TextStyle(color: unselectedColor, fontSize: 12),
                  destinations: [
                    for (final d in _destinations)
                      NavigationRailDestination(
                        icon: Icon(d.icon),
                        selectedIcon: Icon(d.activeIcon),
                        label: Text(d.label),
                      ),
                  ],
                ),
                VerticalDivider(width: 0.5, thickness: 0.5, color: dividerColor),
                Expanded(child: pages),
              ],
            )
          : pages,

      bottomNavigationBar: isWide
          ? null
          : Container(
              decoration: BoxDecoration(
                color: barColor,
                border: Border(
                  top: BorderSide(color: dividerColor, width: 0.5),
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
                  backgroundColor: barColor,
                  elevation: 0,
                  enableFeedback: false,
                  selectedItemColor: selectedColor,
                  unselectedItemColor: unselectedColor,
                  selectedFontSize: 12,
                  unselectedFontSize: 12,
                  items: [
                    for (final d in _destinations)
                      BottomNavigationBarItem(
                        icon: Icon(d.icon),
                        activeIcon: Icon(d.activeIcon),
                        label: d.label,
                      ),
                  ],
                ),
              ),
            ),
    );
  }
}
