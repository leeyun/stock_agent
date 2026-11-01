import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../model/stock_model.dart';
import '../../../widgets/tag_widget.dart';
import '../../../widgets/responsive_center.dart';

class NewsDetailScreen extends StatelessWidget {
  final NewsModel news;

  const NewsDetailScreen({super.key, required this.news});

  Future<void> _launchURL(String urlString) async {
    final Uri url = Uri.parse(urlString);
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      debugPrint('링크를 열 수 없습니다: $urlString');
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isPositive = news.tag == '호재';
    final isNegative = news.tag == '악재';

    // 다크/라이트 모드별 호재·악재 박스 배경색
    Color reasonBgColor;
    if (isPositive) {
      reasonBgColor = isDark ? const Color(0xFF3B1D22) : const Color(0xFFFFF0F0);
    } else if (isNegative) {
      reasonBgColor = isDark ? const Color(0xFF192A44) : const Color(0xFFF0F4FF);
    } else {
      reasonBgColor = isDark ? const Color(0xFF26283B) : const Color(0xFFF2F3F5);
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: isDark ? const Color(0xFF1B1D2C) : Colors.white,
        elevation: 0,
        centerTitle: true,
        automaticallyImplyLeading: false,
        title: const Text(
          'Trender',
          style: TextStyle(
            color: Color(0xFF5C5CFF),
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      body: ResponsiveCenter(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20.0),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(24),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 뒤로가기 + 언론사 이름
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.arrow_back_ios_new, size: 18, color: isDark ? Colors.white : Colors.black),
                      const SizedBox(width: 8),
                      Text(
                        news.media,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: isDark ? Colors.white : Colors.black,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
  
                // 2. 뉴스 제목
                Text(
                  news.title,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : Colors.black,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 8),
  
                // 3. 날짜 및 시간
                Text(
                  '${news.date}, ${news.time}',
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
                ),
                const SizedBox(height: 20),
  
                // 4. ✨ 뉴스 3줄 요약 박스
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16.0),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1B1D2C) : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: isDark ? Colors.white24 : Colors.grey.shade300),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text('✨', style: TextStyle(fontSize: 16)),
                          const SizedBox(width: 4),
                          Text(
                            '뉴스 요약',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: isDark ? Colors.white : Colors.black,
                            ),
                          ),
                        ],
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8.0),
                        child: Divider(height: 1, color: isDark ? Colors.white24 : Colors.black87),
                      ),
                      ...news.bulletSummaries.map((summaryText) => Padding(
                            padding: const EdgeInsets.only(bottom: 6.0),
                            child: Text(
                              '• $summaryText',
                              style: TextStyle(
                                fontSize: 14,
                                color: isDark ? Colors.white70 : Colors.black87,
                                height: 1.4,
                              ),
                            ),
                          )),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
  
                // 5. 호재/악재 AI 사유 안내 박스
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16.0),
                  decoration: BoxDecoration(
                    color: reasonBgColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      TagWidget(tag: news.tag),
                      const SizedBox(height: 10),
                      Text(
                        news.aiReason,
                        style: TextStyle(
                          fontSize: 14,
                          color: isDark ? Colors.white : Colors.black87,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
  
                // 6. 원본 뉴스 링크
                Align(
                  alignment: Alignment.centerRight,
                  child: InkWell(
                    onTap: () => _launchURL(news.originalUrl),
                    child: const Text(
                      '원본 뉴스 보기',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.blue,
                        decoration: TextDecoration.underline,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}