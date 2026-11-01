import 'package:flutter/material.dart';
import 'package:trender/widgets/tag_widget.dart';
import '../../../model/stock_model.dart';
import 'news_detail_screen.dart';
import '../../../widgets/responsive_center.dart';

class StockDetailScreen extends StatelessWidget {
  final StockModel stock;

  const StockDetailScreen({super.key, required this.stock});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final logoText = stock.companyName.length >= 2
        ? stock.companyName.substring(0, 2)
        : stock.companyName;

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
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Container(
            width: double.infinity,
            height: double.infinity,
            padding: const EdgeInsets.all(20.0),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(24),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 헤더: 뒤로가기 + 종목명 + 시세 / 로고 박스
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        GestureDetector(
                          onTap: () => Navigator.pop(context),
                          child: Padding(
                            padding: const EdgeInsets.only(right: 8.0, top: 2.0),
                            child: Icon(
                              Icons.arrow_back_ios_new,
                              size: 22,
                              color: isDark ? Colors.white : Colors.black,
                            ),
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              stock.companyName,
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: isDark ? Colors.white : Colors.black,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${stock.price}  ${stock.changeRate}(${stock.changePrice})',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: stock.isPositive ? const Color(0xFFE54B4B) : const Color(0xFF3A7BD5),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: isDark ? Colors.white24 : Colors.grey.shade300),
                      ),
                      child: Center(
                        child: Text(
                          logoText,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: isDark ? Colors.white70 : Colors.grey,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
  
                // 전체 뉴스 목록
                Expanded(
                  child: stock.newsList.isEmpty
                      ? Center(
                          child: Text(
                            '관련 뉴스가 없습니다.',
                            style: TextStyle(color: isDark ? Colors.white54 : Colors.grey),
                          ),
                        )
                      : ListView.builder(
                          physics: const BouncingScrollPhysics(),
                          itemCount: stock.newsList.length,
                          itemBuilder: (context, index) {
                            final news = stock.newsList[index];
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                InkWell(
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(builder: (_) => NewsDetailScreen(news: news)),
                                    );
                                  },
                                  borderRadius: BorderRadius.circular(8),
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 4.0),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            TagWidget(tag: news.tag),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(
                                                news.title,
                                                style: TextStyle(
                                                  fontSize: 15,
                                                  fontWeight: FontWeight.bold,
                                                  color: isDark ? Colors.white : Colors.black,
                                                ),
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Text(news.time, style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
                                        const SizedBox(height: 6),
                                        Text(
                                          news.summary,
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: isDark ? Colors.white70 : Colors.black87,
                                            height: 1.3,
                                          ),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                if (index < stock.newsList.length - 1)
                                  Divider(height: 20, color: isDark ? Colors.white12 : Colors.grey.shade200),
                              ],
                            );
                          },
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